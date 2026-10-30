"""Independent timer entry point, including a fallback when application/DB startup fails."""
from pathlib import Path
import json,os,sys,time,sqlite3,smtplib,ssl
from email.message import EmailMessage
from email.utils import parseaddr
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))

def fallback(kind):
    values={}
    for line in (root/'.env').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"\'')
    now=int(time.time());dbpath=Path(values.get('DATABASE',str(root/'data/jwb.sqlite3')));marker=dbpath.parent/'.watchdog-alert.json'
    try:
        prior=json.loads(marker.read_text()) if marker.exists() else {}
        if now-prior.get('sent',0)<3600:return
        marker.write_text(json.dumps({'sent':now,'kind':kind}));marker.chmod(0o600)
    except (OSError,ValueError):print('Fallback monitor cannot persist its alert throttle; check service logs',file=sys.stderr);return
    recipients=[]
    if values.get('ADMIN_ALERT_EMAIL'):recipients=[values['ADMIN_ALERT_EMAIL']]
    else:
        try:
            with sqlite3.connect(dbpath.resolve().as_uri()+'?mode=ro',uri=True,timeout=3) as db:recipients=[r[0] for r in db.execute('SELECT email FROM users WHERE admin=1')]
        except sqlite3.Error:recipients=[parseaddr(values.get('MAIL_FROM',''))[1]]
    if values.get('MAIL_MODE','smtp')!='smtp':print('Fallback alert recorded; SMTP mode is not active',file=sys.stderr);return
    for address in dict.fromkeys(recipients):
        if '@' not in address or '\n' in address or '\r' in address:continue
        msg=EmailMessage();msg['From']=values.get('MAIL_FROM','');msg['To']=address;msg['Subject']='JWB · 应用或数据库启动异常 / Startup failure';msg.set_content('The JWB watchdog could not initialize the application/database.\nCategory: '+kind+'\nInspect jwb-cloud and jwb-ops service logs from the server terminal. No account data is included.')
        secure=values.get('SMTP_TLS')=='ssl';factory=smtplib.SMTP_SSL if secure else smtplib.SMTP
        with factory(values.get('SMTP_HOST',''),int(values.get('SMTP_PORT','587')),timeout=15,**({'context':ssl.create_default_context()} if secure else {})) as smtp:
            if not secure:smtp.starttls(context=ssl.create_default_context())
            if values.get('SMTP_USER'):smtp.login(values['SMTP_USER'],values.get('SMTP_PASSWORD',''))
            smtp.send_message(msg)

if __name__=='__main__':
    try:
        from app import create_app
        app=create_app();print(json.dumps(app.extensions['run_ops_checks'](),ensure_ascii=False))
    except Exception as error:
        category=type(error).__name__;print('JWB monitor initialization failed: '+category,file=sys.stderr)
        try:fallback(category)
        except Exception as transport:print('Fallback email could not be sent: '+type(transport).__name__,file=sys.stderr)
        sys.exit(1)
