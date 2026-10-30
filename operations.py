"""Passive runtime checks plus optional loopback heartbeat and deduplicated admin alerts."""
from datetime import datetime,timezone
from email.message import EmailMessage
import json
import os
from pathlib import Path
import shutil
import smtplib
import ssl
import time
import urllib.request
from urllib.parse import urlparse
from records import log_mail
from suite import notify,clock

LABELS={'heartbeat':'应用心跳 / Application heartbeat','database':'数据库 / Database','mail':'邮件发送 / Email delivery','fx':'参考汇率 / Reference rates','backup':'备份 / Backups','disk':'磁盘空间 / Disk space','http':'接口异常 / API failures','maintenance':'维护任务 / Maintenance'}

def send_alert(app,address,subject,body):
    if app.config['MAIL_MODE']=='memory':app.extensions.setdefault('ops_outbox',[]).append({'email':address,'subject':subject,'body':body});return
    if app.config['MAIL_MODE']=='console':return
    msg=EmailMessage();msg['From']=app.config['MAIL_FROM'];msg['To']=address;msg['Subject']=subject;msg.set_content(body)
    secure=app.config['SMTP_TLS']=='ssl';factory=smtplib.SMTP_SSL if secure else smtplib.SMTP
    with factory(app.config['SMTP_HOST'],app.config['SMTP_PORT'],timeout=15,**({'context':ssl.create_default_context()} if secure else {})) as smtp:
        if not secure:smtp.starttls(context=ssl.create_default_context())
        if app.config['SMTP_USER']:smtp.login(app.config['SMTP_USER'],app.config['SMTP_PASSWORD'])
        smtp.send_message(msg)

def run_checks(app,connect,heartbeat=True,send=True):
    now=clock(app);checks={};database=Path(app.config['DATABASE']);backup_dir=Path(app.config['BACKUP_DIR'])
    with connect() as db:
        okay=db.execute('PRAGMA quick_check').fetchone()[0]=='ok';checks['database']=(okay,'SQLite quick_check: '+('ok' if okay else 'failed'))
        mail=list(db.execute('SELECT result,created FROM mail_events WHERE purpose!=? ORDER BY id DESC LIMIT 3',('ops-alert',)))
        bad=len(mail)==3 and all(row['result']=='failed' for row in mail) and mail[0]['created']>=now-3600
        checks['mail']=(not bad,'Recent consecutive mail failures' if bad else 'No recent consecutive transport failures')
        fx=db.execute('SELECT value FROM fx WHERE id=1').fetchone()
        value=json.loads(fx[0]) if fx else {};age=now-datetime.fromisoformat(value['asOf']).timestamp() if value.get('asOf') else None
        checks['fx']=(age is not None and -300<=age<=3*86400,'Reference age: '+(str(max(0,int(age//3600)))+' h' if age is not None else 'no cached reference'))
        failures=db.execute('SELECT COUNT(*) FROM http_failures WHERE created>=?',(now-600,)).fetchone()[0]
        checks['http']=(failures<5,f'{failures} API 5xx responses in 10 minutes')
        maintenance=db.execute("SELECT completed,ok FROM task_heartbeats WHERE name='maintenance'").fetchone()
        checks['maintenance']=(bool(maintenance and maintenance['ok'] and now-maintenance['completed']<=3*3600),'Last maintenance age: '+(str(max(0,now-maintenance['completed']))+' s' if maintenance else 'not recorded'))
    try:
        reports=[]
        for file in list(backup_dir.glob('jwb-auto-*.sqlite3.json'))[-1000:]:
            try:
                report=json.loads(file.read_text());stamp=datetime.fromisoformat(report.get('verifiedAt','')).timestamp()
                if report.get('restoreDrill')=='passed' and file.with_suffix('').is_file():reports.append(stamp)
            except (ValueError,OSError):continue
        last=max(reports) if reports else 0;checks['backup']=(bool(last and now-last<=36*3600),'Last verified automatic backup: '+(datetime.fromtimestamp(last,timezone.utc).isoformat() if last else 'none'))
    except OSError:checks['backup']=(False,'Backup directory is not readable')
    disk=shutil.disk_usage(database.parent);threshold=int(app.config.get('OPS_DISK_MIN_BYTES',512*1024*1024))
    checks['disk']=(disk.free>=threshold and disk.free/disk.total>=.05,f'Free: {disk.free//(1024*1024)} MiB; {disk.free/disk.total:.1%}')
    if heartbeat:
        url=app.config.get('OPS_HEALTH_URL') or 'http://127.0.0.1:8895'+app.config['BASE_PATH']+'/api/health'
        target=urlparse(url)
        if target.scheme!='http' or target.hostname not in ('127.0.0.1','localhost','::1') or target.username or target.password:raise ValueError('Heartbeat must use local loopback HTTP')
        try:
            with urllib.request.urlopen(url,timeout=4) as res:body=json.load(res);ok=res.status==200 and body.get('ok') is True
            checks['heartbeat']=(ok,'Local application responded' if ok else 'Unexpected health response')
        except Exception:checks['heartbeat']=(False,'Local application did not respond successfully')
    due=[]
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        admins=[dict(r) for r in db.execute('SELECT id,email FROM users u WHERE admin=1 AND NOT EXISTS(SELECT 1 FROM user_flags f WHERE f.user_id=u.id AND f.disabled=1)')]
        for name,(ok,detail) in checks.items():
            previous=db.execute('SELECT * FROM ops_checks WHERE name=?',(name,)).fetchone()
            db.execute('INSERT OR REPLACE INTO ops_checks VALUES(?,?,?,?,?)',(name,now,int(ok),detail,now if ok else previous['last_success'] if previous else None))
            alert=db.execute('SELECT * FROM ops_alerts WHERE name=?',(name,)).fetchone();active=not ok
            first=alert['first_seen'] if alert and alert['active'] and active else now
            sent=alert['last_sent'] if alert else 0
            db.execute('INSERT OR REPLACE INTO ops_alerts VALUES(?,?,?,?,?,?)',(name,int(active),first,now,sent,detail))
            if active and (not alert or not alert['active'] or now-sent>=3600):
                for admin in admins:notify(db,admin['id'],'ops:'+name+':'+str(now//3600),'system','运行异常 / Operational alert · '+LABELS[name],detail,now)
                if send and now-sent>=3600:
                    due.append((name,detail));db.execute('UPDATE ops_alerts SET last_sent=? WHERE name=?',(now,name))
            elif not active and alert and alert['active']:
                for admin in admins:notify(db,admin['id'],'ops-resolved:'+name+':'+str(now),'system','异常已恢复 / Operational check recovered · '+LABELS[name],detail,now)
    if due:
        configured=os.getenv('ADMIN_ALERT_EMAIL','').strip().lower()
        recipients=[configured] if configured else list(dict.fromkeys(a['email'] for a in admins))
        recipients=[r for r in recipients if '@' in r and '\n' not in r and '\r' not in r]
        body='JWB Simulation operational alerts\n\n'+'\n'.join(LABELS[name]+': '+detail for name,detail in due)+'\n\nCheck the private administration console. No passwords or account balances are included.'
        for address in recipients:
            try:
                send_alert(app,address,'JWB · 运行异常提醒 / Operational alert',body)
                with connect() as db:log_mail(db,address,'ops-alert','accepted')
            except Exception:
                with connect() as db:log_mail(db,address,'ops-alert','failed','transport')
    return {'checked':now,'checks':{name:{'ok':okay,'detail':detail} for name,(okay,detail) in checks.items()},'activeAlerts':sum(not v[0] for v in checks.values())}
