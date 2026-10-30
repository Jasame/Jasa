"""Long-lived simulation records: refunds, lifecycle, preferences and feedback."""
import calendar
import json
import secrets
import time
import uuid
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_UP
from domain import DomainError,PRODUCTS,CURRENCIES,card_for,money,quantize,set_money,ledger,feed,pan,add_months
from records import epoch,record_command
from suite import cents,capture_operation,notify,clock

VERSION='6.0.1'
DEFAULT_PREFS={'language':'zh','favoriteCurrency':'USD','defaultCard':'','hideAmounts':False,'notifyTransactions':True,'notifyReminders':True}

def init_growth(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS user_options(user_id TEXT PRIMARY KEY REFERENCES users(id),data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS refund_totals(record_id TEXT PRIMARY KEY REFERENCES business_records(id),cents INTEGER NOT NULL DEFAULT 0,credits INTEGER NOT NULL DEFAULT 0,points INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS feedback(id TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),created INTEGER,updated INTEGER,category TEXT,title TEXT,body TEXT,page TEXT,version TEXT,status TEXT,reply TEXT);
    CREATE INDEX IF NOT EXISTS feedback_user ON feedback(user_id,created DESC);
    CREATE TABLE IF NOT EXISTS task_heartbeats(name TEXT PRIMARY KEY,completed INTEGER,ok INTEGER,detail TEXT);
    CREATE TABLE IF NOT EXISTS ops_checks(name TEXT PRIMARY KEY,checked INTEGER,ok INTEGER,detail TEXT,last_success INTEGER);
    CREATE TABLE IF NOT EXISTS ops_alerts(name TEXT PRIMARY KEY,active INTEGER,first_seen INTEGER,last_seen INTEGER,last_sent INTEGER,detail TEXT);
    CREATE TABLE IF NOT EXISTS http_failures(created INTEGER);
    CREATE INDEX IF NOT EXISTS failures_time ON http_failures(created);
    ''')

def preferences(db,uid):
    row=db.execute('SELECT data FROM user_options WHERE user_id=?',(uid,)).fetchone()
    return {**DEFAULT_PREFS,**(json.loads(row['data']) if row else {})}

def lifecycle_defaults(card,now):
    if 'renewAt' not in card:
        period=max(1,datetime.fromtimestamp(now,timezone.utc).year-datetime.fromisoformat(card['openedAt']).year)
        while epoch(add_months(card['openedAt'],12*period))<=now:period+=1
        card['renewAt']=epoch(add_months(card['openedAt'],12*period))
        card['expiresAt']=epoch(add_months(card['openedAt'],60));card['annualFeePeriodPaid']=card.get('annualFeePaid',PRODUCTS[card['cardId']]['annualFee'])
    card.setdefault('replacementCount',0)

def maintain_lifecycle(db,uid,state,now):
    for card in state['cards']:
        lifecycle_defaults(card,now)
        if card['status']=='CLOSED':continue
        if now>=card['expiresAt'] and card['status'] in ('ACTIVE','FROZEN'):
            card['status']='EXPIRED';notify(db,uid,'expired:'+card['uid']+':'+str(card['expiresAt']),'lifecycle','卡片已到期 / Card expired','请换卡后继续消费；原账单仍可还款 / Replace the card to spend again; bills remain payable',now)
        for _ in range(100):
            due=card['renewAt']
            if due>now:break
            # Post at the anniversary, before rolling monthly periods, for deterministic billing.
            before=json.loads(json.dumps(state));fee=Decimal(str(PRODUCTS[card['cardId']]['annualFee']))
            if fee:
                set_money(card,'statementBalance',Decimal(str(card['statementBalance']))+fee)
                ledger(state,'5020 · Annual Fee Expense',f'2010 · Card Payable ({card["uid"]})',fee,'Annual demo renewal fee')
                feed(state,'年度模拟年费 / Annual renewal fee · '+PRODUCTS[card['cardId']]['name'],f'+${fee:.2f}','','fee')
            card['annualFeePaid']=float(fee);card['annualFeePeriodPaid']=float(fee)
            card['renewAt']=epoch(add_months(datetime.fromtimestamp(due,timezone.utc).isoformat(),12))
            result={'message':'年度模拟年费已处理 / Annual renewal processed'}
            rid=record_command(db,uid,None,'cards/annual-renewal',{'uid':card['uid']},result,200,before,state,{})
            capture_operation(db,uid,rid,'cards/annual-renewal',{},result,before,state,200,due)
            db.execute('UPDATE business_records SET created=? WHERE id=?',(due,rid))
            db.execute('INSERT OR IGNORE INTO spend_facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(rid,uid,card['uid'],card['cardId'],due,'Annual renewal','fee',0,0,0,0,cents(fee)))
            notify(db,uid,rid,'lifecycle','年度续费已处理 / Annual renewal processed',f'{PRODUCTS[card["cardId"]]["name"]} · USD {fee:.2f}',now)
        if 0<card['renewAt']-now<=30*86400:
            notify(db,uid,'renew:'+card['uid']+':'+str(card['renewAt']),'expiry','年费周年日临近 / Annual renewal approaching',f'{PRODUCTS[card["cardId"]]["name"]} · USD {PRODUCTS[card["cardId"]]["annualFee"]:.2f}',now)
        if 0<card['expiresAt']-now<=60*86400:
            notify(db,uid,'card-expiry:'+card['uid']+':'+str(card['expiresAt']),'expiry','卡片即将到期 / Card nearing expiry','可在持卡服务中换卡 / Replacement is available in card services',now)

def proportional(total,part,whole):return int((Decimal(total)*part/whole).quantize(Decimal(1),rounding=ROUND_HALF_UP))

def execute_extended(db,uid,state,route,data,now):
    card=card_for(state,data.get('uid'));lifecycle_defaults(card,now)
    if route=='pos/refund':
        row=db.execute('SELECT f.*,r.route,r.status FROM spend_facts f JOIN business_records r ON r.id=f.id WHERE f.id=? AND f.user_id=? AND f.card_uid=?',(data.get('recordId'),uid,card['uid'])).fetchone()
        if not row or row['route']!='pos/authorize' or row['status']>=400 or row['purchase_cents']<=0:raise DomainError('原消费不存在或资料不足 / Original purchase unavailable',404)
        previous=db.execute('SELECT * FROM refund_totals WHERE record_id=?',(row['id'],)).fetchone()
        old=dict(previous) if previous else {'cents':0,'credits':0,'points':0}
        amount=cents(money(data.get('amount')));total=old['cents']+amount
        if total>row['purchase_cents']:raise DomainError('退款超过原消费剩余金额 / Refund exceeds remaining purchase',409)
        note=str(data.get('reason','')).strip()
        if not 6<=len(note)<=200:raise DomainError('退款原因须为 6–200 字 / Refund reason must be 6–200 characters')
        credit_total=proportional(row['credits_cents'],total,row['purchase_cents']);point_total=proportional(row['reward_points'],total,row['purchase_cents'])
        credit=credit_total-old['credits'];points=point_total-old['points'];welcome=0
        set_money(card,'spendProgress',max(Decimal(0),Decimal(str(card['spendProgress']))-Decimal(amount)/100))
        if card['welcomeUnlocked'] and card['spendProgress']<PRODUCTS[card['welcomeProductId']]['welcomeSpendReq']:
            card['welcomeUnlocked']=False;welcome=PRODUCTS[card['welcomeProductId']]['welcomeJR']
        if credit:
            set_money(card,'statementBalance',Decimal(str(card['statementBalance']))+Decimal(credit)/100)
            ledger(state,'4010 · Statement Credit Income',f'2010 · Card Payable ({card["uid"]})',Decimal(credit)/100,'Refund: reverse original statement credit')
            # Restore only the original product's current anniversary allowance.
            origin=db.execute('SELECT created FROM business_records WHERE id=?',(row['id'],)).fetchone()[0]
            period_start=epoch(add_months(card['openedAt'],card.get('benefitPeriod',0)*12))
            if card['status']!='CLOSED' and origin>=period_start:
                if card['cardId']==row['product']:set_money(card,'remainingCreditPool',min(Decimal(str(PRODUCTS[card['cardId']]['fixedCredits'])),Decimal(str(card['remainingCreditPool']))+Decimal(credit)/100))
                elif row['product'] in card.get('benefitPools',{}):set_money(card['benefitPools'],row['product'],min(Decimal(str(PRODUCTS[row['product']]['fixedCredits'])),Decimal(str(card['benefitPools'][row['product']]))+Decimal(credit)/100))
        balance=cents(card['statementBalance']);debt_part=min(balance,amount);surplus=amount-debt_part
        if debt_part:ledger(state,f'2010 · Card Payable ({card["uid"]})','5010 · Purchase Expense',Decimal(debt_part)/100,'Refund original purchase · '+row['id'])
        if surplus:
            if Decimal(str(state['treasuryWallets']['USD']))+Decimal(surplus)/100>1_000_000_000:raise DomainError('退款后钱包超上限 / Wallet limit exceeded')
            set_money(state['treasuryWallets'],'USD',Decimal(str(state['treasuryWallets']['USD']))+Decimal(surplus)/100)
            ledger(state,'1010 · Cash (USD)','5010 · Purchase Expense',Decimal(surplus)/100,'Refund surplus · '+row['id'])
        set_money(card,'statementBalance',Decimal(balance-debt_part)/100)
        state['jrPointsBalance']-=points+welcome
        if points:ledger(state,'4030 · Rewards Income','1100 · JR Rewards Asset',Decimal(points)/100,'Reverse purchase rewards')
        if welcome:ledger(state,'4030 · Welcome Bonus Income','1100 · JR Rewards Asset',Decimal(welcome)/100,'Reverse welcome bonus after net spend falls below threshold')
        db.execute('INSERT OR REPLACE INTO refund_totals VALUES(?,?,?,?)',(row['id'],total,credit_total,point_total))
        feed(state,'模拟退款 / Demo refund · '+row['merchant'],f'-${amount/100:.2f}',f'-{points+welcome} JR','refund')
        return {'message':'退款已入账，积分与抵扣已冲回 / Refund posted; rewards and credits reversed','refund':{'original':row['id'],'purchase':-amount,'credits':-credit,'rewards':-points,'welcome':-welcome,'merchant':row['merchant'],'category':row['category'],'product':row['product']}}
    if card['status']=='CLOSED':raise DomainError('卡片已关闭 / Card is closed',409)
    if route=='cards/close':
        if cents(card['statementBalance']):raise DomainError('请先结清全部欠款 / Settle all card debt before closing',409)
        card['status']='CLOSED';card['closedAt']=now;card['remainingCreditPool']=0;card['closedCreditLimit']=card['creditLimit'];card['creditLimit']=0
        pref=preferences(db,uid)
        if pref['defaultCard']==card['uid']:
            pref['defaultCard']='';db.execute('INSERT OR REPLACE INTO user_options VALUES(?,?)',(uid,json.dumps(pref)))
        feed(state,'模拟销卡 / Card closed · '+PRODUCTS[card['cardId']]['name'],'$0.00','','lifecycle')
        return {'message':'卡片已关闭，历史记录保留，未使用权益失效 / Card closed; history retained and unused benefits forfeited'}
    if route=='cards/replace':
        if data.get('reason') not in ('lost','damaged','expired'):raise DomainError('请选择补换卡原因 / Select replacement reason')
        if data.get('reason')=='expired' and card['expiresAt']-now>60*86400:raise DomainError('到期前 60 天内可换卡 / Renewal replacement opens 60 days before expiry',409)
        card['cardNumber']=pan(PRODUCTS[card['cardId']]['bin']);card['cvv']=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ0123456789') for _ in range(5))
        card['expiresAt']=epoch(add_months(datetime.fromtimestamp(now,timezone.utc).isoformat(),60));card['expDate']=datetime.fromtimestamp(card['expiresAt'],timezone.utc).strftime('%m/%y')
        card['replacementCount']+=1;card['status']='ACTIVE'
        feed(state,'模拟补换卡 / Card replaced · '+PRODUCTS[card['cardId']]['name'],'$0.00','','lifecycle')
        return {'message':'补换卡完成，卡号和安全码已更新，原账户与账务保留 / Card replaced; number and code changed, account history retained'}
    raise DomainError('操作无效 / Invalid operation',404)

def capture_extended(db,uid,rid,route,result,state,now):
    if route=='pos/refund':
        r=result['refund'];card=card_for(state,db.execute('SELECT card_uid FROM business_records WHERE id=?',(rid,)).fetchone()[0])
        db.execute('INSERT OR IGNORE INTO spend_facts VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(rid,uid,card['uid'],r['product'],now,r['merchant'],r['category'],r['purchase'],r['credits'],r['rewards'],r['welcome'],0))
    if route in ('pos/refund','cards/replace','cards/close'):notify(db,uid,rid,'lifecycle',result['message'],result['message'],now)
