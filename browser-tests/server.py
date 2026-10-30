"""Loopback-only browser test server. Temporary DB, synthetic users, no real SMTP/FX."""
import sys,tempfile,time,json,uuid,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flask import request,jsonify
from werkzeug.security import generate_password_hash
from app import create_app
from domain import empty_state
from growth_security import totp_code

folder=tempfile.TemporaryDirectory(prefix='jwb-browser-');now=int(time.time())
app=create_app(dict(TESTING=True,SECRET_KEY='JWB-browser-only-secret-'*3,DATABASE=folder.name+'/browser.sqlite3',COOKIE_SECURE=False,MAIL_MODE='memory',PUBLIC_ORIGIN='http://127.0.0.1:8896',BASE_PATH='/bank',BACKUP_DIR=folder.name+'/backups',FEATURE_NOW=lambda:now,FX_TEST_PROVIDER=lambda:dict(ratesToUSD={'USD':1,'CNY':1/7,'HKD':1/7.8,'JPY':1/150,'GBP':1.25,'EUR':1.1},source='Browser fixture',asOf='2026-10-18T00:00:00+00:00',fetchedAt=now,mode='reference',stale=False)))
@app.post('/api/test-fixture')
def fixture():
    if request.remote_addr!='127.0.0.1':return '',403
    uid=uuid.uuid4().hex;email=uid+'@example.test';password='browser-test-password';data=request.get_json() or {}
    with sqlite3.connect(app.config['DATABASE']) as db:
        # Each scenario starts with a fresh loopback login budget in this temporary test DB.
        db.execute("DELETE FROM limits WHERE key='login-ip:127.0.0.1'")
        db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,email,generate_password_hash(password),int(bool(data.get('admin'))),now));db.execute('INSERT INTO accounts VALUES(?,?,0)',(uid,json.dumps(empty_state())))
    client=app.test_client();h={'X-JWB-Client':'web'};r=client.post('/bank/api/auth/login',json={'email':email,'password':password},headers=h);h['X-CSRF-Token']=r.json['csrf']
    def command(route,body):
        r=client.post('/bank/api/v1/'+route,json=body,headers={**h,'Idempotency-Key':uuid.uuid4().hex});assert r.status_code<400,r.json;return r.json
    command('treasury/wire-in',{'currency':'USD','amount':10000});c=command('underwriting/issue-card',{'cardId':'gold','holderName':'BROWSER VISITOR','income':50000,'existing':0,'months':12})['issuedCard'];command('pos/authorize',{'uid':c['uid'],'merchant':'Browser demo','category':'dining','currency':'USD','amount':100})
    with sqlite3.connect(app.config['DATABASE']) as db:
        value=json.loads(db.execute('SELECT state FROM accounts WHERE user_id=?',(uid,)).fetchone()[0]);value['cards'][0]['openedAt']='2026-01-01T00:00:00+00:00';db.execute('UPDATE accounts SET state=? WHERE user_id=?',(json.dumps(value),uid));db.execute('UPDATE billing_events SET created=? WHERE user_id=?',(now-10,uid));db.execute('UPDATE billing_profiles SET period_start=?,next_close=? WHERE user_id=?',(now-20,now-1,uid))
    client.get('/bank/api/billing')
    return jsonify(testOnly=True,email=email,password=password,now=now,uid=uid)

if __name__=='__main__':
    try:app.run(host='127.0.0.1',port=8896,threaded=True,use_reloader=False)
    finally:folder.cleanup()
