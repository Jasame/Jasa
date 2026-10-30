"""Private administrative history. Never store request bodies or card credentials."""
import hashlib
import json
import math
import re
import time
import uuid
from datetime import datetime

RULE_VERSION='JWB-SIM-2026.10-v1'
INPUT_FIELDS=('cardId','holderName','income','existing','months','currency','amount','merchant','category','method','uid','fromUid','toUid','benefitId','reason','recordId')
CARD_FIELDS=('uid','cardId','holderName','expDate','creditLimit','initialCreditLimit','statementBalance','annualFeePaid','spendProgress','welcomeUnlocked','remainingCreditPool','status','openedAt','cliApplied','renewAt','expiresAt','closedAt','replacementCount')

def safe_text(value):
    value=str(value)
    value=re.sub(r'(?<!\d)(?:\d{4}[- ]?){3}(\d{4})(?!\d)',r'•••• •••• •••• \1',value)
    return value

def sanitize(value):
    if isinstance(value,float) and not math.isfinite(value):return str(value)
    if isinstance(value,dict): return {k:sanitize(v) for k,v in value.items() if k not in ('cvv','password','currentPassword','code','digest','token','csrf','SMTP_PASSWORD','APP_SECRET','cardNumber','factor','recoveryCodes','mfaCode','secret','challenge')}
    if isinstance(value,list): return [sanitize(v) for v in value]
    if isinstance(value,str): return safe_text(value)
    return value

def public_card(card):
    return {**sanitize({k:card.get(k) for k in CARD_FIELDS}), 'last4':str(card.get('cardNumber','')).replace('-','')[-4:]}

