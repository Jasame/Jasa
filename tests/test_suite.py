import concurrent.futures
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3
import time
import unittest
import uuid
import test_app as fixtures
from domain import add_months
from suite import next_close,TZ

class SuiteTests(unittest.TestCase):
    setUpBase=fixtures.CloudTests.setUp
    tearDown=fixtures.CloudTests.tearDown
    post=fixtures.CloudTests.post
    register=fixtures.CloudTests.register
    command=fixtures.CloudTests.command
    state=fixtures.CloudTests.state
    issue=fixtures.CloudTests.issue
    login_device=fixtures.CloudTests.login_device
    def setUp(self):
        self.setUpBase();self.now=int(time.time());self.app.config['FEATURE_NOW']=lambda:self.now
        with sqlite3.connect(self.path) as db:db.execute("UPDATE users SET admin=1 WHERE email='one@example.com'")
        self.uid=self.a.get('/api/auth/me').json['user']['id'];self.other_uid=self.b.get('/api/auth/me').json['user']['id']
    def purchase(self,card,amount=100,category='everyday'):
        r=self.command(self.b,'pos/authorize',dict(uid=card['uid'],currency='USD',amount=amount,category=category,merchant='DEMO MERCHANT'));self.assertEqual(r.status_code,200,r.json)
    def close_cycle(self):
        with sqlite3.connect(self.path) as db:db.execute('UPDATE billing_profiles SET next_close=?,period_start=? WHERE user_id=?',(self.now+10,self.now-100,self.other_uid))
        self.now+=11
        response=self.b.get('/api/billing');self.assertEqual(response.status_code,200,response.json);return response.json
    def action(self,kind,extra=None,key=None,client=None):
        return self.post(client or self.a,'admin/actions',{'action':kind,'userId':self.other_uid,'reason':'Demo test adjustment','currentPassword':'strong-password!',**(extra or {})},**{'Idempotency-Key':key or uuid.uuid4().hex})

    def test_billed_unbilled_and_partial_payment_allocate_oldest_debt(self):
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=1000));card=self.issue(self.b);self.purchase(card,100,'travel')
        data=self.close_cycle();self.assertEqual(data['cards'][0]['billedCents'],10000);self.assertEqual(data['cards'][0]['unbilledCents'],0)
        self.purchase(card,50,'travel')
        self.assertEqual(self.command(self.b,'cards/repay',dict(uid=card['uid'],method='USD',amount=30)).status_code,200)
        data=self.b.get('/api/billing').json;c=data['cards'][0]
        self.assertEqual((c['billedCents'],c['unbilledCents'],c['debtCents']),(7000,5000,12000))
        self.assertEqual(data['statements'][0]['closingCents'],10000);self.assertEqual(data['statements'][0]['remainingCents'],7000)
        self.assertEqual(self.command(self.b,'cards/repay',dict(uid=card['uid'],method='USD',amount=121)).status_code,400)
        self.command(self.b,'cards/repay',dict(uid=card['uid'],method='USD',amount=120))
        self.assertEqual(self.b.get('/api/billing').json['cards'][0]['debtCents'],0)

    def test_statement_and_notification_rollover_are_idempotent(self):
        card=self.issue(self.b,'gold');data=self.close_cycle();count=len(data['statements'])
        for _ in range(3):self.app.extensions['run_maintenance']()
        self.assertEqual(len(self.b.get('/api/billing').json['statements']),count)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND kind='statement'",(self.other_uid,)).fetchone()[0],count)
        bill=data['statements'][0]
        response=self.post(self.b,'billing/settings',{'closeDay':15,'dueDays':14});self.assertEqual(response.status_code,200)
        updated=self.b.get('/api/billing').json
        self.assertEqual(updated['statements'][0]['dueAt'],bill['dueAt']);self.assertEqual(updated['statements'][0]['closingCents'],29500)
        self.assertEqual(updated['profile']['due_days'],14)

    def test_close_day_28_handles_non_leap_february_and_year_end(self):
        stamp=datetime(2027,1,29,12,tzinfo=TZ).timestamp()
        self.assertEqual(datetime.fromtimestamp(next_close(stamp,28),TZ),datetime(2027,3,1,tzinfo=TZ))
        stamp=datetime(2026,12,29,12,tzinfo=TZ).timestamp()
        self.assertEqual(datetime.fromtimestamp(next_close(stamp,28),TZ),datetime(2027,1,29,tzinfo=TZ))
        for data in ({'closeDay':29,'dueDays':20},{'closeDay':True,'dueDays':20},{'closeDay':20,'dueDays':3}):self.assertEqual(self.post(self.b,'billing/settings',data).status_code,400)

    def test_annual_benefits_preserve_usage_on_product_change_and_reset_next_period(self):
        card=self.issue(self.b,'aero')
        data=dict(uid=card['uid'],benefitId='companion',merchant='DEMO TRIP')
        self.assertEqual(self.command(self.b,'benefits/use',data).status_code,200)
        self.assertEqual(self.command(self.b,'benefits/use',data).status_code,409)
        self.command(self.b,'cards/product-change',dict(uid=card['uid'],cardId='gold'))
        self.command(self.b,'cards/product-change',dict(uid=card['uid'],cardId='aero'))
        self.assertEqual(self.command(self.b,'benefits/use',data).status_code,409)
        self.now=int(datetime.fromisoformat(add_months(card['openedAt'],12)).timestamp())+1
        self.assertEqual(self.command(self.b,'benefits/use',data).status_code,200)
        benefits=self.b.get('/api/benefits').json;self.assertEqual(len(benefits['usage']),2)
        self.command(self.b,'cards/security-freeze',dict(uid=card['uid']))
        self.assertEqual(self.command(self.b,'benefits/use',dict(data,benefitId='lounge')).status_code,423)

    def test_automatic_credits_are_allocated_and_analysis_separates_rewards(self):
        card=self.issue(self.b,'gold');self.purchase(card,100,'dining')
        billing=self.b.get('/api/billing').json
        self.assertEqual(billing['cards'][0]['debtCents'],36500)
        data=self.b.get('/api/analytics?year='+str(datetime.now(TZ).year)).json
        self.assertEqual(data['totals']['purchase_cents'],10000);self.assertEqual(data['totals']['credits_cents'],3000)
        self.assertEqual(data['totals']['reward_points'],500);self.assertEqual(data['totals']['welcome_points'],0);self.assertEqual(data['totals']['fees_cents'],29500)
        self.assertEqual(self.b.get('/api/analytics?merchant=NO_MATCH').json['matched'],0)
        self.assertEqual(self.b.get('/api/analytics?merchant=DEMO').json['totals']['purchase_cents'],10000)

    def test_notifications_are_private_and_read_operations_are_scoped(self):
        self.issue(self.b)
        data=self.b.get('/api/notifications').json;self.assertGreater(data['unread'],0);nid=data['items'][0]['id']
        self.assertEqual(self.post(self.a,'notifications/read',{'id':nid}).status_code,404)
        self.assertEqual(self.post(self.b,'notifications/read',{'id':nid}).status_code,200)
        self.assertEqual(self.b.get('/api/notifications?unread=1').json['total'],0)
        self.assertEqual(self.b.post('/api/notifications/read',json={'all':True}).status_code,403)

    def test_statement_pdf_and_annual_report_use_auth_and_owner_scope(self):
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=1000));card=self.issue(self.b,'gold');self.purchase(card,100,'travel')
        sid=self.close_cycle()['statements'][0]['id']
        self.assertEqual(self.a.get('/api/statements/'+sid+'/pdf').status_code,404)
        self.assertEqual(self.app.test_client().get('/api/statements/'+sid+'/pdf').status_code,401)
        for lang in ('zh','en'):
            response=self.b.get('/api/statements/'+sid+'/pdf?lang='+lang);self.assertEqual(response.status_code,200);self.assertTrue(response.data.startswith(b'%PDF'));self.assertEqual(response.headers['Cache-Control'],'no-store')
        response=self.b.get('/api/analytics/report.pdf?year='+str(datetime.now(TZ).year));self.assertEqual(response.status_code,200);self.assertGreater(len(response.data),3000)
        self.assertEqual(self.b.get('/api/analytics/report.pdf?year=invalid').status_code,400)

    def test_admin_adjustment_requires_role_password_reason_and_books_exactly_once(self):
        self.assertEqual(self.action('adjust-wallet',{'amount':'100'},client=self.b).status_code,403)
        self.assertEqual(self.action('adjust-wallet',{'amount':'100','currentPassword':'wrong'}).status_code,400)
        self.assertEqual(self.action('adjust-wallet',{'amount':'100','reason':'bad'}).status_code,400)
        key=uuid.uuid4().hex
        for _ in range(3):self.assertEqual(self.action('adjust-wallet',{'amount':'100'},key).status_code,200)
        self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],100)
        self.assertEqual(self.action('adjust-wallet',{'amount':'200'},key).status_code,409)
        self.assertEqual(self.action('adjust-wallet',{'amount':'-101'}).status_code,400)
        self.assertEqual(self.action('adjust-points',{'amount':'500'}).status_code,200)
        self.assertEqual(self.state(self.b)['jrPointsBalance'],500)
        self.assertEqual(len(self.state(self.b)['generalLedger']),2)
        rows=self.a.get('/api/admin/records?route=admin/adjust-wallet').json['items'];self.assertEqual(len(rows),1)
        detail=self.a.get('/api/admin/records/'+rows[0]['id']).json;self.assertEqual(detail['details']['adminAction']['actor'],self.uid)

    def test_admin_disable_revoke_enable_and_rules(self):
        self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=100))
        self.assertEqual(self.action('disable').status_code,200);self.assertEqual(self.b.get('/api/state').status_code,401)
        self.assertEqual(self.post(self.b,'auth/login',dict(email='two@example.com',password='strong-password!')).status_code,403)
        self.assertEqual(self.action('enable').status_code,200)
        client=self.login_device(email='two@example.com');self.assertEqual(client.get('/api/state').status_code,200);self.assertEqual(self.state(client)['treasuryWallets']['USD'],100)
        self.assertEqual(self.action('revoke').status_code,200);self.assertEqual(client.get('/api/state').status_code,401)
        self.assertEqual(self.action('disable',{'userId':self.uid}).status_code,409)
        self.assertEqual(self.action('settings',{'publicRegistration':False,'minIncome':9000}).status_code,200)
        self.assertFalse(self.a.get('/api/auth/me').json['publicRegistration'])
        self.assertEqual(self.a.get('/api/admin/system').json['settings']['min_income'],9000)

    def test_concurrent_admin_adjustments_with_one_key_post_once(self):
        key=uuid.uuid4().hex;cookie=self.a.get_cookie('jwb_session').value;csrf=self.csrf[id(self.a)]
        def run(_):
            client=self.app.test_client();client.set_cookie('jwb_session',cookie)
            return client.post('/api/admin/actions',json={'action':'adjust-wallet','userId':self.other_uid,'amount':'100','reason':'Concurrent demo adjustment','currentPassword':'strong-password!'},headers={'X-JWB-Client':'web','X-CSRF-Token':csrf,'Idempotency-Key':key}).status_code
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:self.assertEqual(list(pool.map(run,range(3))),[200]*3)
        self.assertEqual(self.state(self.b)['treasuryWallets']['USD'],100)

    def test_revoked_session_cannot_commit_an_inflight_financial_command(self):
        provider=self.app.config['FX_TEST_PROVIDER']
        def revoke_during_dependency():
            with sqlite3.connect(self.path) as db:
                db.execute('DELETE FROM sessions WHERE user_id=?',(self.other_uid,))
                db.execute('INSERT OR REPLACE INTO user_flags VALUES(?,?,?,?)',(self.other_uid,1,'In-flight test',self.now))
            return provider()
        self.app.config['FX_TEST_PROVIDER']=revoke_during_dependency
        self.assertEqual(self.command(self.b,'treasury/wire-in',dict(currency='USD',amount=100)).status_code,401)
        with sqlite3.connect(self.path) as db:value=json.loads(db.execute('SELECT state FROM accounts WHERE user_id=?',(self.other_uid,)).fetchone()[0])
        self.assertEqual(value['treasuryWallets']['USD'],0)

    def test_demo_scenarios_do_not_create_accounts_or_persist_financial_records(self):
        tables=('users','accounts','business_records','ledger_records','notifications','mail_events')
        with sqlite3.connect(self.path) as db:before={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in tables}
        guest=self.app.test_client()
        for scenario in ('travel','dining','first-card'):
            response=self.post(guest,'demo/scenario',{'scenario':scenario});self.assertEqual(response.status_code,200,response.json)
            self.assertFalse(response.json['persisted']);self.assertTrue(response.json['fixedRates']);self.assertEqual(response.json['steps'][-1]['cards'][0]['statementBalance'],0)
            self.assertNotIn('cardNumber',response.get_data(as_text=True));self.assertNotIn('cvv',response.get_data(as_text=True))
        with sqlite3.connect(self.path) as db:self.assertEqual(before,{t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in tables})
        self.assertEqual(guest.get('/api/billing').status_code,401)
        response=guest.get('/demo/');self.assertEqual(response.status_code,200);response.close()

    def test_account_reset_clears_current_billing_without_deleting_statements(self):
        card=self.issue(self.b,'gold');self.close_cycle();self.command(self.b,'core/reset',{'currentPassword':'strong-password!'})
        data=self.b.get('/api/billing').json;self.assertEqual(data['cards'],[]);self.assertEqual(len(data['statements']),1);self.assertEqual(data['statements'][0]['remainingCents'],0)
        self.assertEqual(self.b.get('/api/analytics?year='+str(datetime.now(TZ).year)).json['totals']['fees_cents'],29500)

if __name__=='__main__':unittest.main()
