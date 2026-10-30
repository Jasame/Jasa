"""Billing, notifications, benefit periods and analysis for the simulation."""
import calendar
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import json
import re
import time
import uuid
from domain import PRODUCTS,CURRENCIES,add_months
from records import epoch,public_card,sanitize

TZ=timezone(timedelta(hours=8))
VOUCHERS={
 'everyday':[],
 'gold':[('hotel_privilege','酒店礼遇使用记录','Hotel privilege visit',None)],
 'aero':[('companion','同行伴侣演示券','Demo companion certificate',1),('lounge','休息室演示通行','Demo lounge visit',None)],
 'aspire':[('free_night','免房演示券','Demo free night',1),('diamond','钻石礼遇使用记录','Diamond privilege visit',None)],
 'platinum':[('lounge','休息室演示通行','Demo lounge visit',None),('fhr','FHR 礼遇使用记录','FHR privilege visit',None)],
 'centurion':[('concierge','礼宾服务演示','Demo concierge request',None),('lounge','休息室演示通行','Demo lounge visit',None)]}

def cents(value):return int((Decimal(str(value))*100).quantize(Decimal(1)))
def utc_iso(value):return datetime.fromtimestamp(value,timezone.utc).isoformat()
def clock(app):return int(app.config['FEATURE_NOW']()) if app.config.get('FEATURE_NOW') else int(time.time())
def next_close(now,day):
    date=datetime.fromtimestamp(now,TZ);end=date.replace(day=day,hour=0,minute=0,second=0,microsecond=0)+timedelta(days=1)
    if end.timestamp()<=now:
        y,m=divmod(date.year*12+date.month,12);end=datetime(y,m+1,day,tzinfo=TZ)+timedelta(days=1)
    return int(end.timestamp())

