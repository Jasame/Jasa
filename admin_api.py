"""Read-only administrative endpoints with server-side authorization and access audit."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from functools import wraps
import json
from pathlib import Path
import re
import time
from flask import g, jsonify, request, send_from_directory
from werkzeug.utils import redirect
from domain import DomainError, CURRENCIES
from records import public_card, sanitize, safe_text

CHINA=timezone(timedelta(hours=8))

def audit_access(db,actor,action,target='',filters=None):
    db.execute('INSERT INTO admin_access(actor_id,action,target,filters,created) VALUES(?,?,?,?,?)',(actor,action,target,json.dumps(filters or {},ensure_ascii=False),int(time.time())))

def register_admin(app,connect,require,identity,limited,root,mail_ready):
    def admin(fn):
        @wraps(fn)
        @require
        def wrapper(*args,**kwargs):
            if not g.user['admin']:raise DomainError('需要管理员权限 / Admin required',403)
            limited('admin-read:'+g.user['id'],180,60)
            return fn(*args,**kwargs)
        return wrapper

    def log(action,target=''):
        with connect() as db:
            audit_access(db,g.user['id'],action,target,{k:str(v)[:254] for k,v in request.args.items() if k in ('q','page','pageSize','from','to','status','route','userId','role','result')})

    def integer(name,default,maximum):
        raw=request.args.get(name,str(default))
        if not re.fullmatch(r'[1-9][0-9]{0,6}',raw) or int(raw)>maximum:raise DomainError('分页参数无效 / Invalid pagination')
        return int(raw)

    def page_rows(db,select,source,where,args,order):
        page=integer('page',1,1000000);size=integer('pageSize',20,100)
        clause=' WHERE '+' AND '.join(where) if where else ''
        count=db.execute('SELECT COUNT(*) FROM '+source+clause,args).fetchone()[0]
        pages=max(1,(count+size-1)//size);page=min(page,pages)
        rows=db.execute('SELECT '+select+' FROM '+source+clause+' ORDER BY '+order+' LIMIT ? OFFSET ?',[*args,size,(page-1)*size]).fetchall()
        return rows,dict(page=page,pageSize=size,total=count,pages=pages)

    def query_text():
        q=request.args.get('q','').strip()
        if len(q)>254:raise DomainError('搜索内容过长 / Search is too long')
        return '%'+q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%' if q else None

    def dates(where,args,column):
        values={}
        for name in ('from','to'):
            value=request.args.get(name)
            if not value:continue
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise ValueError()
                values[name]=datetime.strptime(value,'%Y-%m-%d').replace(tzinfo=CHINA)
            except ValueError:raise DomainError('日期格式无效 / Invalid date')
        if len(values)==2 and values['from']>values['to']:raise DomainError('开始日期晚于结束日期 / Date range is reversed')
        if 'from' in values:where.append(column+'>=?');args.append(int(values['from'].timestamp()))
        if 'to' in values:
            try:upper=int((values['to']+timedelta(days=1)).timestamp())
            except (OverflowError,ValueError):raise DomainError('结束日期超出范围 / End date is out of range')
            where.append(column+'<?');args.append(upper)

    def user_filter(where,args,column):
        uid=request.args.get('userId','')
        if uid:
            if len(uid)>100:raise DomainError('用户编号无效 / Invalid user ID')
            where.append(column+'=?');args.append(uid)

    @app.get('/admin')
    def admin_redirect():return redirect(app.config['BASE_PATH']+'/admin/',code=308)

    @app.get('/admin/')
    def admin_page():
        user=identity()
        if not user:return redirect(app.config['BASE_PATH']+'/#admin',code=303)
        if not user['admin']:
            return '<!doctype html><meta charset="utf-8"><title>JWB</title><p>需要管理员权限 / Admin access required.</p>',403,{'Cache-Control':'no-store'}
        with connect() as db:audit_access(db,user['id'],'page_open')
        response=send_from_directory(root/'static','admin.html')
        response.headers['Cache-Control']='no-store'
        return response

    @app.get('/api/admin/summary')
    @admin
    def summary():
        log('summary')
        now=int(time.time());day=datetime.now(CHINA).replace(hour=0,minute=0,second=0,microsecond=0)
        since=int((day-timedelta(days=13)).timestamp())
        with connect() as db:
            # One read transaction keeps counts and aggregates consistent during user commands.
            db.execute('BEGIN')
            wallets={c:Decimal(0) for c in CURRENCIES};points=Decimal(0);debt=Decimal(0);credit=Decimal(0);cards=0;frozen=0
            for row in db.execute('SELECT state FROM accounts'):
                value=json.loads(row['state']);cards+=sum(c.get('status')!='CLOSED' for c in value['cards']);points+=Decimal(str(value['jrPointsBalance']))
                for c in CURRENCIES:wallets[c]+=Decimal(str(value['treasuryWallets'].get(c,0)))
                for card in value['cards']:
                    debt+=Decimal(str(card['statementBalance']));credit+=Decimal(str(card['creditLimit']));frozen+=card['status']=='FROZEN'
            users=db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
            admins=db.execute('SELECT COUNT(*) FROM users WHERE admin=1').fetchone()[0]
            logins=db.execute("SELECT COUNT(DISTINCT user_id) FROM security_events WHERE event='signed_in' AND created>=?",(now-7*86400,)).fetchone()[0]
            records=dict(db.execute('SELECT COUNT(*) AS total,SUM(CASE WHEN legacy=0 THEN 1 ELSE 0 END) AS current,SUM(CASE WHEN legacy=0 AND status>=400 THEN 1 ELSE 0 END) AS failed FROM business_records').fetchone())
            tracked=db.execute("SELECT created FROM schema_migrations WHERE name='admin-history-v1'").fetchone()[0]
            days={(day-timedelta(days=i)).strftime('%Y-%m-%d'):{'newUsers':0,'operations':0} for i in reversed(range(14))}
            for table,field,condition in [('users','newUsers',''),('business_records','operations',' AND legacy=0')]:
                for row in db.execute('SELECT created FROM '+table+' WHERE created>=?'+condition,(since,)):
                    key=datetime.fromtimestamp(row['created'],CHINA).strftime('%Y-%m-%d')
                    if key in days:days[key][field]+=1
        return jsonify(users=users,admins=admins,logins7d=logins,cards=cards,frozenCards=frozen,wallets={c:float(v) for c,v in wallets.items()},points=float(points),debtUSD=float(debt),creditUSD=float(credit),records=records,trackedSince=tracked,trend=[dict(date=k,**v) for k,v in days.items()],generatedAt=now)

    @app.get('/api/admin/users')
    @admin
    def users():
        where=[];args=[];q=query_text()
        if q:where.append("(u.email LIKE ? ESCAPE '\\' OR u.id LIKE ? ESCAPE '\\')");args.extend([q,q])
        role=request.args.get('role','')
        if role not in ('','admin','user'):raise DomainError('角色筛选无效 / Invalid role filter')
        if role:where.append('u.admin=?');args.append(int(role=='admin'))
        dates(where,args,'u.created');log('users_search')
        with connect() as db:
            db.execute('BEGIN')
            rows,paging=page_rows(db,"u.id,u.email,u.admin,u.created,a.state,COALESCE(f.disabled,0) AS disabled,(SELECT MAX(created) FROM security_events s WHERE s.user_id=u.id AND s.event='signed_in') AS lastLogin",'users u JOIN accounts a ON a.user_id=u.id LEFT JOIN user_flags f ON f.user_id=u.id',where,args,'u.created DESC,u.id')
            result=[]
            for row in rows:
                state=json.loads(row['state']);result.append({k:row[k] for k in ('id','email','admin','created','lastLogin','disabled') }|{'cards':sum(c.get('status')!='CLOSED' for c in state['cards']),'wallets':state['treasuryWallets'],'points':state['jrPointsBalance'],'debtUSD':round(sum(c['statementBalance'] for c in state['cards']),2)})
        return jsonify(items=result,**paging)

    @app.get('/api/admin/users/<uid>')
    @admin
    def user_detail(uid):
        log('user_detail',uid[:100])
        with connect() as db:
            db.execute('BEGIN')
            row=db.execute('SELECT u.id,u.email,u.admin,u.created,a.state,a.revision FROM users u JOIN accounts a ON a.user_id=u.id WHERE u.id=?',(uid,)).fetchone()
            if not row:raise DomainError('用户不存在 / User not found',404)
            state=json.loads(row['state'])
            security=[dict(r) for r in db.execute('SELECT event,created FROM security_events WHERE user_id=? ORDER BY id DESC LIMIT 20',(uid,))]
            sessions=[dict(r) for r in db.execute('SELECT s.expires,d.created,d.last_seen,d.agent,d.network FROM sessions s LEFT JOIN session_details d ON d.token=s.token WHERE s.user_id=? AND s.expires>? ORDER BY COALESCE(d.last_seen,0) DESC LIMIT 20',(uid,int(time.time())))]
            flags=db.execute('SELECT disabled,reason FROM user_flags WHERE user_id=?',(uid,)).fetchone()
        return jsonify(user={**{k:row[k] for k in ('id','email','admin','created','revision')},'disabled':bool(flags and flags['disabled']),'disabledReason':flags['reason'] if flags else ''},wallets=state['treasuryWallets'],points=state['jrPointsBalance'],cards=[public_card(c) for c in state['cards']],security=sanitize(security),sessions=sanitize(sessions))

    def records_list(application=False):
        where=[];args=[];q=query_text()
        if application:where.append("r.route='underwriting/issue-card'")
        if q:where.append("(u.email LIKE ? ESCAPE '\\' OR r.id LIKE ? ESCAPE '\\' OR r.summary LIKE ? ESCAPE '\\')");args.extend([q]*3)
        status=request.args.get('status','')
        if status not in ('','success','failed'):raise DomainError('结果筛选无效 / Invalid result filter')
        if status:where.append('r.status'+('<400' if status=='success' else '>=400'))
        route=request.args.get('route','')
        if route:
            if route not in ('legacy/activity','treasury/wire-in','treasury/fx-swap','treasury/accrue-apy','underwriting/issue-card','pos/authorize','cards/repay','cards/security-freeze','cards/rotate-cvv','cards/product-change','cards/reallocate-limit','credit/cli-3x','core/reset','benefits/use','admin/adjust-wallet','admin/adjust-points','pos/refund','cards/replace','cards/close','cards/annual-renewal'):raise DomainError('业务类型无效 / Invalid operation filter')
            where.append('r.route=?');args.append(route)
        user_filter(where,args,'r.user_id');dates(where,args,'r.created');log('applications_search' if application else 'records_search')
        with connect() as db:
            db.execute('BEGIN')
            rows,paging=page_rows(db,'r.id,r.user_id,u.email,r.route,r.status,r.created,r.product,r.card_uid,r.summary,r.legacy','business_records r JOIN users u ON u.id=r.user_id',where,args,'r.created DESC,r.rowid DESC')
        return jsonify(items=[dict(r) for r in rows],**paging)

    @app.get('/api/admin/records')
    @admin
    def records():return records_list()

    @app.get('/api/admin/applications')
    @admin
    def applications():return records_list(True)

    @app.get('/api/admin/records/<rid>')
    @admin
    def record_detail(rid):
        log('record_detail',rid[:100])
        with connect() as db:
            row=db.execute('SELECT r.id,r.user_id,u.email,r.route,r.status,r.created,r.product,r.card_uid,r.summary,r.details,r.legacy FROM business_records r JOIN users u ON u.id=r.user_id WHERE r.id=?',(rid,)).fetchone()
            if not row:raise DomainError('记录不存在 / Record not found',404)
            result=dict(row);result['details']=sanitize(json.loads(result['details']))
        return jsonify(result)

    @app.get('/api/admin/ledger')
    @admin
    def ledger():
        where=[];args=[];q=query_text()
        if q:where.append("(u.email LIKE ? ESCAPE '\\' OR l.entry_id LIKE ? ESCAPE '\\')");args.extend([q,q])
        user_filter(where,args,'l.user_id');dates(where,args,'l.created');log('ledger_search')
        with connect() as db:
            db.execute('BEGIN')
            rows,paging=page_rows(db,'l.user_id,u.email,l.entry_id,l.record_id,l.created,l.details,l.legacy','ledger_records l JOIN users u ON u.id=l.user_id',where,args,'l.created DESC,l.entry_id')
        return jsonify(items=[{**dict(row),'details':sanitize(json.loads(row['details']))} for row in rows],**paging)

    @app.get('/api/admin/mail')
    @admin
    def mail():
        where=[];args=[];q=query_text()
        if q:where.append("email LIKE ? ESCAPE '\\'");args.append(q)
        status=request.args.get('result','')
        if status not in ('','accepted','failed'):raise DomainError('邮件结果无效 / Invalid email result')
        if status:where.append('result=?');args.append(status)
        dates(where,args,'created');log('mail_search')
        with connect() as db:
            db.execute('BEGIN')
            rows,paging=page_rows(db,'id,email,purpose,result,error_category,created','mail_events',where,args,'created DESC,id DESC')
        return jsonify(items=[dict(r) for r in rows],**paging)

    @app.get('/api/admin/audit')
    @admin
    def access_audit():
        where=[];args=[];q=query_text()
        if q:where.append("(u.email LIKE ? ESCAPE '\\' OR a.target LIKE ? ESCAPE '\\')");args.extend([q,q])
        dates(where,args,'a.created');log('audit_search')
        with connect() as db:
            db.execute('BEGIN')
            rows,paging=page_rows(db,'a.id,u.email,a.actor_id,a.action,a.target,a.filters,a.created','admin_access a JOIN users u ON u.id=a.actor_id',where,args,'a.id DESC')
        return jsonify(items=[{**dict(r),'filters':json.loads(r['filters'])} for r in rows],**paging)

    def backup_status():
        directory=Path(app.config['BACKUP_DIR'])
        try:
            reports=sorted((p for p in directory.iterdir() if p.name.endswith('.sqlite3.json') and not p.is_symlink()),key=lambda p:p.stat().st_mtime,reverse=True)
            for report in reports[:50]:
                if report.stat().st_size>16000:continue
                data=json.loads(report.read_text());snapshot=report.with_suffix('')
                if snapshot.is_symlink() or not snapshot.is_file():continue
                verified=datetime.fromisoformat(data['verifiedAt']).timestamp()
                if data.get('restoreDrill')!='passed':continue
                return {'state':'recent' if time.time()-verified<36*3600 else 'old','name':snapshot.name,'verifiedAt':verified,'users':data.get('users'),'accounts':data.get('accounts'),'bytes':snapshot.stat().st_size,'check':'reported_passed'}
            return {'state':'missing'}
        except FileNotFoundError:return {'state':'missing'}
        except PermissionError:return {'state':'permission_denied'}
        except (OSError,ValueError,KeyError,TypeError):return {'state':'unreadable'}

    @app.get('/api/admin/system')
    @admin
    def system():
        log('system_status');now=time.time()
        with connect() as db:
            settings=json.loads(db.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])
            fxrow=db.execute('SELECT value FROM fx WHERE id=1').fetchone()
            mailcounts={row['result']:row['total'] for row in db.execute('SELECT result,COUNT(*) AS total FROM mail_events WHERE created>=? GROUP BY result',(int(now)-86400,))}
            since=db.execute("SELECT created FROM schema_migrations WHERE name='admin-history-v1'").fetchone()[0]
            version=db.execute('SELECT sqlite_version()').fetchone()[0]
        fx={'state':'not_loaded'}
        if fxrow:
            value=json.loads(fxrow['value'])
            try:
                fetched=float(value['fetchedAt']);asof=datetime.fromisoformat(value['asOf']).timestamp()
                state='recent' if now-fetched<app.config['FX_REFRESH_SECONDS'] and now-asof<7*86400 else 'cached' if now-fetched<86400 and now-asof<7*86400 else 'expired'
                fx={k:value.get(k) for k in ('source','asOf','fetchedAt','mode')};fx['state']=state
            except (ValueError,KeyError,TypeError):fx={'state':'invalid'}
        return jsonify(settings=settings,mail={'configured':mail_ready(),'mode':app.config['MAIL_MODE'],'accepted24h':mailcounts.get('accepted',0),'failed24h':mailcounts.get('failed',0)},fx=fx,backup=backup_status(),database={'sqliteVersion':version,'state':'query_ok'},trackedSince=since,generatedAt=int(now))
