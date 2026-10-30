"""Preferences, calendar, lifecycle records, feedback and operations endpoints."""
from datetime import datetime,timezone
import json
import re
import uuid
from io import BytesIO
from flask import g,request,jsonify,send_file
from domain import DomainError,CURRENCIES
from records import public_card
from suite import clock,billing_view,refresh_benefit_period
from growth import preferences,DEFAULT_PREFS,VERSION,lifecycle_defaults
from growth_security import sensitive
from admin_api import audit_access

def register_growth(app,connect,require,limited,payload,live_session,maintain,root):
    def state(db):
        maintain(db,g.user['id'],clock(app));return json.loads(db.execute('SELECT state FROM accounts WHERE user_id=?',(g.user['id'],)).fetchone()[0])
    @app.get('/api/health')
    def health():
        with connect() as db:db.execute('SELECT 1').fetchone()
        return jsonify(ok=True,version=VERSION)
    @app.get('/api/releases')
    def releases():return jsonify(json.loads((root/'releases.json').read_text()))
    @app.get('/api/preferences')
    @require
    def get_preferences():
        with connect() as db:value=preferences(db,g.user['id'])
        return jsonify(value)
    @app.post('/api/preferences')
    @require
    def save_preferences():
        data=payload();limited('preferences:'+g.user['id'],60,60)
        if not data or any(key not in DEFAULT_PREFS for key in data):raise DomainError('偏好设置无效 / Invalid preferences')
        for key,value in data.items():
            if isinstance(DEFAULT_PREFS[key],bool) and not isinstance(value,bool):raise DomainError('偏好开关无效 / Invalid preference switch')
        if 'language' in data and data['language'] not in ('zh','en') or 'favoriteCurrency' in data and data['favoriteCurrency'] not in CURRENCIES:raise DomainError('语言或币种无效 / Invalid language or currency')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);value=state(db)
            if data.get('defaultCard') and not any(c['uid']==data['defaultCard'] and c['status']!='CLOSED' for c in value['cards']):raise DomainError('默认卡片无效 / Invalid default card')
            prefs=preferences(db,g.user['id']);prefs.update(data);db.execute('INSERT OR REPLACE INTO user_options VALUES(?,?)',(g.user['id'],json.dumps(prefs)))
        return jsonify(saved=True,preferences=prefs,message='偏好已同步 / Preferences synced')
    @app.get('/api/card-services')
    @require
    def card_services():
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');value=state(db)
            rows=[dict(r) for r in db.execute('SELECT f.id,f.card_uid,f.product,f.created,f.merchant,f.purchase_cents,COALESCE(t.cents,0) AS refundedCents FROM spend_facts f JOIN business_records r ON r.id=f.id LEFT JOIN refund_totals t ON t.record_id=f.id WHERE f.user_id=? AND r.route=? AND r.status<400 AND f.purchase_cents>0 ORDER BY f.created DESC,f.rowid DESC LIMIT 200',(g.user['id'],'pos/authorize'))]
        return jsonify(cards=[public_card(c) for c in value['cards']],purchases=rows,pointsMayBeNegative=True)
    def calendar_data():
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');value=state(db);bill=billing_view(db,g.user['id'],value);events=[]
            events.append({'id':'next-close','kind':'statement','at':bill['profile']['next_close']-1,'title':'下次账单日 / Next statement close','tab':'billing'})
            for s in bill['statements']:
                if s['remainingCents']>0:events.append({'id':s['id'],'kind':'due','at':s['dueAt'],'title':'账单还款截止 / Payment due · '+s['card']['last4'],'tab':'billing'})
            for c in value['cards']:
                last4=c['cardNumber'][-4:]
                if c['status']=='CLOSED':continue
                for key,title,at,tab in [('benefit','权益周年到期 / Benefit anniversary',refresh_benefit_period(c,clock(app)),'benefits'),('renew','年费周年日 / Annual fee anniversary',c['renewAt'],'services'),('expiry','卡片到期 / Card expiry',c['expiresAt'],'services')]:
                    events.append({'id':c['uid']+'-'+key,'kind':key,'at':at,'title':title+' · '+last4,'tab':tab})
                from records import epoch
                if not c['welcomeUnlocked'] and epoch(c['welcomeExpiresAt'])>clock(app):events.append({'id':c['uid']+'-welcome','kind':'welcome','at':epoch(c['welcomeExpiresAt']),'title':'欢迎奖励截止 / Welcome offer ends · '+last4,'tab':'benefits'})
        return sorted(events,key=lambda e:e['at'])
    @app.get('/api/calendar')
    @require
    def get_calendar():return jsonify(events=calendar_data(),timezone='Asia/Shanghai')
    @app.get('/api/calendar.ics')
    @require
    def calendar_ics():
        def safe(s):return s.replace('\\','\\\\').replace('\r','').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//JWB Simulation//Calendar//EN','CALSCALE:GREGORIAN','METHOD:PUBLISH']
        for e in calendar_data():
            lines+=['BEGIN:VEVENT','UID:'+e['id']+'@jwb.simulation','DTSTAMP:'+datetime.fromtimestamp(clock(app),timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'DTSTART:'+datetime.fromtimestamp(e['at'],timezone.utc).strftime('%Y%m%dT%H%M%SZ'),'SUMMARY:'+safe(e['title']),'DESCRIPTION:JWB simulation only. Re-export after changes.','END:VEVENT']
        lines+=['END:VCALENDAR'];folded=[]
        for line in lines:
            part=''
            for char in line:
                if len((part+char).encode())>73:folded.append(part);part=' '+char
                else:part+=char
            folded.append(part)
        return send_file(BytesIO(('\r\n'.join(folded)+'\r\n').encode()),mimetype='text/calendar',as_attachment=True,download_name='JWB-calendar.ics',max_age=0)
    @app.get('/api/feedback')
    @require
    def own_feedback():
        with connect() as db:items=[dict(r) for r in db.execute('SELECT id,created,updated,category,title,body,page,version,status,reply FROM feedback WHERE user_id=? ORDER BY created DESC LIMIT 100',(g.user['id'],))]
        return jsonify(items=items)
    @app.post('/api/feedback')
    @require
    def submit_feedback():
        data=payload();limited('feedback:'+g.user['id'],10,3600)
        title=str(data.get('title','')).strip();body=str(data.get('body','')).strip();category=data.get('category');page=str(data.get('page',''))
        if not 3<=len(title)<=80 or not 6<=len(body)<=2000 or category not in ('bug','idea','experience') or not re.fullmatch(r'[a-z-]{0,30}',page):raise DomainError('反馈内容或栏目无效 / Invalid feedback content or page')
        now=clock(app);fid='FB-'+uuid.uuid4().hex
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);db.execute('INSERT INTO feedback VALUES(?,?,?,?,?,?,?,?,?,?,?)',(fid,g.user['id'],now,now,category,title,body,page,VERSION,'open',''))
        return jsonify(id=fid,message='反馈已提交 / Feedback submitted'),201
    @app.get('/api/admin/operations')
    @require
    def ops_admin():
        if not g.user['admin']:raise DomainError('需要管理员权限 / Admin required',403)
        limited('ops-read:'+g.user['id'],60,60)
        with connect() as db:
            audit_access(db,g.user['id'],'operations')
            feedback=[dict(r) for r in db.execute('SELECT f.*,u.email FROM feedback f JOIN users u ON u.id=f.user_id ORDER BY CASE f.status WHEN "open" THEN 0 WHEN "working" THEN 1 ELSE 2 END,f.updated DESC LIMIT 100')]
            checks=[dict(r) for r in db.execute('SELECT * FROM ops_checks ORDER BY name')];alerts=[dict(r) for r in db.execute('SELECT * FROM ops_alerts WHERE active=1 ORDER BY first_seen')]
            total=db.execute('SELECT COUNT(*) FROM users WHERE admin=1').fetchone()[0];mfa=db.execute('SELECT COUNT(*) FROM mfa m JOIN users u ON u.id=m.user_id WHERE enabled=1 AND admin=1').fetchone()[0]
        return jsonify(version=VERSION,checks=checks,alerts=alerts,feedback=feedback,adminMfa={'enabled':mfa,'total':total})
    @app.post('/api/admin/feedback')
    @require
    def reply_feedback():
        if not g.user['admin']:raise DomainError('需要管理员权限 / Admin required',403)
        data=payload();limited('feedback-admin:'+g.user['id'],30,300);status=data.get('status');reply=str(data.get('reply','')).strip()
        if status not in ('open','working','resolved','closed') or not 6<=len(reply)<=2000:raise DomainError('状态或回复无效 / Invalid status or reply')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);sensitive(app,db,g.user['id'],data)
            row=db.execute('SELECT * FROM feedback WHERE id=?',(data.get('id'),)).fetchone()
            if not row:raise DomainError('反馈不存在 / Feedback not found',404)
            db.execute('UPDATE feedback SET status=?,reply=?,updated=? WHERE id=?',(status,reply,clock(app),row['id']))
            audit_access(db,g.user['id'],'feedback_reply',row['id'],{'status':status})
            from suite import notify
            notify(db,row['user_id'],'feedback:'+row['id']+':'+uuid.uuid4().hex,'system','反馈有新回复 / Feedback reply',reply,clock(app))
        return jsonify(message='回复已保存并站内通知用户 / Reply saved; user notified in app')