def init_suite(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS user_flags(user_id TEXT PRIMARY KEY REFERENCES users(id),disabled INTEGER DEFAULT 0,reason TEXT,updated INTEGER);
    CREATE TABLE IF NOT EXISTS billing_profiles(user_id TEXT PRIMARY KEY REFERENCES users(id),close_day INTEGER,due_days INTEGER,period_start INTEGER,next_close INTEGER);
    CREATE TABLE IF NOT EXISTS billing_events(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),card_uid TEXT,created INTEGER,kind TEXT,cents INTEGER,remaining INTEGER,description TEXT,record_id TEXT);
    CREATE INDEX IF NOT EXISTS bill_event_user ON billing_events(user_id,card_uid,created);
    CREATE TABLE IF NOT EXISTS statements(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),card_uid TEXT,close_at INTEGER,due_at INTEGER,data TEXT,UNIQUE(user_id,card_uid,close_at));
    CREATE INDEX IF NOT EXISTS statement_user ON statements(user_id,close_at DESC);
    CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),dedupe TEXT,created INTEGER,kind TEXT,title TEXT,body TEXT,is_read INTEGER DEFAULT 0,UNIQUE(user_id,dedupe));
    CREATE INDEX IF NOT EXISTS notification_user ON notifications(user_id,created DESC);
    CREATE TABLE IF NOT EXISTS spend_facts(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),card_uid TEXT,product TEXT,created INTEGER,merchant TEXT,category TEXT,purchase_cents INTEGER,credits_cents INTEGER,reward_points INTEGER,welcome_points INTEGER,fees_cents INTEGER);
    CREATE INDEX IF NOT EXISTS facts_user ON spend_facts(user_id,created,card_uid);
    CREATE TABLE IF NOT EXISTS benefit_usage(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),card_uid TEXT,product TEXT,benefit_id TEXT,period INTEGER,created INTEGER,note TEXT);
    CREATE INDEX IF NOT EXISTS benefits_user ON benefit_usage(user_id,created DESC);
    CREATE TABLE IF NOT EXISTS admin_commands(actor_id TEXT,key TEXT,hash TEXT,response TEXT,PRIMARY KEY(actor_id,key));
    ''')
    db.execute('BEGIN IMMEDIATE')
    if not db.execute("SELECT 1 FROM schema_migrations WHERE name='suite-v1'").fetchone():
        now=int(time.time())
        for row in db.execute('SELECT user_id,state FROM accounts').fetchall():ensure_profile(db,row['user_id'],json.loads(row['state']),now)
        for row in db.execute('SELECT * FROM business_records WHERE legacy=0 AND status<400').fetchall():
            fact_from_record(db,dict(row),json.loads(row['details']))
        db.execute('INSERT INTO schema_migrations VALUES(?,?)',('suite-v1',now))
    db.commit()

def notify(db,uid,dedupe,kind,title,body,now):
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='user_options'").fetchone():
        row=db.execute('SELECT data FROM user_options WHERE user_id=?',(uid,)).fetchone();pref=json.loads(row[0]) if row else {}
        if kind not in ('security','system') and not pref.get('notifyReminders' if kind in ('due','expiry') else 'notifyTransactions',True):return
    db.execute('INSERT OR IGNORE INTO notifications VALUES(?,?,?,?,?,?,?,0)',('NT-'+uuid.uuid4().hex,uid,dedupe,now,kind,title,body))

def ensure_profile(db,uid,state,now):
    if db.execute('SELECT 1 FROM billing_profiles WHERE user_id=?',(uid,)).fetchone():return
    db.execute('INSERT INTO billing_profiles VALUES(?,?,?,?,?)',(uid,20,20,now,next_close(now,20)))
    for card in state['cards']:
        debt=cents(card['statementBalance'])
        if debt:db.execute('INSERT OR IGNORE INTO billing_events VALUES(?,?,?,?,?,?,?,?,?)',('OPEN-'+card['uid'],uid,card['uid'],now,'opening',debt,debt,'升级期初欠款 / Opening debt at upgrade',None))

def refresh_benefit_period(card,now):
    opened=datetime.fromisoformat(card['openedAt']);today=datetime.fromtimestamp(now,timezone.utc)
    period=max(0,today.year-opened.year)
    if epoch(add_months(card['openedAt'],period*12))>now:period=max(0,period-1)
    old=card.get('benefitPeriod')
    if old is not None:period=max(period,old)
    if old is not None and old!=period or old is None and period>0:
        card['remainingCreditPool']=PRODUCTS[card['cardId']]['fixedCredits'];card['benefitPools']={};card['benefitUses']={}
    card['benefitPeriod']=period;card.setdefault('benefitUses',{})
    return epoch(add_months(card['openedAt'],(period+1)*12))

def allocate_credit(db,uid,card_uid,amount):
    left=amount
    for row in db.execute('SELECT id,remaining FROM billing_events WHERE user_id=? AND card_uid=? AND remaining>0 ORDER BY created,rowid',(uid,card_uid)).fetchall():
        used=min(left,row['remaining']);db.execute('UPDATE billing_events SET remaining=remaining-? WHERE id=?',(used,row['id']));left-=used
        if not left:break
    if left:raise RuntimeError('Billing credit exceeds recorded outstanding debt')

def capture_operation(db,uid,rid,route,data,result,before,after,status,now):
    if status>=400:
        if route=='underwriting/issue-card':notify(db,uid,rid,'application','申请未通过 / Application declined',result['message'],now)
        return
    ensure_profile(db,uid,before,now)
    old={e['entryId'] for e in before['generalLedger']}
    entries=[e for e in reversed(after['generalLedger']) if e['entryId'] not in old]
    for entry in entries:
        credit=re.fullmatch(r'2010 · Card Payable \(([^)]+)\)',entry['creditAccount']);debit=re.fullmatch(r'2010 · Card Payable \(([^)]+)\)',entry['debitAccount'])
        if not credit and not debit:continue
        card_uid=(credit or debit)[1];amount=cents(entry['amountUSD'])
        kind='charge' if credit else 'payment' if route=='cards/repay' else 'credit'
        if debit:allocate_credit(db,uid,card_uid,amount)
        db.execute('INSERT INTO billing_events VALUES(?,?,?,?,?,?,?,?,?)',(entry['entryId'],uid,card_uid,now,kind,amount,amount if credit else 0,entry['memo'],rid))
    if route=='core/reset':
        for card in before['cards']:
            amount=db.execute('SELECT COALESCE(SUM(remaining),0) FROM billing_events WHERE user_id=? AND card_uid=?',(uid,card['uid'])).fetchone()[0]
            if amount:
                allocate_credit(db,uid,card['uid'],amount)
                db.execute('INSERT INTO billing_events VALUES(?,?,?,?,?,?,?,?,?)',('RESET-'+uuid.uuid4().hex,uid,card['uid'],now,'credit',amount,0,'模拟账户重置 / Simulation reset',rid))
        profile=db.execute('SELECT close_day FROM billing_profiles WHERE user_id=?',(uid,)).fetchone()
        db.execute('UPDATE billing_profiles SET period_start=?,next_close=? WHERE user_id=?',(now,next_close(now,profile['close_day']),uid))
    if route=='benefits/use':
        card=next(c for c in after['cards'] if c['uid']==data['uid'])
        db.execute('INSERT INTO benefit_usage VALUES(?,?,?,?,?,?,?,?)',('BU-'+uuid.uuid4().hex,uid,card['uid'],card['cardId'],data['benefitId'],card['benefitPeriod'],now,str(data.get('merchant',''))[:120]))
    record=db.execute('SELECT * FROM business_records WHERE id=?',(rid,)).fetchone()
    if record:fact_from_record(db,dict(record),json.loads(record['details']))
    titles={'underwriting/issue-card':'卡片已签发 / Card issued','pos/authorize':'消费已入账 / Purchase posted','cards/repay':'还款成功 / Repayment posted','treasury/wire-in':'模拟资金到账 / Demo funding received','treasury/fx-swap':'换汇完成 / FX completed','benefits/use':'权益已使用 / Benefit used','admin/adjust-wallet':'管理员调整模拟余额 / Admin adjusted demo funds','admin/adjust-points':'管理员调整模拟积分 / Admin adjusted rewards'}
    if route in titles:notify(db,uid,rid,route,titles[route],result['message'],now)
    if any(e['creditAccount']=='4030 · Welcome Bonus Income' for e in entries):notify(db,uid,rid+':welcome','reward','开卡奖励已达标 / Welcome offer earned','积分已计入你的模拟账户 / Rewards have been added to your demo account',now)

def fact_from_record(db,row,details):
    route=row['route'];inputs=details.get('inputs',{});ledger_ids=details.get('ledgerIds',[])
    if route not in ('pos/authorize','underwriting/issue-card','cards/product-change'):return
    entries=[]
    for entry_id in ledger_ids:
        record=db.execute('SELECT details FROM ledger_records WHERE user_id=? AND entry_id=?',(row['user_id'],entry_id)).fetchone()
        if record:entries.append(json.loads(record['details']))
    purchase=sum(cents(e['amountUSD']) for e in entries if e['debitAccount']=='5010 · Purchase Expense')
    fees=sum(cents(e['amountUSD']) for e in entries if e['debitAccount']=='5020 · Annual Fee Expense')
    credits=sum(cents(e['amountUSD']) for e in entries if e['creditAccount']=='4010 · Statement Credit Income')
    rewards=sum(cents(e['amountUSD']) for e in entries if e['creditAccount']=='4030 · Rewards Income')
    welcome=sum(cents(e['amountUSD']) for e in entries if e['creditAccount']=='4030 · Welcome Bonus Income')
    db.execute('INSERT OR IGNORE INTO spend_facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(row['id'],row['user_id'],row['card_uid'],row['product'],row['created'],str(inputs.get('merchant','')),str(inputs.get('category','fee')),purchase,credits,rewards,welcome,fees))

def roll_bills(db,uid,state,now):
    ensure_profile(db,uid,state,now)
    profile=dict(db.execute('SELECT * FROM billing_profiles WHERE user_id=?',(uid,)).fetchone())
    for _ in range(1200):
        close=profile['next_close']
        if close>now:break
        for card in state['cards']:
            if epoch(card['openedAt'])>=close or card.get('closedAt',now+1)<close:continue
            events=db.execute('SELECT * FROM billing_events WHERE user_id=? AND card_uid=? AND created<? ORDER BY created,rowid',(uid,card['uid'],close)).fetchall()
            previous=[e for e in events if e['created']<profile['period_start']];current=[e for e in events if e['created']>=profile['period_start']]
            total=lambda rows:sum(e['cents']*(1 if e['kind'] in ('charge','opening') else -1) for e in rows)
            payload={'card':public_card(card),'periodStart':profile['period_start'],'closeAt':close,'dueAt':close+profile['due_days']*86400-1,'openingCents':total(previous),'chargesCents':sum(e['cents'] for e in current if e['kind'] in ('charge','opening')),'paymentsCents':sum(e['cents'] for e in current if e['kind']=='payment'),'creditsCents':sum(e['cents'] for e in current if e['kind']=='credit'),'closingCents':max(0,total(events)),'items':[{k:e[k] for k in ('id','created','kind','cents','description')} for e in current]}
            sid='ST-'+uuid.uuid4().hex
            db.execute('INSERT OR IGNORE INTO statements VALUES(?,?,?,?,?,?)',(sid,uid,card['uid'],close,payload['dueAt'],json.dumps(payload)))
            notify(db,uid,'statement:'+card['uid']+':'+str(close),'statement','月度账单已生成 / Monthly statement ready',f'{PRODUCTS[card["cardId"]]["name"]} · USD {payload["closingCents"]/100:.2f}',now)
        profile['period_start']=close;profile['next_close']=next_close(close+1,profile['close_day'])
    db.execute('UPDATE billing_profiles SET period_start=?,next_close=? WHERE user_id=?',(profile['period_start'],profile['next_close'],uid))
    for row in db.execute('SELECT id,card_uid,close_at,due_at FROM statements WHERE user_id=? AND due_at BETWEEN ? AND ?',(uid,now-86400,now+3*86400)).fetchall():
        remaining=db.execute('SELECT COALESCE(SUM(remaining),0) FROM billing_events WHERE user_id=? AND card_uid=? AND created<?',(uid,row['card_uid'],row['close_at'])).fetchone()[0]
        if remaining:notify(db,uid,'due:'+row['id'],'due','账单还款提醒 / Statement payment reminder',f'USD {remaining/100:.2f} · '+datetime.fromtimestamp(row['due_at'],TZ).strftime('%Y-%m-%d'),now)
    for card in state['cards']:
        if card.get('status')=='CLOSED':continue
        expiry=refresh_benefit_period(card,now)
        if 0<expiry-now<=14*86400:notify(db,uid,'benefit:'+card['uid']+':'+str(expiry),'expiry','权益周期即将到期 / Benefit period ending',PRODUCTS[card['cardId']]['name']+' · '+datetime.fromtimestamp(expiry,TZ).strftime('%Y-%m-%d'),now)
        welcome_end=epoch(card['welcomeExpiresAt'])
        if not card['welcomeUnlocked'] and 0<welcome_end-now<=7*86400:
            notify(db,uid,'welcome-ending:'+card['uid']+':'+str(welcome_end),'expiry','开卡奖励期限即将结束 / Welcome offer window ending',PRODUCTS[card['welcomeProductId']]['name']+' · '+datetime.fromtimestamp(welcome_end,TZ).strftime('%Y-%m-%d'),now)

def statement_view(db,row):
    result=json.loads(row['data']);result.update(id=row['id'])
    result['remainingCents']=db.execute('SELECT COALESCE(SUM(remaining),0) FROM billing_events WHERE user_id=? AND card_uid=? AND created<?',(row['user_id'],row['card_uid'],row['close_at'])).fetchone()[0]
    return result

def billing_view(db,uid,state):
    profile=dict(db.execute('SELECT * FROM billing_profiles WHERE user_id=?',(uid,)).fetchone())
    rows=db.execute('SELECT * FROM statements WHERE user_id=? ORDER BY close_at DESC,id DESC LIMIT 120',(uid,)).fetchall()
    bills=[statement_view(db,row) for row in rows];cards=[]
    for card in state['cards']:
        latest=db.execute('SELECT close_at FROM statements WHERE user_id=? AND card_uid=? ORDER BY close_at DESC LIMIT 1',(uid,card['uid'])).fetchone()
        billed=db.execute('SELECT COALESCE(SUM(remaining),0) FROM billing_events WHERE user_id=? AND card_uid=? AND created<?',(uid,card['uid'],latest['close_at'] if latest else 0)).fetchone()[0]
        debt=cents(card['statementBalance']);cards.append({'uid':card['uid'],'cardId':card['cardId'],'last4':card['cardNumber'][-4:],'billedCents':billed,'unbilledCents':debt-billed,'debtCents':debt})
    return {'profile':profile,'cards':cards,'statements':bills}

def analytics(db,uid,start,end,card_uid='',category='',merchant=''):
    clauses=['user_id=?','created>=?','created<?'];args=[uid,start,end]
    for column,value in [('card_uid',card_uid),('category',category)]:
        if value:clauses.append(column+'=?');args.append(value)
    if merchant:clauses.append("merchant LIKE ? ESCAPE '\\'");args.append('%'+merchant.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%')
    rows=[dict(row) for row in db.execute('SELECT * FROM spend_facts WHERE '+' AND '.join(clauses)+' ORDER BY created DESC,rowid DESC',args)]
    totals={key:sum(r[key] for r in rows) for key in ('purchase_cents','credits_cents','reward_points','welcome_points','fees_cents')}
    groups={key:{} for key in ('category','merchant','product')};monthly={}
    for r in rows:
        for key in groups:
            label=r[key] or '—';groups[key][label]=groups[key].get(label,0)+r['purchase_cents']
        month=datetime.fromtimestamp(r['created'],TZ).strftime('%Y-%m');monthly[month]=monthly.get(month,0)+r['purchase_cents']
    since=db.execute("SELECT created FROM schema_migrations WHERE name='admin-history-v1'").fetchone()[0]
    return {'totals':totals,'groups':groups,'monthly':monthly,'items':rows[:200],'matched':len(rows),'trackedSince':since,'start':start,'end':end}
