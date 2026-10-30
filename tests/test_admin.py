import json
from pathlib import Path
import smtplib
import sqlite3
import time
import unittest
import uuid
from unittest.mock import patch
from app import create_app
from domain import DomainError
from backup_tools import daily_backup,verify_backup
import test_app as fixtures

class AdminTests(unittest.TestCase):
    setUpBase=fixtures.CloudTests.setUp
    tearDown=fixtures.CloudTests.tearDown
    post=fixtures.CloudTests.post
    register=fixtures.CloudTests.register
    command=fixtures.CloudTests.command
    state=fixtures.CloudTests.state
    issue=fixtures.CloudTests.issue
    clear_mail_counters=fixtures.CloudTests.clear_mail_counters

    def setUp(self):
        self.setUpBase()
        with sqlite3.connect(self.path) as db:db.execute("UPDATE users SET admin=1 WHERE email='one@example.com'")
        self.uid=self.a.get('/api/auth/me').json['user']['id']
        self.other_uid=self.b.get('/api/auth/me').json['user']['id']

    def get(self,path):return self.a.get('/api/admin/'+path)

    def test_all_admin_endpoints_require_server_role(self):
        guest=self.app.test_client()
        for route in ('summary','users','users/'+self.uid,'applications','records','records/unknown','ledger','mail','system','audit','overview'):
            self.assertEqual(guest.get('/api/admin/'+route).status_code,401,route)
            self.assertEqual(self.b.get('/api/admin/'+route).status_code,403,route)
        self.assertEqual(guest.get('/admin/').status_code,303)
        self.assertEqual(self.b.get('/admin/').status_code,403)
        response=self.a.get('/admin/');self.assertEqual(response.status_code,200);self.assertIn('no-store',response.headers['Cache-Control']);response.close()
        with sqlite3.connect(self.path) as db:db.execute('UPDATE users SET admin=0 WHERE id=?',(self.uid,))
        self.assertEqual(self.get('summary').status_code,403)

    def test_summary_current_totals_are_currency_separated(self):
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=100))
        self.command(self.b,'treasury/wire-in',dict(currency='CNY',amount=700))
        card=self.issue(self.b,'gold')
        self.command(self.b,'cards/security-freeze',dict(uid=card['uid']))
        data=self.get('summary').json
        self.assertEqual(data['users'],2);self.assertEqual(data['admins'],1)
        self.assertEqual(data['wallets']['USD'],100);self.assertEqual(data['wallets']['CNY'],700)
        self.assertEqual(data['cards'],1);self.assertEqual(data['frozenCards'],1);self.assertEqual(data['debtUSD'],295)
        self.assertEqual(data['records']['current'],4);self.assertEqual(len(data['trend']),14)

    def test_user_search_literal_wildcards_and_pagination(self):
        data=self.get('users?q=two%40example.com&pageSize=1').json
        self.assertEqual(data['total'],1);self.assertEqual(data['items'][0]['id'],self.other_uid)
        data=self.get('users?pageSize=1&page=2').json;self.assertEqual(data['pages'],2);self.assertEqual(data['page'],2)
        self.assertEqual(self.get('users?role=admin').json['total'],1)
        self.assertEqual(self.get('users?q=%25').json['total'],0)
        self.assertEqual(self.get('users?q=_').json['total'],0)
        self.assertEqual(self.get("users?q='OR%201=1--").json['total'],0)
        self.assertEqual(self.get('users?q='+self.uid).json['total'],1)

    def test_detail_and_history_never_expose_credentials(self):
        card=self.issue(self.b,'gold')
        self.command(self.b,'pos/authorize',dict(uid=card['uid'],currency='USD',amount=10,category='travel',merchant='Test'))
        self.assertEqual(self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=float('nan'))).status_code,400)
        records=self.get('records?userId='+self.other_uid).json['items']
        responses=[self.get('users/'+self.other_uid),self.get('summary'),self.get('system'),self.get('mail'),self.get('ledger')]
        responses.extend(self.get('records/'+r['id']) for r in records)
        forbidden={'password','currentPassword','cvv','cardNumber','token','digest','csrf','command_key','SMTP_PASSWORD','APP_SECRET'}
        def check(value):
            if isinstance(value,dict):
                self.assertFalse(forbidden.intersection(value))
                for item in value.values():check(item)
            if isinstance(value,list):
                for item in value:check(item)
        for response in responses:
            self.assertEqual(response.status_code,200,response.json);check(response.json)
            self.assertNotIn(card['cardNumber'],response.get_data(as_text=True))
            self.assertNotIn(card['cvv'],response.get_data(as_text=True))
        self.assertEqual(self.get('users/'+self.other_uid).json['cards'][0]['last4'],card['cardNumber'][-4:])

    def test_records_are_atomic_idempotent_linked_and_survive_reset(self):
        key=uuid.uuid4().hex
        for _ in range(3):self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=100),key)
        result=self.get('records?userId='+self.other_uid).json
        self.assertEqual(result['total'],1)
        detail=self.get('records/'+result['items'][0]['id']).json
        self.assertEqual(detail['details']['walletDelta']['USD'],100)
        ledger=self.get('ledger?userId='+self.other_uid).json['items'];self.assertEqual(len(ledger),1)
        self.assertEqual(ledger[0]['record_id'],detail['id'])
        self.assertEqual(ledger[0]['entry_id'],detail['details']['ledgerIds'][0])
        self.command(self.b,'core/reset',{'currentPassword':'strong-password!'})
        self.assertEqual(self.get('records?userId='+self.other_uid).json['total'],2)
        self.assertEqual(self.get('ledger?userId='+self.other_uid).json['total'],1)
        self.assertEqual(self.get('summary').json['wallets']['USD'],0)
        self.assertEqual(self.state(self.b)['generalLedger'],[])

    def test_approval_and_rejection_capture_model_inputs_and_rule_snapshot(self):
        self.command(self.b,'underwriting/issue-card',dict(cardId='gold',income=0,months=0,existing=0,holderName='Demo'))
        self.issue(self.b,'gold')
        result=self.get('applications?userId='+self.other_uid).json
        self.assertEqual(result['total'],2)
        rejected=self.get('applications?status=failed').json['items'][0]
        details=self.get('records/'+rejected['id']).json['details']
        self.assertEqual(details['inputs']['income'],0);self.assertFalse(details['assessment']['approved'])
        self.assertIn('ruleVersion',details);self.assertEqual(details['rules']['min_income'],5000)
        self.assertEqual(self.get('applications?status=success').json['total'],1)

    def test_filters_reject_bad_dates_status_and_excessive_page_size(self):
        for route in ('users?pageSize=101','users?page=0','users?page=-1','users?page=1.2','records?status=foo','mail?result=no','users?role=root','records?route=invalid','records?from=2026-02-31','users?from=2026-10-19&to=2026-10-18','users?to=9999-12-31'):
            self.assertEqual(self.get(route).status_code,400,route)
        self.assertEqual(self.get('users/missing').status_code,404)
        self.assertEqual(self.get('records/missing').status_code,404)
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=1))
        rid=self.get('records').json['items'][0]['id']
        # 16:30 UTC is 00:30 the next day in Beijing.
        import datetime
        epoch=int(datetime.datetime(2026,10,17,16,30,tzinfo=datetime.timezone.utc).timestamp())
        with sqlite3.connect(self.path) as db:db.execute('UPDATE business_records SET created=? WHERE id=?',(epoch,rid))
        self.assertEqual(self.get('records?from=2026-10-18&to=2026-10-18').json['total'],1)
        self.assertEqual(self.get('records?from=2026-10-17&to=2026-10-17').json['total'],0)

    def test_read_only_admin_requests_preserve_account_and_reject_writes(self):
        before=self.state(self.b)
        for route in ('summary','users','users/'+self.other_uid,'applications','records','ledger','mail','system','audit'):
            self.assertEqual(self.get(route).status_code,200,route)
        for method in ('post','put','delete'):
            response=getattr(self.a,method)('/api/admin/users/'+self.other_uid,json={'admin':True,'balance':999999},headers={'X-JWB-Client':'web','X-CSRF-Token':self.csrf[id(self.a)]})
            self.assertEqual(response.status_code,405)
        self.assertEqual(self.state(self.b),before)
        self.assertFalse(self.b.get('/api/auth/me').json['user']['admin'])
        events=self.get('audit').json['items']
        self.assertTrue(any(e['action']=='user_detail' and e['target']==self.other_uid for e in events))
        self.assertTrue(all(e['actor_id']==self.uid for e in events))

    def test_mail_logging_sanitizes_errors_and_records_transport_acceptance(self):
        self.assertEqual(self.get('mail?result=accepted').json['total'],2)
        self.clear_mail_counters();self.app.config.update(MAIL_MODE='smtp',SMTP_HOST='test.invalid',MAIL_FROM='test@example.com',SMTP_TLS='ssl',SMTP_PORT=465,SMTP_PASSWORD='private-password')
        with patch('app.smtplib.SMTP_SSL',side_effect=smtplib.SMTPAuthenticationError(535,b'private-server-response')):
            self.assertEqual(self.post(self.b,'auth/request-code',dict(email='two@example.com',purpose='login')).status_code,503)
        response=self.get('mail?result=failed');self.assertEqual(response.json['total'],1)
        self.assertEqual(response.json['items'][0]['error_category'],'authentication')
        self.assertNotIn('private-password',response.get_data(as_text=True));self.assertNotIn('private-server-response',response.get_data(as_text=True))
        self.assertEqual(self.get('system').json['mail']['failed24h'],1)

    def test_backup_status_uses_saved_report_without_triggering_backup(self):
        directory=Path(self.tmp.name)/'backups';self.app.config['BACKUP_DIR']=str(directory)
        self.assertEqual(self.get('system').json['backup']['state'],'missing')
        snapshot,_=daily_backup(self.path,directory)
        data=self.get('system').json['backup'];self.assertEqual(data['state'],'recent');self.assertEqual(data['name'],snapshot.name)
        self.assertEqual(len(list(directory.glob('*.sqlite3'))),1)
        self.assertEqual(verify_backup(snapshot)['restoreDrill'],'passed')

    def test_system_uses_existing_cache_without_external_probes(self):
        def forbidden():raise AssertionError('The admin status must not call the FX provider')
        self.app.config['FX_TEST_PROVIDER']=forbidden
        from datetime import datetime,timezone
        value={'source':'test cache','asOf':datetime.now(timezone.utc).isoformat(),'fetchedAt':time.time(),'mode':'reference','ratesToUSD':{'USD':1}}
        with sqlite3.connect(self.path) as db:db.execute('INSERT OR REPLACE INTO fx VALUES(1,?)',(json.dumps(value),))
        self.assertEqual(self.get('system').json['fx']['state'],'recent')
        value['fetchedAt']=time.time()-90000
        with sqlite3.connect(self.path) as db:db.execute('UPDATE fx SET value=?',(json.dumps(value),))
        self.assertEqual(self.get('system').json['fx']['state'],'expired')

    def test_migration_backfills_only_available_history_once(self):
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=50));self.issue(self.b,'gold')
        self.command(self.b,'underwriting/issue-card',dict(cardId='gold',income=50000,months=12,existing=0,holderName='Test'))
        before=self.state(self.b)
        with sqlite3.connect(self.path) as db:
            db.execute('DELETE FROM business_records');db.execute('DELETE FROM ledger_records');db.execute("DELETE FROM schema_migrations WHERE name='admin-history-v1'")
        create_app(dict(self.app.config))
        records=self.get('records').json['items'];self.assertTrue(all(r['legacy'] for r in records))
        apprec=next(r for r in records if r['route']=='underwriting/issue-card' and r['status']<400)
        detail=self.get('records/'+apprec['id']).json['details']
        self.assertNotIn('inputs',detail);self.assertEqual(detail['ruleVersion'],'legacy-unrecorded')
        self.assertEqual(self.get('applications?status=failed').json['total'],1)
        count=len(records);create_app(dict(self.app.config))
        self.assertEqual(self.get('records').json['total'],count);self.assertEqual(self.state(self.b),before)

    def test_admin_mount_and_scoped_cookie(self):
        config=dict(self.app.config);config.update(BASE_PATH='/bank')
        mounted=create_app(config);client=mounted.test_client();client.set_cookie('jwb_session',self.a.get_cookie('jwb_session').value,path='/bank/')
        response=client.get('/bank/admin/');self.assertEqual(response.status_code,200);self.assertIn(b'../assets/admin.js',response.data);response.close()
        for asset in ('admin.js','admin.css','fonts.css'):
            response=client.get('/bank/assets/'+asset);self.assertEqual(response.status_code,200);response.close()
        self.assertEqual(client.get('/bank/api/admin/users').status_code,200)
        self.assertEqual(client.get('/admin/').status_code,404)
        self.assertEqual(client.get('/bank/admin').status_code,308)
        guest=mounted.test_client();self.assertEqual(guest.get('/bank/admin/').headers['Location'],'/bank/#admin')

    def test_admin_limit_and_private_response_cache_headers(self):
        response=self.get('summary');self.assertEqual(response.headers['Cache-Control'],'no-store')
        with sqlite3.connect(self.path) as db:db.execute('INSERT OR REPLACE INTO limits VALUES(?,?,?)',('admin-read:'+self.uid,180,int(time.time())+60))
        response=self.get('users');self.assertEqual(response.status_code,429);self.assertGreater(response.json['retryAfter'],0)

    def test_dependency_failure_is_recorded_and_same_retry_can_recover(self):
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=100))
        quote=self.post(self.b,'quotes',{'from':'USD','to':'CNY','amount':10}).json
        provider=self.app.config['FX_TEST_PROVIDER']
        def unavailable():raise DomainError('汇率暂不可用 / Rates unavailable',503)
        self.app.config['FX_TEST_PROVIDER']=unavailable;key=uuid.uuid4().hex
        response=self.command(self.b,'treasury/fx-swap',{'quoteId':quote['quoteId']},key)
        self.assertEqual(response.status_code,503)
        self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],100)
        self.app.config['FX_TEST_PROVIDER']=provider
        self.assertEqual(self.command(self.b,'treasury/fx-swap',{'quoteId':quote['quoteId']},key).status_code,200)
        self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],90)
        rows=self.get('records?route=treasury/fx-swap').json['items']
        self.assertEqual(sorted(r['status'] for r in rows),[200,503])

if __name__=='__main__':unittest.main()
