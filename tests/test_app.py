import concurrent.futures
import json
import sqlite3
import tempfile
import time
import unittest
import uuid
from backup_tools import backup_database, daily_backup, verify_backup, restore_database
from pathlib import Path
from app import create_app

class CloudTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'test.sqlite3')
        self.app=create_app(dict(TESTING=True,SECRET_KEY='s'*64,DATABASE=self.path,COOKIE_SECURE=False,MAIL_MODE='memory',PUBLIC_ORIGIN='http://localhost',FX_TEST_PROVIDER=lambda:dict(ratesToUSD={'USD':1,'CNY':1/7,'HKD':1/7.8,'JPY':1/150,'GBP':1.25,'EUR':1.1},source='test fixture',asOf='2026-10-17T00:00:00Z',fetchedAt=time.time(),mode='reference',stale=False)))
        self.a=self.app.test_client();self.b=self.app.test_client();self.csrf={}
        self.register(self.a,'one@example.com');self.register(self.b,'two@example.com')
    def tearDown(self): self.tmp.cleanup()
    def post(self,c,path,data,**headers): return c.post('/api/'+path,json=data,headers={'X-JWB-Client':'web','X-CSRF-Token':self.csrf.get(id(c),''),**headers})
    def register(self,c,email):
        r=self.post(c,'auth/request-code',dict(email=email,purpose='register'));self.assertEqual(r.status_code,200)
        code=self.app.extensions['test_inbox'][-1]['code']
        r=self.post(c,'auth/register',dict(email=email,code=code,password='strong-password!'));self.assertEqual(r.status_code,200,r.json)
        self.csrf[id(c)]=r.json['csrf']
    def command(self,c,route,data,key=None): return self.post(c,'v1/'+route,data,**{'Idempotency-Key':key or uuid.uuid4().hex})
    def state(self,c): return c.get('/api/state').json['db']
    def issue(self,c,product='everyday'):
        r=self.command(c,'underwriting/issue-card',dict(cardId=product,income=100000,months=12,existing=0,holderName='TEST HOLDER',currentLimit=999999999));self.assertEqual(r.status_code,201,r.json);return r.json['issuedCard']
    def test_zero_account_and_guest_gate(self):
        guest=self.app.test_client();self.assertEqual(guest.get('/api/state').status_code,401)
        response=guest.get('/');self.assertEqual(response.status_code,200);response.close();self.assertEqual(len(guest.get('/api/catalog').json),6)
        self.assertEqual(guest.get('/.env').status_code,404)
        value=self.state(self.a);self.assertEqual(value['cards'],[]);self.assertEqual(value['jrPointsBalance'],0);self.assertEqual(sum(value['treasuryWallets'].values()),0)
    def test_idempotency_and_isolation(self):
        key=uuid.uuid4().hex
        for _ in range(2): self.assertEqual(self.command(self.a,'treasury/wire-in',dict(currency='USD',amount='100'),key).status_code,200)
        self.assertEqual(self.state(self.a)['treasuryWallets']['USD'],100);self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],0)
        self.assertEqual(self.command(self.a,'treasury/wire-in',dict(currency='USD',amount='200'),key).status_code,409)
    def test_server_approval_and_card_ownership(self):
        r=self.command(self.a,'underwriting/issue-card',dict(cardId='everyday',income=0,months=0,existing=99999999,holderName='X',approved=True));self.assertEqual(r.status_code,422)
        card=self.issue(self.a);self.assertLessEqual(card['creditLimit'],25000)
        self.assertEqual(self.command(self.b,'cards/security-freeze',{'uid':card['uid']}).status_code,404)
        self.assertEqual(self.command(self.a,'credit/cli-3x',{'uid':card['uid']}).status_code,409)
        self.assertEqual(self.command(self.a,'underwriting/issue-card',dict(cardId='everyday',income=100000,holderName='X')).status_code,409)
    def test_spend_rewards_repay_and_freeze(self):
        c=self.issue(self.a);purchase=dict(uid=c['uid'],currency='USD',amount=1500,category='travel',merchant='Test airline')
        self.assertEqual(self.command(self.a,'pos/authorize',purchase).status_code,200)
        value=self.state(self.a);self.assertTrue(value['cards'][0]['welcomeUnlocked']);self.assertEqual(value['jrPointsBalance'],38000)
        self.command(self.a,'pos/authorize',dict(purchase,amount=1));self.assertEqual(self.state(self.a)['jrPointsBalance'],38002)
        self.command(self.a,'cards/security-freeze',{'uid':c['uid']});self.assertEqual(self.command(self.a,'pos/authorize',purchase).status_code,423)
        self.assertEqual(self.command(self.a,'cards/repay',dict(uid=c['uid'],method='USD')).status_code,402)
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=2000));self.assertEqual(self.command(self.a,'cards/repay',dict(uid=c['uid'],method='USD')).status_code,200)
        self.assertEqual(self.state(self.a)['cards'][0]['statementBalance'],0)
    def test_quote_ownership_and_single_use(self):
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=100))
        q=self.post(self.a,'quotes',{'from':'USD','to':'CNY','amount':10}).json
        self.assertEqual(self.command(self.b,'treasury/fx-swap',dict(quoteId=q['quoteId'])).status_code,409)
        self.assertEqual(self.command(self.a,'treasury/fx-swap',dict(quoteId=q['quoteId'],received=100000)).status_code,200)
        value=self.state(self.a);self.assertEqual(value['treasuryWallets']['USD'],90);self.assertEqual(value['treasuryWallets']['CNY'],70)
        self.assertEqual(self.command(self.a,'treasury/fx-swap',dict(quoteId=q['quoteId'])).status_code,409)
    def test_csrf_and_bad_inputs(self):
        self.assertEqual(self.a.post('/api/auth/logout',json={}).status_code,403)
        r=self.post(self.a,'auth/logout',{},Origin='https://evil.test');self.assertEqual(r.status_code,403)
        for amount in ('NaN','Infinity',-1,0,0.001): self.assertEqual(self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=amount)).status_code,400)
        self.assertEqual(self.post(self.a,'assessment',{'cardId':[]}).status_code,400)
    def test_otp_one_use_attempts_and_password_reset_revokes(self):
        self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'))
        # Mail cooldown is shared across purposes, reset it as fixture setup.
        with sqlite3.connect(self.path) as db: db.execute('DELETE FROM limits')
        self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'));code=self.app.extensions['test_inbox'][-1]['code']
        other=self.app.test_client();r=self.post(other,'auth/login-code',dict(email='one@example.com',code=code));self.assertEqual(r.status_code,200)
        self.assertEqual(self.post(other,'auth/login-code',dict(email='one@example.com',code=code)).status_code,400)
        with sqlite3.connect(self.path) as db: db.execute('DELETE FROM limits')
        self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='reset'));code=self.app.extensions['test_inbox'][-1]['code']
        self.assertEqual(self.post(other,'auth/reset-password',dict(email='one@example.com',code=code,password='changed-password!')).status_code,200)
        self.assertEqual(self.a.get('/api/state').status_code,401);self.assertEqual(other.get('/api/state').status_code,401)
        self.assertEqual(self.post(other,'auth/login',dict(email='one@example.com',password='changed-password!')).status_code,200)
    def test_concurrent_replay_exactly_once(self):
        cookie=self.a.get_cookie('jwb_session').value;csrf=self.csrf[id(self.a)];key=uuid.uuid4().hex
        def run(_):
            client=self.app.test_client();client.set_cookie('jwb_session',cookie)
            return client.post('/api/v1/treasury/wire-in',json=dict(currency='USD',amount=100),headers={'X-JWB-Client':'web','X-CSRF-Token':csrf,'Idempotency-Key':key}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: self.assertEqual(list(pool.map(run,range(4))),[200]*4)
        self.assertEqual(self.state(self.a)['treasuryWallets']['USD'],100)
    def test_annual_fee_and_reset_only_current_user(self):
        c=self.issue(self.a,'gold');self.assertEqual(c['statementBalance'],295)
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=5));self.command(self.a,'core/reset',{'currentPassword':'strong-password!'})
        self.assertEqual(self.state(self.a)['cards'],[]);self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],5)
    def test_missing_smtp_truthful(self):
        self.app.config.update(MAIL_MODE='smtp',SMTP_HOST='',MAIL_FROM='')
        self.assertFalse(self.a.get('/api/auth/me').json['mailReady'])
        with sqlite3.connect(self.path) as db: db.execute('DELETE FROM limits')
        r=self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'));self.assertEqual(r.status_code,503)

    def test_expired_quote_and_otp_attempt_limit(self):
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=100))
        quote=self.post(self.a,'quotes',{'from':'USD','to':'JPY','amount':1}).json
        with sqlite3.connect(self.path) as db:
            db.execute('UPDATE quotes SET expires=0 WHERE id=?',(quote['quoteId'],));db.execute('DELETE FROM limits')
        self.assertEqual(self.command(self.a,'treasury/fx-swap',dict(quoteId=quote['quoteId'])).status_code,409)
        self.assertEqual(self.state(self.a)['treasuryWallets']['USD'],100)
        self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'));code=self.app.extensions['test_inbox'][-1]['code']
        bad='000000' if code!='000000' else '111111'
        for _ in range(5):self.assertEqual(self.post(self.a,'auth/login-code',dict(email='one@example.com',code=bad)).status_code,400)
        self.assertEqual(self.post(self.a,'auth/login-code',dict(email='one@example.com',code=code)).status_code,400)

    def test_product_change_preserves_bonus_and_debt_cap(self):
        card=self.issue(self.a,'gold')
        self.command(self.a,'pos/authorize',dict(uid=card['uid'],currency='USD',amount=10,category='travel',merchant='Travel'))
        self.assertEqual(self.command(self.a,'cards/product-change',dict(uid=card['uid'],cardId='platinum')).status_code,200)
        changed=self.state(self.a)['cards'][0];self.assertEqual(changed['welcomeProductId'],'gold');self.assertEqual(changed['spendProgress'],10)
        self.assertEqual(changed['statementBalance'],705)
        self.command(self.a,'cards/product-change',dict(uid=card['uid'],cardId='gold'))
        self.command(self.a,'cards/product-change',dict(uid=card['uid'],cardId='platinum'))
        self.assertEqual(self.state(self.a)['cards'][0]['statementBalance'],705)

    def test_concurrent_distinct_deposits_have_no_lost_updates(self):
        cookie=self.a.get_cookie('jwb_session').value;csrf=self.csrf[id(self.a)]
        def run(_):
            client=self.app.test_client();client.set_cookie('jwb_session',cookie)
            return client.post('/api/v1/treasury/wire-in',json=dict(currency='USD',amount=100),headers={'X-JWB-Client':'web','X-CSRF-Token':csrf,'Idempotency-Key':uuid.uuid4().hex}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:self.assertEqual(list(pool.map(run,range(4))),[200]*4)
        self.assertEqual(self.state(self.a)['treasuryWallets']['USD'],400)

    def test_bank_subdirectory_mount_and_cookie(self):
        config=dict(self.app.config);config.update(BASE_PATH='/bank',DATABASE=str(Path(self.tmp.name)/'bank.sqlite3'),PUBLIC_ORIGIN='https://jasa.hk')
        mounted=create_app(config);client=mounted.test_client()
        response=client.get('/bank');self.assertEqual(response.status_code,308);self.assertEqual(response.headers['Location'],'/bank/')
        self.assertEqual(client.get('/').status_code,404)
        response=client.get('/bank/');self.assertEqual(response.status_code,200);self.assertIn(b'src="assets/cloud.js',response.data);response.close()
        for asset in ['cloud.js','suite.js','ui.js','ui.css']:
            response=client.get('/bank/assets/'+asset+'?v=20261018-2');self.assertEqual(response.status_code,200);response.close()
        self.assertEqual(client.get('/bank/api/state').status_code,401)
        headers={'X-JWB-Client':'web','Origin':'https://jasa.hk'}
        response=client.post('/bank/api/auth/request-code',json=dict(email='bank@example.com',purpose='register'),headers=headers);self.assertEqual(response.status_code,200)
        code=mounted.extensions['test_inbox'][-1]['code']
        response=client.post('/bank/api/auth/register',json=dict(email='bank@example.com',password='strong-password!',code=code),headers=headers)
        self.assertEqual(response.status_code,200);self.assertIn('Path=/bank/',response.headers['Set-Cookie'])
        csrf=response.json['csrf'];self.assertEqual(client.get('/bank/api/state').status_code,200)
        response=client.post('/bank/api/auth/logout',json={},headers=dict(headers,**{'X-CSRF-Token':csrf}));self.assertEqual(response.status_code,200)
        self.assertIn('Path=/bank/',response.headers['Set-Cookie']);self.assertEqual(client.get('/bank/api/state').status_code,401)

    def clear_mail_counters(self):
        with sqlite3.connect(self.path) as db:db.execute('DELETE FROM limits')

    def test_mail_rejected_retries_do_not_exhaust_ip(self):
        self.clear_mail_counters()
        before=len(self.app.extensions['test_inbox'])
        data=dict(email='one@example.com',purpose='login')
        response=self.post(self.a,'auth/request-code',data);self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['retryAfter'],60)
        for _ in range(25):
            response=self.post(self.a,'auth/request-code',data)
            self.assertEqual(response.status_code,429);self.assertEqual(response.json['rateLimit'],'email_cooldown')
            self.assertGreater(response.json['retryAfter'],0);self.assertIn('Retry-After',response.headers)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT count FROM limits WHERE key LIKE 'mail-ip:%'").fetchone()[0],1)
            self.assertEqual(db.execute("SELECT count FROM limits WHERE key='mail-hour:one@example.com'").fetchone()[0],1)
        self.assertEqual(len(self.app.extensions['test_inbox'])-before,1)
        self.assertEqual(self.post(self.b,'auth/request-code',dict(email='two@example.com',purpose='login')).status_code,200)

    def test_mail_email_hour_limit_reports_exact_wait(self):
        self.clear_mail_counters();self.app.config['MAIL_EMAIL_HOURLY_LIMIT']=2
        for _ in range(2):
            self.assertEqual(self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login')).status_code,200)
            with sqlite3.connect(self.path) as db:db.execute("UPDATE limits SET until=0 WHERE key='mail:one@example.com'")
        response=self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'))
        self.assertEqual(response.status_code,429);self.assertEqual(response.json['rateLimit'],'email_hourly')
        self.assertGreater(response.json['retryAfter'],3500)
        self.assertEqual(self.post(self.b,'auth/request-code',dict(email='two@example.com',purpose='login')).status_code,200)

    def test_mail_ip_quota_applies_across_emails(self):
        self.clear_mail_counters();self.app.config['MAIL_IP_HOURLY_LIMIT']=2
        for address in ('first@example.com','second@example.com'):
            self.assertEqual(self.post(self.a,'auth/request-code',dict(email=address,purpose='register')).status_code,200)
        response=self.post(self.a,'auth/request-code',dict(email='third@example.com',purpose='register'))
        self.assertEqual(response.status_code,429);self.assertEqual(response.json['rateLimit'],'ip_hourly')
        with sqlite3.connect(self.path) as db:self.assertIsNone(db.execute("SELECT count FROM limits WHERE key='mail:third@example.com'").fetchone())

    def test_concurrent_mail_requests_send_one_code(self):
        self.clear_mail_counters();before=len(self.app.extensions['test_inbox'])
        def run(_):
            with self.app.test_client() as client:return client.post('/api/auth/request-code',json=dict(email='one@example.com',purpose='login'),headers={'X-JWB-Client':'web'}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(run,range(6)))
        self.assertEqual(results.count(200),1);self.assertEqual(results.count(429),5)
        self.assertEqual(len(self.app.extensions['test_inbox'])-before,1)

    def test_unconfigured_mail_does_not_consume_quota(self):
        self.clear_mail_counters();self.app.config.update(MAIL_MODE='smtp',SMTP_HOST='',MAIL_FROM='')
        response=self.post(self.a,'auth/request-code',dict(email='one@example.com',purpose='login'))
        self.assertEqual(response.status_code,503)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM limits').fetchone()[0],0)

    def login_device(self,email='one@example.com',pw='strong-password!'):
        client=self.app.test_client()
        result=self.post(client,'auth/login',dict(email=email,password=pw))
        self.assertEqual(result.status_code,200,result.json);self.csrf[id(client)]=result.json['csrf']
        return client

    def test_device_list_ownership_and_revoke(self):
        other=self.login_device()
        sessions=self.a.get('/api/auth/sessions').json['sessions']
        self.assertEqual(len(sessions),2);self.assertEqual(sum(s['current'] for s in sessions),1)
        self.assertNotIn('token',sessions[0]);self.assertTrue(all(s['id'] for s in sessions))
        target=next(s['id'] for s in sessions if not s['current'])
        self.assertEqual(self.post(self.b,'auth/revoke-session',{'id':target}).status_code,404)
        self.assertEqual(self.post(self.a,'auth/revoke-session',{'id':target}).status_code,200)
        self.assertEqual(other.get('/api/state').status_code,401)
        self.assertEqual(self.a.get('/api/state').status_code,200)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM session_details').fetchone()[0],2)

    def test_revoke_other_devices_handles_legacy_sessions(self):
        other=self.login_device()
        with sqlite3.connect(self.path) as db:db.execute('DELETE FROM session_details')
        self.assertEqual(len(self.a.get('/api/auth/sessions').json['sessions']),2)
        self.assertEqual(self.post(self.a,'auth/revoke-session',{'others':True}).status_code,200)
        self.assertEqual(other.get('/api/state').status_code,401);self.assertEqual(self.a.get('/api/state').status_code,200)

    def test_change_password_requires_current_and_revokes_all(self):
        other=self.login_device();self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=123))
        data={'currentPassword':'wrong-password','password':'a-new-strong-password'}
        self.assertEqual(self.post(self.a,'auth/change-password',data).status_code,400)
        self.assertEqual(other.get('/api/state').status_code,200)
        data['currentPassword']='strong-password!'
        self.assertEqual(self.post(self.a,'auth/change-password',data).status_code,200)
        self.assertEqual(self.a.get('/api/state').status_code,401);self.assertEqual(other.get('/api/state').status_code,401)
        self.assertEqual(self.post(self.a,'auth/login',dict(email='one@example.com',password='strong-password!')).status_code,401)
        renewed=self.login_device(pw='a-new-strong-password')
        self.assertEqual(self.state(renewed)['treasuryWallets']['USD'],123)

    def email_change_codes(self,client,new_email):
        self.clear_mail_counters();values={}
        for target in ('old','new'):
            result=self.post(client,'auth/change-email/request-code',{'target':target,'newEmail':new_email,'currentPassword':'strong-password!'})
            self.assertEqual(result.status_code,200,result.json)
            values[target]=self.app.extensions['test_inbox'][-1]['code']
        return dict(currentPassword='strong-password!',newEmail=new_email,oldCode=values['old'],newCode=values['new'])

    def test_email_change_two_proofs_atomic_and_preserves_account(self):
        other=self.login_device();uid=self.a.get('/api/auth/me').json['user']['id']
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=345));self.issue(self.a)
        data=self.email_change_codes(self.a,'new@example.com')
        wrong='111111' if data['newCode']!='111111' else '222222'
        self.assertEqual(self.post(self.a,'auth/change-email',dict(data,newCode=wrong)).status_code,400)
        self.assertEqual(self.a.get('/api/auth/me').json['user']['email'],'one@example.com')
        self.assertEqual(self.post(self.a,'auth/change-email',data).status_code,200)
        self.assertEqual(other.get('/api/state').status_code,401);self.assertEqual(self.a.get('/api/state').status_code,401)
        renewed=self.login_device(email='new@example.com')
        self.assertEqual(renewed.get('/api/auth/me').json['user']['id'],uid)
        self.assertEqual(self.state(renewed)['treasuryWallets']['USD'],345);self.assertEqual(len(self.state(renewed)['cards']),1)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM codes WHERE email IN (?,?)',('one@example.com','new@example.com')).fetchone()[0],0)

    def test_email_change_cannot_use_other_users_or_registration_codes(self):
        data=self.email_change_codes(self.a,'new@example.com')
        self.assertEqual(self.post(self.b,'auth/change-email',data).status_code,400)
        self.assertEqual(self.post(self.a,'auth/change-email',dict(data,currentPassword='wrong-password')).status_code,400)
        self.assertEqual(self.post(self.a,'auth/change-email',dict(data,newEmail='two@example.com')).status_code,409)
        self.assertEqual(self.post(self.a,'auth/change-email',data).status_code,200)

    def test_security_csrf_and_rate_limits(self):
        self.assertEqual(self.app.test_client().get('/api/auth/sessions').status_code,401)
        self.assertEqual(self.a.post('/api/auth/change-password',json={},headers={'X-JWB-Client':'web'}).status_code,403)
        for _ in range(10):self.assertEqual(self.post(self.a,'auth/change-password',{'currentPassword':'bad','password':'new-password-strong'}).status_code,400)
        result=self.post(self.a,'auth/change-password',{'currentPassword':'bad','password':'new-password-strong'})
        self.assertEqual(result.status_code,429);self.assertGreater(result.json['retryAfter'],0)
        for _ in range(12):self.assertEqual(self.post(self.b,'auth/login',{'email':'two@example.com','password':'bad'}).status_code,401)
        self.assertEqual(self.post(self.b,'auth/login',{'email':'two@example.com','password':'bad'}).status_code,429)

    def test_guide_progress_and_preferences_are_isolated(self):
        initial=self.a.get('/api/experience').json;self.assertFalse(initial['hidden']);self.assertFalse(any(initial['steps'].values()))
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=10));card=self.issue(self.a)
        self.command(self.a,'pos/authorize',dict(uid=card['uid'],currency='USD',amount=1,category='everyday',merchant='Test'))
        self.post(self.a,'experience',{'ledgerSeen':True,'hidden':True})
        result=self.a.get('/api/experience').json;self.assertTrue(result['hidden']);self.assertTrue(all(result['steps'].values()))
        other=self.login_device();self.assertEqual(other.get('/api/experience').json,result)
        self.assertFalse(any(self.b.get('/api/experience').json['steps'].values()))
        self.assertEqual(self.post(self.a,'experience',{'funds':True}).status_code,400)
        self.assertEqual(self.post(self.a,'experience',{'hidden':'false'}).status_code,400)
        self.command(self.a,'core/reset',{'currentPassword':'strong-password!'})
        reset=self.a.get('/api/experience').json
        self.assertFalse(any(reset['steps'].values()));self.assertTrue(reset['hidden'])

    def test_legacy_schema_upgrade_keeps_accounts(self):
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=50))
        with sqlite3.connect(self.path) as db:
            for table in ('session_details','security_events','preferences'):db.execute('DROP TABLE '+table)
        upgraded=create_app(dict(self.app.config));client=upgraded.test_client()
        client.set_cookie('jwb_session',self.a.get_cookie('jwb_session').value)
        self.assertEqual(client.get('/api/state').json['db']['treasuryWallets']['USD'],50)
        self.assertTrue(client.get('/api/auth/sessions').json['sessions'][0]['current'])

    def test_backup_drill_checksum_restore_and_safety_copy(self):
        target=Path(self.tmp.name)/'snapshot.sqlite3';safety=Path(self.tmp.name)/'before-restore.sqlite3'
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=100))
        report=backup_database(self.path,target);self.assertEqual(report['restoreDrill'],'passed');self.assertEqual(report['users'],2)
        self.assertEqual(target.stat().st_mode & 0o777,0o600)
        self.command(self.a,'treasury/wire-in',dict(currency='USD',amount=200))
        restore_database(target,self.path,safety)
        self.assertEqual(self.a.get('/api/state').status_code,401)
        renewed=self.login_device();self.assertEqual(self.state(renewed)['treasuryWallets']['USD'],100)
        with sqlite3.connect(safety) as db:
            value=json.loads(db.execute("SELECT state FROM accounts JOIN users ON users.id=accounts.user_id WHERE email='one@example.com'").fetchone()[0])
            self.assertEqual(value['treasuryWallets']['USD'],300)
        self.assertEqual(verify_backup(safety)['restoreDrill'],'passed')
        with self.assertRaises(FileExistsError):backup_database(self.path,target)
        raw=target.read_bytes();target.write_bytes(raw+b'corruption')
        with self.assertRaisesRegex(ValueError,'SHA-256'):verify_backup(target)

    def test_backup_rotation_preserves_manual_and_rejects_invalid_source(self):
        directory=Path(self.tmp.name)/'backups'
        for _ in range(3):daily_backup(self.path,directory,2)
        self.assertEqual(len(list(directory.glob('*.sqlite3'))),2)
        manual=directory/'manual.sqlite3';backup_database(self.path,manual)
        daily_backup(self.path,directory,2);self.assertTrue(manual.exists())
        unrelated=Path(self.tmp.name)/'not-jwb.sqlite3'
        with sqlite3.connect(unrelated) as db:db.execute('CREATE TABLE unrelated(x)')
        before=list(directory.glob('*.sqlite3'))
        with self.assertRaises(ValueError):daily_backup(unrelated,directory,2)
        self.assertEqual(sorted(before),sorted(directory.glob('*.sqlite3')))
        safety=directory/'should-not-exist.sqlite3'
        with self.assertRaises(ValueError):restore_database(unrelated,self.path,safety)
        self.assertFalse(safety.exists())

if __name__=='__main__':unittest.main()