def init_records(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS schema_migrations(name TEXT PRIMARY KEY,created INTEGER);
    CREATE TABLE IF NOT EXISTS business_records(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),command_key TEXT,route TEXT,status INTEGER,created INTEGER,product TEXT,card_uid TEXT,summary TEXT,details TEXT,legacy INTEGER DEFAULT 0,UNIQUE(user_id,command_key));
    CREATE INDEX IF NOT EXISTS business_time ON business_records(created DESC,id);
    CREATE INDEX IF NOT EXISTS business_user ON business_records(user_id,created DESC);
    CREATE INDEX IF NOT EXISTS business_route ON business_records(route,status,created DESC);
    CREATE TABLE IF NOT EXISTS ledger_records(user_id TEXT REFERENCES users(id),entry_id TEXT,record_id TEXT,created INTEGER,details TEXT,legacy INTEGER DEFAULT 0,PRIMARY KEY(user_id,entry_id));
    CREATE INDEX IF NOT EXISTS ledger_user_time ON ledger_records(user_id,created DESC);
    CREATE INDEX IF NOT EXISTS ledger_time ON ledger_records(created DESC);
    CREATE TABLE IF NOT EXISTS mail_events(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT,purpose TEXT,result TEXT,error_category TEXT,created INTEGER);
    CREATE INDEX IF NOT EXISTS mail_time ON mail_events(created DESC);
    CREATE TABLE IF NOT EXISTS admin_access(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT REFERENCES users(id),action TEXT,target TEXT,filters TEXT,created INTEGER);
    CREATE INDEX IF NOT EXISTS admin_time ON admin_access(created DESC);
    CREATE INDEX IF NOT EXISTS security_user_time ON security_events(user_id,created DESC);
    CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id,expires);
    CREATE INDEX IF NOT EXISTS audit_user_time ON audit(user_id,created DESC);
    ''')
    # Serialize migration across Gunicorn workers. No financial data is modified.
    db.execute('BEGIN IMMEDIATE')
    if not db.execute("SELECT 1 FROM schema_migrations WHERE name='admin-history-v1'").fetchone():
        for row in db.execute('SELECT user_id,state FROM accounts').fetchall():
            uid=row['user_id'];state=json.loads(row['state'])
            for entry in state.get('generalLedger',[]): store_ledger(db,uid,entry,None,True)
            for entry in state.get('posFeed',[]):
                rid='LEG-'+hashlib.sha256((uid+str(entry.get('txHash'))).encode()).hexdigest()[:24]
                db.execute('INSERT OR IGNORE INTO business_records VALUES(?,?,?,?,?,?,?,?,?,?,1)',(rid,uid,None,'legacy/activity',200,epoch(entry.get('time')),'','',safe_text(entry.get('desc','')),json.dumps(sanitize({'activity':entry,'note':'legacy_activity_only'}))))
        for row in db.execute('SELECT user_id,key,response,status FROM commands').fetchall():
            result=json.loads(row['response']);card=result.get('issuedCard')
            if not card:continue
            rid='LEG-APP-'+hashlib.sha256((row['user_id']+row['key']).encode()).hexdigest()[:20]
            details={'card':public_card(card),'assessment':sanitize(result.get('assessment',{})),'note':'legacy_inputs_not_recorded','ruleVersion':'legacy-unrecorded'}
            db.execute('INSERT OR IGNORE INTO business_records VALUES(?,?,?,?,?,?,?,?,?,?,1)',(rid,row['user_id'],row['key'],'underwriting/issue-card',row['status'],epoch(card.get('openedAt')),card.get('cardId',''),card.get('uid',''),safe_text(result.get('message','')),json.dumps(details)))
        for row in db.execute("SELECT id,user_id,event,created FROM audit WHERE event LIKE 'underwriting/issue-card:%'").fetchall():
            try:status=int(row['event'].rsplit(':',1)[1])
            except ValueError:continue
            if status<400:continue
            details={'note':'legacy_inputs_not_recorded','ruleVersion':'legacy-unrecorded'}
            db.execute('INSERT OR IGNORE INTO business_records VALUES(?,?,?,?,?,?,?,?,?,?,1)',('LEG-APP-FAIL-'+str(row['id']),row['user_id'],None,'underwriting/issue-card',status,row['created'],'','','旧版申请记录：原始资料与审批摘要未记录 / Legacy application; inputs and decision summary unavailable',json.dumps(details)))
        db.execute('INSERT INTO schema_migrations VALUES(?,?)',('admin-history-v1',int(time.time())))
    db.commit()

def epoch(value):
    try:return int(datetime.fromisoformat(value.replace('Z','+00:00')).timestamp())
    except (ValueError,AttributeError,TypeError):return 0

def store_ledger(db,uid,entry,record_id,legacy=False):
    db.execute('INSERT OR IGNORE INTO ledger_records VALUES(?,?,?,?,?,?)',(uid,entry['entryId'],record_id,epoch(entry.get('time')),json.dumps(sanitize(entry)),int(legacy)))

def record_command(db,uid,key,route,data,result,status,before,after,rules):
    rid='OP-'+uuid.uuid4().hex
    inputs={k:(v[:300] if isinstance(v,str) else v) for k in INPUT_FIELDS if (v:=data.get(k)) is not None}
    card_uid=str(data.get('uid') or result.get('issuedCard',{}).get('uid') or '')
    card=next((c for c in after['cards'] if c['uid']==card_uid),{})
    details={'inputs':inputs,'message':result.get('message'),'walletDelta':{c:round(after['treasuryWallets'].get(c,0)-before['treasuryWallets'].get(c,0),2) for c in after['treasuryWallets']},'pointsDelta':after['jrPointsBalance']-before['jrPointsBalance']}
    old_cards={c['uid']:c for c in before['cards']}
    details['cards']=[{'before':public_card(old_cards[c['uid']]) if c['uid'] in old_cards else None,'after':public_card(c)} for c in after['cards'] if c!=old_cards.get(c['uid'])]
    if route=='core/reset':details['removedCards']=[public_card(c) for c in before['cards']]
    if route=='underwriting/issue-card':details.update(assessment=result.get('assessment'),ruleVersion=RULE_VERSION,rules={'min_income':rules.get('min_income',5000),'assetThresholdUSD':2500})
    if data.get('_quote'):details['quote']={k:data['_quote'].get(k) for k in ('from','to','amount','received','rate','source','asOf')}
    if result.get('adminAction'):details['adminAction']=result['adminAction']
    old_entries={e['entryId'] for e in before['generalLedger']}
    entries=[e for e in after['generalLedger'] if e['entryId'] not in old_entries]
    details['ledgerIds']=[e['entryId'] for e in entries]
    db.execute('INSERT INTO business_records VALUES(?,?,?,?,?,?,?,?,?,?,0)',(rid,uid,key,route,status,int(time.time()),str(data.get('cardId') or card.get('cardId','')),card_uid,safe_text(result.get('message','')),json.dumps(sanitize(details))))
    for entry in entries:store_ledger(db,uid,entry,rid)
    return rid

def log_mail(db,email,purpose,result,error=''):
    db.execute('INSERT INTO mail_events(email,purpose,result,error_category,created) VALUES(?,?,?,?,?)',(email,purpose.split(':',1)[0],result,error,int(time.time())))
