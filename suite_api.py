"""User product features, isolated preset demos and controlled administrator actions."""
from datetime import datetime
from decimal import Decimal
import hashlib
import hmac
import json
import re
import secrets
import uuid
from io import BytesIO
from flask import request,jsonify,g,send_file,send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import redirect
from domain import DomainError,PRODUCTS,empty_state,execute,ledger,feed,audit_log,number,set_money
from records import record_command,public_card
from admin_api import audit_access
from suite import TZ,VOUCHERS,clock,next_close,refresh_benefit_period,billing_view,statement_view,analytics,capture_operation,notify,cents
from reports import report_pdf
from growth_security import verify_factor

def register_suite(app,connect,require,limited,payload,maintain,live_session,root):
    def user_state(db,uid):
        maintain(db,uid,clock(app));row=db.execute('SELECT state,revision FROM accounts WHERE user_id=?',(uid,)).fetchone()
        return json.loads(row['state']),row['revision']
    def selection():
        year=request.args.get('year');month=request.args.get('month',datetime.fromtimestamp(clock(app),TZ).strftime('%Y-%m'))
        try:
            if year:
                if not re.fullmatch(r'20\d{2}|21\d{2}',year):raise ValueError()
                start=datetime(int(year),1,1,tzinfo=TZ);end=start.replace(year=start.year+1)
            else:
                if not re.fullmatch(r'20\d{2}-\d{2}|21\d{2}-\d{2}',month):raise ValueError()
                start=datetime.strptime(month,'%Y-%m').replace(tzinfo=TZ);end=start.replace(year=start.year+1,month=1) if start.month==12 else start.replace(month=start.month+1)
        except ValueError:raise DomainError('日期选择无效 / Invalid period')
        return int(start.timestamp()),int(end.timestamp()),start.year
    def lang():
        language=request.args.get('lang','zh')
        if language not in ('zh','en'):raise DomainError('语言无效 / Invalid language')
        return language
    @app.get('/api/billing')
    @require
    def billing():
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');state,_=user_state(db,g.user['id']);data=billing_view(db,g.user['id'],state)
        return jsonify(data)
    @app.post('/api/billing/settings')
    @require
    def billing_settings():
        data=payload();day=data.get('closeDay');due=data.get('dueDays')
        if isinstance(day,bool) or not isinstance(day,int) or not 1<=day<=28 or isinstance(due,bool) or not isinstance(due,int) or not 7<=due<=28:raise DomainError('账单日 1–28，还款间隔 7–28 天 / Close day 1–28; payment interval 7–28 days')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');user_state(db,g.user['id'])
            db.execute('UPDATE billing_profiles SET close_day=?,due_days=?,next_close=? WHERE user_id=?',(day,due,next_close(clock(app),day),g.user['id']))
        return jsonify(message='后续账期设置已更新；已出账单不变 / Future billing settings updated; existing statements unchanged')
    @app.get('/api/statements/<sid>/pdf')
    @require
    def statement_pdf(sid):
        limited('pdf:'+g.user['id'],20,60)
        with connect() as db:
            row=db.execute('SELECT * FROM statements WHERE id=? AND user_id=?',(sid,g.user['id'])).fetchone()
            if not row:raise DomainError('账单不存在 / Statement not found',404)
            value=statement_view(db,row)
        return send_file(BytesIO(report_pdf('statement',value,g.user['email'],lang())),mimetype='application/pdf',as_attachment=True,download_name='JWB-'+sid+'.pdf',max_age=0)
    @app.get('/api/benefits')
    @require
    def benefits():
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');state,_=user_state(db,g.user['id']);cards=[]
            for card in state['cards']:
                if card.get('status')=='CLOSED':continue
                expiry=refresh_benefit_period(card,clock(app));vouchers=[]
                for key,zh,en,limit in VOUCHERS[card['cardId']]:
                    count=card['benefitUses'].get(f'{card["benefitPeriod"]}:{card["cardId"]}:{key}',0)
                    vouchers.append({'id':key,'zh':zh,'en':en,'limit':limit,'used':count})
                cards.append({'uid':card['uid'],'product':card['cardId'],'last4':card['cardNumber'][-4:],'status':card['status'],'expires':expiry,'remainingCredit':card['remainingCreditPool'],'creditLimit':PRODUCTS[card['cardId']]['fixedCredits'],'rule':PRODUCTS[card['cardId']].get('autoCreditRule'),'vouchers':vouchers,'welcome':{'product':card['welcomeProductId'],'earned':card['welcomeUnlocked'],'spent':card['spendProgress'],'required':PRODUCTS[card['welcomeProductId']]['welcomeSpendReq'],'expires':card['welcomeExpiresAt'],'points':PRODUCTS[card['welcomeProductId']]['welcomeJR']}})
            usage=[dict(row) for row in db.execute('SELECT id,card_uid,product,benefit_id,created,note FROM benefit_usage WHERE user_id=? ORDER BY created DESC,id DESC LIMIT 100',(g.user['id'],))]
        return jsonify(cards=cards,usage=usage)
    @app.get('/api/analytics')
    @require
    def analysis():
        start,end,year=selection();merchant=request.args.get('merchant','').strip();category=request.args.get('category','');card=request.args.get('cardUid','')
        if len(merchant)>120 or len(card)>100 or category not in ('','dining','travel','hotel','everyday','fee'):raise DomainError('筛选参数无效 / Invalid filters')
        with connect() as db:
            data=analytics(db,g.user['id'],start,end,card,category,merchant)
            data['cards']=[dict(row) for row in db.execute('SELECT DISTINCT card_uid,product FROM spend_facts WHERE user_id=?',(g.user['id'],))]
        return jsonify(**data,year=year)
    @app.get('/api/analytics/report.pdf')
    @require
    def annual_pdf():
        if not request.args.get('year'):raise DomainError('请选择报告年份 / Select a report year')
        limited('pdf:'+g.user['id'],20,60);start,end,year=selection()
        with connect() as db:data=analytics(db,g.user['id'],start,end)
        data['year']=year
        return send_file(BytesIO(report_pdf('annual',data,g.user['email'],lang())),mimetype='application/pdf',as_attachment=True,download_name=f'JWB-Annual-{year}.pdf',max_age=0)
    @app.get('/api/notifications')
    @require
    def notifications():
        raw=request.args.get('page','1')
        if not re.fullmatch(r'[1-9]\d{0,5}',raw):raise DomainError('分页无效 / Invalid page')
        page=int(raw);uid=g.user['id'];unread=request.args.get('unread')=='1'
        with connect() as db:
            where='user_id=?'+(' AND is_read=0' if unread else '')
            total=db.execute('SELECT COUNT(*) FROM notifications WHERE '+where,(uid,)).fetchone()[0]
            pages=max(1,(total+29)//30);page=min(page,pages)
            rows=[dict(r) for r in db.execute('SELECT id,created,kind,title,body,is_read FROM notifications WHERE '+where+' ORDER BY created DESC,id DESC LIMIT 30 OFFSET ?',(uid,(page-1)*30))]
            count=db.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0',(uid,)).fetchone()[0]
        return jsonify(items=rows,unread=count,page=page,pages=pages,total=total)
    @app.post('/api/notifications/read')
    @require
    def read_notifications():
        data=payload()
        with connect() as db:
            if data.get('all') is True:db.execute('UPDATE notifications SET is_read=1 WHERE user_id=?',(g.user['id'],))
            else:
                result=db.execute('UPDATE notifications SET is_read=1 WHERE user_id=? AND id=?',(g.user['id'],data.get('id')))
                if not result.rowcount:raise DomainError('通知不存在 / Notification not found',404)
        return jsonify(saved=True)

    @app.post('/api/admin/actions')
    @require
    def admin_actions():
        if not g.user['admin']:raise DomainError('需要管理员权限 / Admin required',403)
        limited('admin-write:'+g.user['id'],30,900);data=payload();key=request.headers.get('Idempotency-Key','')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{16,100}',key):raise DomainError('需要幂等键 / Idempotency key required')
        action=data.get('action');reason=str(data.get('reason','')).strip()
        if not 6<=len(reason)<=200:raise DomainError('操作原因须为 6–200 字 / Reason must be 6–200 characters')
        if action not in ('disable','enable','revoke','adjust-wallet','adjust-points','settings'):raise DomainError('管理操作无效 / Invalid admin action')
        signature=hashlib.sha256(json.dumps({k:v for k,v in data.items() if k not in ('currentPassword','factor')},sort_keys=True).encode()).hexdigest()
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            live_session(db)
            actor=db.execute('SELECT * FROM users WHERE id=?',(g.user['id'],)).fetchone()
            if not actor['admin'] or not check_password_hash(actor['password'],str(data.get('currentPassword',''))[:129]):raise DomainError('请验证当前管理员密码 / Verify your current administrator password',400)
            previous=db.execute('SELECT hash,response FROM admin_commands WHERE actor_id=? AND key=?',(actor['id'],key)).fetchone()
            if previous:
                if not hmac.compare_digest(signature,previous['hash']):raise DomainError('重复操作参数不一致 / Idempotency parameters conflict',409)
                return jsonify(json.loads(previous['response']))
            verify_factor(app,db,actor['id'],data.get('factor'))
            uid=str(data.get('userId',''));now=clock(app)
            if action=='settings':
                registration=data.get('publicRegistration');income=data.get('minIncome')
                if not isinstance(registration,bool):raise DomainError('注册开关无效 / Invalid registration switch')
                income=number(income,0,1_000_000_000)
                if income!=int(income):raise DomainError('收入门槛须为整数 / Income threshold must be an integer')
                settings=json.loads(db.execute('SELECT value FROM settings WHERE id=1').fetchone()[0]);settings.update(public_registration=registration,min_income=int(income))
                db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(settings),));uid='settings'
            else:
                target=db.execute('SELECT id,email,admin FROM users WHERE id=?',(uid,)).fetchone()
                if not target:raise DomainError('用户不存在 / User not found',404)
                if action=='disable' and uid==actor['id']:raise DomainError('不能停用当前管理员自己 / Cannot disable your own account',409)
                if action=='disable' and target['admin']:
                    count=db.execute('SELECT COUNT(*) FROM users u WHERE admin=1 AND NOT EXISTS(SELECT 1 FROM user_flags f WHERE f.user_id=u.id AND f.disabled=1)').fetchone()[0]
                    if count<=1:raise DomainError('必须保留可用管理员 / Keep at least one enabled administrator',409)
                if action in ('disable','enable'):
                    db.execute('INSERT OR REPLACE INTO user_flags VALUES(?,?,?,?)',(uid,int(action=='disable'),reason,now))
                if action in ('disable','revoke'):
                    db.execute('DELETE FROM sessions WHERE user_id=?',(uid,));db.execute('DELETE FROM codes WHERE email=?',(target['email'],))
                if action in ('adjust-wallet','adjust-points'):
                    state,revision=user_state(db,uid);before=json.loads(json.dumps(state));amount=number(data.get('amount'),-1_000_000,1_000_000)
                    if amount==0:raise DomainError('调整金额不能为零 / Adjustment cannot be zero')
                    if action=='adjust-wallet':
                        if amount!=amount.quantize(Decimal('.01')):raise DomainError('USD 最多两位小数 / USD allows two decimals')
                        balance=Decimal(str(state['treasuryWallets']['USD']))+amount
                        if not 0<=balance<=1_000_000_000:raise DomainError('调整后余额超出范围 / Adjusted balance is out of range')
                        set_money(state['treasuryWallets'],'USD',balance);asset='1010 · Cash (USD)';equity='3020 · Admin Demo Adjustment';usd_amount=abs(amount)
                    else:
                        if amount!=int(amount) or not 0<=state['jrPointsBalance']+int(amount)<=1_000_000_000:raise DomainError('积分须为整数且调整后不超范围 / Rewards must be whole numbers within balance limits')
                        state['jrPointsBalance']+=int(amount);asset='1100 · JR Rewards Asset';equity='4040 · Admin Demo Rewards';usd_amount=abs(amount)/100
                    ledger(state,asset if amount>0 else equity,equity if amount>0 else asset,usd_amount,'Admin adjustment · '+reason)
                    feed(state,'管理员模拟调整 / Admin demo adjustment',f'{amount:+} '+('USD' if action=='adjust-wallet' else 'JR'),'','admin')
                    result={'message':'管理员模拟调整已记录 / Admin demo adjustment recorded','adminAction':{'actor':actor['id'],'reason':reason}}
                    route='admin/'+action;audit_log(state,'/api/v1/'+route,200,result['message'])
                    db.execute('UPDATE accounts SET state=?,revision=? WHERE user_id=?',(json.dumps(state),revision+1,uid))
                    rid=record_command(db,uid,'admin:'+actor['id']+':'+key,route,{'amount':str(amount),'reason':reason},result,200,before,state,{})
                    capture_operation(db,uid,rid,route,data,result,before,state,200,now)
                db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(uid,'admin_'+action,now))
            audit_access(db,actor['id'],'manage:'+action,uid,{'reason':reason,'amount':str(data.get('amount','')),'publicRegistration':data.get('publicRegistration'),'minIncome':data.get('minIncome')})
            result={'message':'管理操作已完成并记录审计 / Admin action completed and audited'}
            db.execute('INSERT INTO admin_commands VALUES(?,?,?,?)',(actor['id'],key,signature,json.dumps(result)))
        return jsonify(result)

    @app.get('/demo')
    def demo_redirect():return redirect(app.config['BASE_PATH']+'/demo/',code=308)
    @app.get('/demo/')
    def demo_page():return send_from_directory(root/'static','demo.html')
    @app.post('/api/demo/scenario')
    def demo_scenario():
        limited('demo:'+str(request.remote_addr),30,60);data=payload();scenario=data.get('scenario','travel')
        if scenario not in ('travel','dining','first-card'):raise DomainError('请选择有效演示场景 / Invalid demo scenario')
        state=empty_state();steps=[];table={'USD':1,'CNY':1/7,'HKD':1/7.8,'JPY':1/150,'GBP':1.25,'EUR':1.1};rules={'min_income':5000}
        def step(title,route,inputs):
            result=execute(state,route,inputs,table,rules)
            steps.append({'title':title,'message':result['message'],'wallets':dict(state['treasuryWallets']),'points':state['jrPointsBalance'],'cards':[public_card(c) for c in state['cards']],'feed':state['posFeed'][:5]})
        step('模拟入金 / Add demo funds','treasury/wire-in',{'currency':'USD','amount':10000})
        product='platinum' if scenario=='travel' else 'gold' if scenario=='dining' else 'everyday'
        step('申请并发卡 / Apply and issue','underwriting/issue-card',{'cardId':product,'income':100000,'months':12,'existing':0,'holderName':'DEMO VISITOR'})
        card=state['cards'][0]
        if scenario=='travel':step('参考换汇 / Reference FX','treasury/fx-swap',{'_quote':{'from':'USD','to':'CNY','amount':'100','received':'700','rate':'7','usdRate':'1','source':'FIXED DEMO REFERENCE','asOf':'fixed demo'}})
        step('模拟消费与权益 / Spend and explore benefits','pos/authorize',{'uid':card['uid'],'currency':'USD','amount':500 if scenario=='travel' else 100,'category':'travel' if scenario=='travel' else 'dining' if scenario=='dining' else 'everyday','merchant':'DEMO HOTEL' if scenario=='travel' else 'DEMO MERCHANT'})
        step('模拟还款 / Repay demo balance','cards/repay',{'uid':card['uid'],'method':'USD'})
        return jsonify(scenario=scenario,steps=steps,fixedRates=True,persisted=False)
