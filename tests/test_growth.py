import json
from pathlib import Path
import sqlite3
import time
import unittest
import uuid
from datetime import datetime,timezone
import test_app as fixtures
from growth_security import totp_code
from backup_tools import daily_backup

class GrowthTests(unittest.TestCase):
    setUpBase=fixtures.CloudTests.setUp
    tearDown=fixtures.CloudTests.tearDown
    post=fixtures.CloudTests.post
    register=fixtures.CloudTests.register
    command=fixtures.CloudTests.command
    state=fixtures.CloudTests.state
    issue=fixtures.CloudTests.issue
    def setUp(self):
        self.setUpBase();self.now=int(time.time());self.app.config['FEATURE_NOW']=lambda:self.now
        self.uid=self.a.get('/api/auth/me').json['user']['id'];self.other=self.b.get('/api/auth/me').json['user']['id'];self.app.config['BACKUP_DIR']=str(Path(self.tmp.name)/'backups')
        with sqlite3.connect(self.path) as db:db.execute('UPDATE users SET admin=1 WHERE id=?',(self.uid,))
    def purchase(self,card,amount=100,category='everyday'):
        r=self.command(self.b,'pos/authorize',{'uid':card['uid'],'currency':'USD','amount':amount,'category':category,'merchant':'GROWTH DEMO'});self.assertEqual(r.status_code,200,r.json)
        return self.b.get('/api/card-services').json['purchases'][0]['id']
    def secure(self,c,route,data,key=None):return self.command(c,route,{'currentPassword':'strong-password!',**data},key)
    def mfa(self):
        setup=self.post(self.b,'security/mfa/setup',{'currentPassword':'strong-password!'});self.assertEqual(setup.status_code,200,setup.json);secret=setup.json['secret']
        r=self.post(self.b,'security/mfa/enable',{'currentPassword':'strong-password!','code':totp_code(secret,self.now//30)});self.assertEqual(r.status_code,200,r.json)
        return secret,r.json['recoveryCodes']
    def test_refund_rounding_reconciles_original_credits_rewards_and_billing(self):
        card=self.issue(self.b,'gold');rid=self.purchase(card,100,'dining');pool=self.state(self.b)['cards'][0]['remainingCreditPool']
        for amount in [33.33,66.67]:
            r=self.secure(self.b,'pos/refund',{'uid':card['uid'],'recordId':rid,'amount':amount,'reason':'Proportional refund test'});self.assertEqual(r.status_code,200,r.json)
        value=self.state(self.b);self.assertEqual(value['cards'][0]['spendProgress'],0);self.assertEqual(value['jrPointsBalance'],0);self.assertEqual(value['cards'][0]['statementBalance'],295);self.assertGreater(value['cards'][0]['remainingCreditPool'],pool)
        self.assertEqual(self.b.get('/api/billing').json['cards'][0]['debtCents'],29500)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute('SELECT SUM(purchase_cents),SUM(credits_cents),SUM(reward_points) FROM spend_facts WHERE user_id=?',(self.other,)).fetchone(),(0,0,0))
    def test_refund_after_repayment_surplus_and_spent_rewards(self):
        card=self.issue(self.b);rid=self.purchase(card,100);self.command(self.b,'cards/repay',{'uid':card['uid'],'method':'JR'});before=self.state(self.b)['cards'][0]['statementBalance']
        r=self.secure(self.b,'pos/refund',{'uid':card['uid'],'recordId':rid,'amount':100,'reason':'Refund after using rewards'});self.assertEqual(r.status_code,200,r.json)
        value=self.state(self.b);self.assertEqual(value['cards'][0]['statementBalance'],0);self.assertEqual(value['treasuryWallets']['USD'],3);self.assertLess(value['jrPointsBalance'],0)
        old=value['jrPointsBalance'];self.purchase(card,10);self.assertGreater(self.state(self.b)['jrPointsBalance'],old)
    def test_refund_scope_idempotency_and_overrefund(self):
        card=self.issue(self.b);rid=self.purchase(card,10);data={'uid':card['uid'],'recordId':rid,'amount':5,'reason':'Refund replay check'};key=uuid.uuid4().hex
        self.assertEqual(self.secure(self.a,'pos/refund',data).status_code,404)
        self.assertEqual(self.secure(self.b,'pos/refund',data,key).status_code,200);self.assertEqual(self.secure(self.b,'pos/refund',{**data,'factor':'changed'},key).status_code,200)
        before=self.state(self.b);self.assertEqual(self.secure(self.b,'pos/refund',{**data,'amount':6}).status_code,409);after=self.state(self.b);self.assertEqual(before['cards'],after['cards']);self.assertEqual(self.b.get('/api/card-services').json['purchases'][0]['refundedCents'],500)
    def test_welcome_bonus_is_reversed_below_net_threshold(self):
        card=self.issue(self.b);rid=self.purchase(card,1500);self.assertTrue(self.state(self.b)['cards'][0]['welcomeUnlocked'])
        r=self.secure(self.b,'pos/refund',{'uid':card['uid'],'recordId':rid,'amount':1,'reason':'Welcome threshold return'});self.assertEqual(r.status_code,200,r.json);self.assertFalse(self.state(self.b)['cards'][0]['welcomeUnlocked'])
    def test_replacement_and_closure_preserve_history_and_block_closed_spending(self):
        card=self.issue(self.b,'gold');self.assertEqual(self.secure(self.b,'cards/close',{'uid':card['uid']}).status_code,409);self.assertEqual(self.secure(self.b,'cards/replace',{'uid':card['uid'],'reason':'expired'}).status_code,409)
        r=self.secure(self.b,'cards/replace',{'uid':card['uid'],'reason':'lost'});self.assertEqual(r.status_code,200,r.json);new=r.json['db']['cards'][0]
        for k in ['uid','openedAt','statementBalance','creditLimit','spendProgress']:self.assertEqual(new[k],card[k])
        self.assertNotEqual(new['cardNumber'],card['cardNumber']);self.command(self.b,'treasury/wire-in',{'currency':'USD','amount':295});self.command(self.b,'cards/repay',{'uid':card['uid'],'method':'USD'})
        self.assertEqual(self.secure(self.b,'cards/close',{'uid':card['uid']}).status_code,200);self.assertEqual(self.command(self.b,'cards/security-freeze',{'uid':card['uid']}).status_code,409)
        self.assertEqual(self.command(self.b,'pos/authorize',{'uid':card['uid'],'currency':'USD','amount':1,'category':'everyday','merchant':'Closed'}).status_code,409);self.issue(self.b,'gold');self.assertEqual(len(self.state(self.b)['cards']),2)
    def test_renewal_is_once_and_legacy_anniversaries_are_not_backcharged(self):
        card=self.issue(self.b,'gold');self.now=card['renewAt']+1
        self.assertEqual(self.state(self.b)['cards'][0]['statementBalance'],590);self.assertEqual(self.state(self.b)['cards'][0]['statementBalance'],590)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM business_records WHERE route='cards/annual-renewal' AND user_id=?",(self.other,)).fetchone()[0],1)
        self.command(self.b,'treasury/wire-in',{'currency':'USD','amount':590});self.command(self.b,'cards/repay',{'uid':card['uid'],'method':'USD'});self.secure(self.b,'cards/close',{'uid':card['uid']});self.now+=370*86400;self.assertEqual(self.state(self.b)['cards'][0]['statementBalance'],0)
        with sqlite3.connect(self.path) as db:
            value=json.loads(db.execute('SELECT state FROM accounts WHERE user_id=?',(self.other,)).fetchone()[0]);c=value['cards'][0];c['status']='ACTIVE';c['openedAt']='2020-01-01T00:00:00+00:00'
            for k in ['renewAt','expiresAt','annualFeePeriodPaid']:c.pop(k,None)
            db.execute('UPDATE accounts SET state=? WHERE user_id=?',(json.dumps(value),self.other))
        value=self.state(self.b);self.assertEqual(value['cards'][0]['statementBalance'],0);self.assertGreater(value['cards'][0]['renewAt'],self.now);self.assertEqual(value['cards'][0]['status'],'EXPIRED')
    def test_sensitive_passwords_required_and_not_logged(self):
        card=self.issue(self.b);self.assertEqual(self.command(self.b,'cards/close',{'uid':card['uid']}).status_code,400);self.assertEqual(self.command(self.b,'core/reset',{}).status_code,400);self.assertEqual(self.secure(self.b,'cards/rotate-cvv',{'uid':card['uid']}).status_code,200)
        with sqlite3.connect(self.path) as db:
            for row in db.execute('SELECT details FROM business_records'):self.assertNotIn('strong-password!',row[0]);self.assertNotIn('currentPassword',row[0])
    def test_totp_rfc_vector_encrypted_secret_login_replay_and_recovery(self):
        self.assertEqual(totp_code('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ',1),'287082');secret,codes=self.mfa()
        with sqlite3.connect(self.path) as db:
            row=db.execute('SELECT secret,recovery FROM mfa WHERE user_id=?',(self.other,)).fetchone();self.assertNotIn(secret,row[0]);self.assertNotIn(codes[0].replace('-',''),row[1])
        client=self.app.test_client();r=self.post(client,'auth/login',{'email':'two@example.com','password':'strong-password!'});self.assertTrue(r.json['mfaRequired']);self.assertIsNone(client.get_cookie('jwb_session'));challenge=r.json['challenge']
        self.assertEqual(self.post(client,'auth/mfa-login',{'challenge':challenge,'factor':totp_code(secret,self.now//30)}).status_code,400)
        good=self.post(client,'auth/mfa-login',{'challenge':challenge,'factor':codes[0]});self.assertEqual(good.status_code,200,good.json);self.assertEqual(self.post(client,'auth/mfa-login',{'challenge':challenge,'factor':codes[1]}).status_code,401)
        self.assertEqual(self.post(self.b,'security/mfa/disable',{'currentPassword':'strong-password!','factor':codes[0]}).status_code,400);self.assertEqual(self.post(self.b,'security/mfa/disable',{'currentPassword':'strong-password!','factor':codes[1]}).status_code,200)
    def test_email_login_and_password_reset_cannot_bypass_mfa(self):
        secret,codes=self.mfa();guest=self.app.test_client();
        with sqlite3.connect(self.path) as db:db.execute("DELETE FROM limits WHERE key LIKE 'mail:%'")
        self.post(guest,'auth/request-code',{'email':'two@example.com','purpose':'login'});code=self.app.extensions['test_inbox'][-1]['code'];r=self.post(guest,'auth/login-code',{'email':'two@example.com','code':code});self.assertTrue(r.json['mfaRequired']);self.assertIsNone(guest.get_cookie('jwb_session'))
        with sqlite3.connect(self.path) as db:db.execute("DELETE FROM limits WHERE key LIKE 'mail:%'")
        self.post(guest,'auth/request-code',{'email':'two@example.com','purpose':'reset'});code=self.app.extensions['test_inbox'][-1]['code'];data={'email':'two@example.com','code':code,'password':'different-password!'}
        self.assertEqual(self.post(guest,'auth/reset-password',data).status_code,400);self.assertEqual(self.post(guest,'auth/reset-password',{**data,'factor':codes[0]}).status_code,200)
    def test_sensitive_mfa_retry_with_new_code_keeps_original_idempotency(self):
        card=self.issue(self.b);secret,codes=self.mfa();key=uuid.uuid4().hex;data={'uid':card['uid'],'reason':'lost'}
        self.assertEqual(self.secure(self.b,'cards/replace',{**data,'factor':codes[0]},key).status_code,200)
        r=self.secure(self.b,'cards/replace',{**data,'factor':codes[1]},key);self.assertEqual(r.status_code,200,r.json);self.assertEqual(r.json['db']['cards'][0]['replacementCount'],1);self.assertEqual(self.b.get('/api/security/mfa').json['recoveryRemaining'],9)
    def test_preferences_calendar_and_notification_choices_are_scoped(self):
        card=self.issue(self.b);data={'language':'en','favoriteCurrency':'JPY','defaultCard':card['uid'],'hideAmounts':True,'notifyTransactions':False,'notifyReminders':False};self.assertEqual(self.post(self.b,'preferences',data).status_code,200);self.assertFalse(self.a.get('/api/preferences').json['hideAmounts']);self.assertTrue(self.b.get('/api/preferences').json['hideAmounts'])
        count=self.b.get('/api/notifications').json['total'];self.purchase(card,2);self.assertEqual(self.b.get('/api/notifications').json['total'],count);self.assertEqual(self.post(self.a,'preferences',{'defaultCard':card['uid']}).status_code,400)
        events=self.b.get('/api/calendar').json['events'];self.assertTrue(any(e['kind']=='renew' for e in events));r=self.b.get('/api/calendar.ics');self.assertEqual(r.status_code,200);self.assertIn(b'BEGIN:VCALENDAR',r.data);self.assertNotIn(card['cardNumber'].encode(),r.data);r.close()
    def test_feedback_owner_admin_reply_and_audit(self):
        r=self.post(self.b,'feedback',{'category':'bug','title':'Layout test','body':'Detailed test feedback','page':'billing'});self.assertEqual(r.status_code,201,r.json);fid=r.json['id'];self.assertEqual(self.a.get('/api/feedback').json['items'],[])
        data={'id':fid,'status':'working','reply':'We are checking this report','currentPassword':'strong-password!'};self.assertEqual(self.post(self.b,'admin/feedback',data).status_code,403);self.assertEqual(self.post(self.a,'admin/feedback',data).status_code,200)
        self.assertEqual(self.b.get('/api/feedback').json['items'][0]['status'],'working');self.assertEqual(self.a.get('/api/admin/operations').json['feedback'][0]['id'],fid)
        with sqlite3.connect(self.path) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM admin_access WHERE action='feedback_reply'").fetchone()[0],1)
    def test_ops_alert_dedup_and_maintenance_age(self):
        daily_backup(self.path,self.app.config['BACKUP_DIR'],14);self.app.extensions['run_maintenance']()
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT OR REPLACE INTO fx VALUES(1,?)',(json.dumps({'asOf':datetime.fromtimestamp(self.now,timezone.utc).isoformat()}),))
            for _ in range(3):db.execute("INSERT INTO mail_events(email,purpose,result,error_category,created) VALUES('test@example.com','login','failed','transport',?)",(self.now,))
        first=self.app.extensions['run_ops_checks'](heartbeat=False);self.assertFalse(first['checks']['mail']['ok']);self.assertTrue(first['checks']['backup']['ok']);sent=len(self.app.extensions.get('ops_outbox',[]));self.assertGreater(sent,0);self.app.extensions['run_ops_checks'](heartbeat=False);self.assertEqual(len(self.app.extensions['ops_outbox']),sent);self.now+=4*3600;later=self.app.extensions['run_ops_checks'](heartbeat=False,send=False);self.assertFalse(later['checks']['maintenance']['ok'])
    def test_health_releases_assets_and_private_endpoints(self):
        guest=self.app.test_client();self.assertEqual(guest.get('/api/health').json['version'],'6.0.0');self.assertEqual(guest.get('/api/releases').json[0]['version'],'6.0.0')
        for path in ['preferences','card-services','calendar','feedback','security/mfa','admin/operations']:self.assertEqual(guest.get('/api/'+path).status_code,401)
        for asset in ['growth.js','growth.css','admin-growth.js']:
            r=guest.get('/assets/'+asset);self.assertEqual(r.status_code,200);r.close()
