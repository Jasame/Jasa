import sys,json,tempfile,time,sqlite3,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from domain import empty_state
from werkzeug.security import generate_password_hash
with tempfile.TemporaryDirectory() as folder:
    clock=[int(time.time())]
    app=create_app(dict(TESTING=True,SECRET_KEY='local-suite-fixture-'*4,DATABASE=folder+'/db.sqlite3',COOKIE_SECURE=False,MAIL_MODE='memory',PUBLIC_ORIGIN='http://localhost',FEATURE_NOW=lambda:clock[0],BACKUP_DIR=folder+'/backups',FX_TEST_PROVIDER=lambda:dict(ratesToUSD={'USD':1,'CNY':1/7,'HKD':1/7.8,'JPY':1/150,'GBP':1.25,'EUR':1.1},source='test reference',asOf='2026-10-18T00:00:00+00:00',fetchedAt=time.time(),mode='reference',stale=False)))
    uid='suite-owner-test'
    with sqlite3.connect(app.config['DATABASE']) as db:
        db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,'owner@example.com',generate_password_hash('local-test-password'),1,clock[0]))
        db.execute('INSERT INTO accounts VALUES(?,?,0)',(uid,json.dumps(empty_state())))
    client=app.test_client();headers={'X-JWB-Client':'web'}
    r=client.post('/api/auth/login',json=dict(email='owner@example.com',password='local-test-password'),headers=headers);headers['X-CSRF-Token']=r.json['csrf']
    def command(route,data):
        r=client.post('/api/v1/'+route,json=data,headers={**headers,'Idempotency-Key':uuid.uuid4().hex});assert r.status_code<400,r.json;return r.json
    command('treasury/wire-in',dict(currency='USD',amount=10000))
    card=command('underwriting/issue-card',dict(cardId='gold',income=50000,months=12,existing=0,holderName='TEST HOLDER'))['issuedCard']
    command('pos/authorize',dict(uid=card['uid'],currency='USD',amount=100,category='dining',merchant='<img src=x onerror="globalThis.pwned=1">'))
    with sqlite3.connect(app.config['DATABASE']) as db:db.execute('UPDATE billing_profiles SET next_close=?,period_start=? WHERE user_id=?',(clock[0]+10,clock[0]-100,uid))
    clock[0]+=11;client.get('/api/billing')
    data={key:client.get('/api/'+key).json for key in ('auth/me','state','catalog','experience','rates','billing','benefits','analytics','notifications','preferences','security/mfa','card-services','calendar','feedback','releases')}
    for route in ('summary','users','applications','records','ledger','mail','system','audit','operations'):data['admin/'+route]=client.get('/api/admin/'+route).json
    data['admin/users/'+uid]=client.get('/api/admin/users/'+uid).json
    for record in data['admin/records']['items']:data['admin/records/'+record['id']]=client.get('/api/admin/records/'+record['id']).json
    for scenario in ('travel','dining','first-card'):data['demo:'+scenario]=client.post('/api/demo/scenario',json={'scenario':scenario},headers=headers).json
    Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/jwb-suite-dom-data.json').write_text(json.dumps(data));print('Authorized suite, admin and isolated demo fixtures created')
