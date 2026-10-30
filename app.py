"""JWB public simulation server. Run behind HTTPS; never processes real money."""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
import re
import secrets
import smtplib
import sqlite3
import ssl
import threading
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from email.message import EmailMessage
from functools import wraps
from contextlib import contextmanager
from pathlib import Path
from flask import Flask, request, jsonify, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers import Response
from werkzeug.utils import redirect
from domain import CATALOG, CURRENCIES, DomainError, empty_state, execute, assess, money, quantize, audit_log
from records import init_records, record_command, log_mail
from admin_api import register_admin, audit_access
from suite import init_suite,roll_bills,capture_operation,clock
from suite_api import register_suite
from growth import init_growth,maintain_lifecycle,execute_extended,capture_extended,lifecycle_defaults,VERSION
from growth_security import init_security,register_security,enabled as mfa_enabled,verify_factor,sensitive,mac
from growth_api import register_growth

ROOT = Path(__file__).parent

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('\"\''))

load_env()

class PathPrefix:
    """Mount without trusting client forwarding headers or changing the main site."""
    def __init__(self, application, prefix):
        self.application, self.prefix = application, prefix
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path == self.prefix:
            query = environ.get('QUERY_STRING', '')
            return redirect(self.prefix+'/' + ('?'+query if query else ''), code=308)(environ, start_response)
        if not path.startswith(self.prefix+'/'):
            return Response('Not found', status=404)(environ, start_response)
        environ = environ.copy()
        environ['SCRIPT_NAME'] = environ.get('SCRIPT_NAME','') + self.prefix
        environ['PATH_INFO'] = path[len(self.prefix):]
        return self.application(environ, start_response)

def create_app(overrides=None):
    app = Flask(__name__, static_folder=None)
    app.config.update(SECRET_KEY=os.getenv('APP_SECRET', ''), DATABASE=os.getenv('DATABASE', str(ROOT/'data/jwb.sqlite3')),
        BASE_PATH=os.getenv('BASE_PATH','').rstrip('/'), PUBLIC_ORIGIN=os.getenv('PUBLIC_ORIGIN','https://localhost'), COOKIE_SECURE=os.getenv('COOKIE_SECURE','true').lower()=='true',
        MAIL_IP_HOURLY_LIMIT=max(1,int(os.getenv('MAIL_IP_HOURLY_LIMIT','60'))),
        MAIL_EMAIL_HOURLY_LIMIT=max(1,int(os.getenv('MAIL_EMAIL_HOURLY_LIMIT','6'))),
        MAIL_RESEND_SECONDS=max(30,int(os.getenv('MAIL_RESEND_SECONDS','60'))),
        MAIL_MODE=os.getenv('MAIL_MODE','smtp'), SMTP_HOST=os.getenv('SMTP_HOST',''), SMTP_PORT=int(os.getenv('SMTP_PORT','587')),
        SMTP_USER=os.getenv('SMTP_USER',''), SMTP_PASSWORD=os.getenv('SMTP_PASSWORD',''), MAIL_FROM=os.getenv('MAIL_FROM',''),
        SMTP_TLS=os.getenv('SMTP_TLS','starttls'), OXR_APP_ID=os.getenv('OXR_APP_ID',''), FX_REFRESH_SECONDS=max(15,int(os.getenv('FX_REFRESH_SECONDS','3600'))), TESTING=False, MAX_CONTENT_LENGTH=2*1024*1024)
    app.config['BACKUP_DIR']=os.getenv('BACKUP_DIR','/www/backup/jwb-cloud')
    app.config['OPS_HEALTH_URL']=os.getenv('OPS_HEALTH_URL','')
    app.config['OPS_DISK_MIN_BYTES']=max(64,int(os.getenv('OPS_DISK_MIN_MB','512')))*1024*1024
    if overrides: app.config.update(overrides)
    if app.config['BASE_PATH'] and not re.fullmatch(r'/[a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*',app.config['BASE_PATH']): raise RuntimeError('Invalid BASE_PATH')
    if len(app.config['SECRET_KEY']) < 32 or app.config['SECRET_KEY'].startswith('REPLACE_'): raise RuntimeError('Set APP_SECRET to at least 32 random characters')
    if app.config['SMTP_TLS'] not in ('ssl','starttls'): raise RuntimeError('SMTP_TLS must be ssl or starttls')
    if app.config['MAIL_MODE'] not in ('memory','console','smtp'): raise RuntimeError('Invalid MAIL_MODE')
    if app.config['COOKIE_SECURE'] and app.config['MAIL_MODE']=='console': raise RuntimeError('Console mail is for local development with COOKIE_SECURE=false only')
    if not app.config['TESTING'] and app.config['MAIL_MODE'] == 'memory': raise RuntimeError('Memory mail is test-only')
    if not app.config['TESTING'] and app.config['COOKIE_SECURE'] and not app.config['PUBLIC_ORIGIN'].startswith('https://'):
        raise RuntimeError('Production PUBLIC_ORIGIN must use HTTPS')
    if os.getenv('TRUST_PROXY')=='true': app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    app.extensions['test_inbox']=[]
    fx_lock=threading.Lock()
    Path(app.config['DATABASE']).parent.mkdir(mode=0o700,parents=True,exist_ok=True)

    @contextmanager
    def connect():
        db=sqlite3.connect(app.config['DATABASE'],timeout=20,isolation_level=None)
        db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA busy_timeout=20000')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
    with connect() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,admin INTEGER DEFAULT 0,created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS accounts(user_id TEXT PRIMARY KEY REFERENCES users(id),state TEXT NOT NULL,revision INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS codes(email TEXT,purpose TEXT,digest TEXT,expires INTEGER,attempts INTEGER,created INTEGER,PRIMARY KEY(email,purpose));
        CREATE TABLE IF NOT EXISTS limits(key TEXT PRIMARY KEY,count INTEGER,until INTEGER);
        CREATE TABLE IF NOT EXISTS commands(user_id TEXT,key TEXT,hash TEXT,response TEXT,status INTEGER,PRIMARY KEY(user_id,key));
        CREATE TABLE IF NOT EXISTS quotes(id TEXT PRIMARY KEY,user_id TEXT,payload TEXT,expires INTEGER,used INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY,value TEXT);
        INSERT OR IGNORE INTO settings VALUES(1,'{"public_registration":true,"min_income":5000}');
        CREATE TABLE IF NOT EXISTS fx(id INTEGER PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT,event TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS session_details(token TEXT PRIMARY KEY REFERENCES sessions(token) ON DELETE CASCADE,id TEXT UNIQUE,created INTEGER,last_seen INTEGER,agent TEXT,network TEXT);
        CREATE TABLE IF NOT EXISTS security_events(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id TEXT REFERENCES users(id),event TEXT,created INTEGER);
        CREATE TABLE IF NOT EXISTS preferences(user_id TEXT PRIMARY KEY REFERENCES users(id),guide_hidden INTEGER DEFAULT 0,ledger_seen INTEGER DEFAULT 0);
        ''')
        init_records(db)
        init_suite(db)
        init_growth(db)
        init_security(db)
    os.chmod(app.config['DATABASE'],0o600)

    def digest(value): return hmac.new(app.config['SECRET_KEY'].encode(),value.encode(),hashlib.sha256).hexdigest()
    def settings(db): return json.loads(db.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])
    def limited(key, maximum, seconds):
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM limits WHERE key=?',(key,)).fetchone();now=int(time.time())
            if row and row['until']>now and row['count']>=maximum:
                error=DomainError(f'请求过于频繁，请在 {row["until"]-now} 秒后重试 / Too many attempts; retry in {row["until"]-now} seconds',429)
                error.retry_after=row['until']-now
                raise error
            count=row['count']+1 if row and row['until']>now else 1
            until=row['until'] if row and row['until']>now else now+seconds
            db.execute('INSERT OR REPLACE INTO limits VALUES(?,?,?)',(key,count,until));db.commit()
    def reserve_mail(address):
        """Check all quotas before changing any; denied retries never consume quota."""
        cooldown=app.config['MAIL_RESEND_SECONDS']
        rules=[('mail:'+address,1,cooldown,'email_cooldown'),
               ('mail-hour:'+address,app.config['MAIL_EMAIL_HOURLY_LIMIT'],3600,'email_hourly'),
               ('mail-ip:'+str(request.remote_addr),app.config['MAIL_IP_HOURLY_LIMIT'],3600,'ip_hourly')]
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');now=int(time.time());entries=[];blocked=[]
            for key,maximum,seconds,reason in rules:
                row=db.execute('SELECT * FROM limits WHERE key=?',(key,)).fetchone()
                active=row and row['until']>now
                if active and row['count']>=maximum:blocked.append((row['until']-now,reason))
                entries.append((key,row['count']+1 if active else 1,row['until'] if active else now+seconds))
            if blocked:
                retry,reason=max(blocked)
                labels={'email_cooldown':('此邮箱需等待发送间隔','This email is in its resend cooldown'),
                        'email_hourly':('此邮箱已达到每小时发送上限','This email reached its hourly limit'),
                        'ip_hourly':('此网络已达到每小时发送上限','This network reached its hourly limit')}
                zh,en=labels[reason]
                error=DomainError(f'{zh}，请在 {retry} 秒后重试 / {en}; retry in {retry} seconds',429)
                error.retry_after=retry;error.rate_limit=reason
                raise error
            db.executemany('INSERT OR REPLACE INTO limits VALUES(?,?,?)',entries)
        return cooldown

    def email(value):
        value=str(value or '').strip().lower()
        if len(value)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise DomainError('请输入有效邮箱 / Invalid email address')
        return value
    def password(value):
        if not isinstance(value,str) or not 10<=len(value)<=128: raise DomainError('密码须为 10–128 个字符 / Password must be 10–128 characters')
        return value
    def payload():
        data=request.get_json(silent=True)
        if not isinstance(data,dict): raise DomainError('需要 JSON 对象 / JSON object required')
        if any(not isinstance(k,str) or isinstance(v,(dict,list)) for k,v in data.items()): raise DomainError('无效参数 / Invalid parameters')
        return data
    def identity():
        raw=request.cookies.get('jwb_session','')
        with connect() as db:
            row=db.execute('SELECT users.* FROM users JOIN sessions ON users.id=sessions.user_id WHERE sessions.token=? AND sessions.expires>? AND NOT EXISTS(SELECT 1 FROM user_flags f WHERE f.user_id=users.id AND f.disabled=1)',(digest(raw),int(time.time()))).fetchone() if raw else None
            if row: db.execute('UPDATE session_details SET last_seen=? WHERE token=? AND last_seen<?',(int(time.time()),digest(raw),int(time.time())-300))
        return dict(row) if row else None
    def require(fn):
        @wraps(fn)
        def wrapper(*args,**kwargs):
            g.user=identity()
            if not g.user: raise DomainError('请先登录 / Sign in first',401)
            if request.method!='GET' and not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),digest('csrf:'+request.cookies.get('jwb_session',''))):
                raise DomainError('会话校验失败，请刷新 / Session verification failed',403)
            return fn(*args,**kwargs)
        return wrapper
    def session_response(user,mfa_verified=False):
        raw=secrets.token_urlsafe(40)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            fresh=db.execute('SELECT * FROM users WHERE id=?',(user['id'],)).fetchone()
            if db.execute('SELECT 1 FROM user_flags WHERE user_id=? AND disabled=1',(user['id'],)).fetchone():raise DomainError('账户已停用，请联系站点管理员 / Account disabled; contact the site administrator',403)
            if not fresh or fresh['password']!=user['password'] or fresh['email']!=user['email']:
                raise DomainError('账户信息已变更，请重新登录 / Account changed; please sign in again',409)
            if not mfa_verified and mfa_enabled(db,user['id']):
                challenge=secrets.token_urlsafe(32)
                db.execute('DELETE FROM mfa_challenges WHERE expires<?',(clock(app),))
                db.execute('INSERT INTO mfa_challenges VALUES(?,?,?,?)',(mac(app,'challenge:'+challenge),user['id'],clock(app)+300,mac(app,fresh['password'])))
                return jsonify(mfaRequired=True,challenge=challenge)
            db.execute('DELETE FROM sessions WHERE expires<=?',(int(time.time()),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(digest(raw),user['id'],int(time.time())+7*86400))
            try:
                address=ipaddress.ip_address(request.remote_addr)
                network=str(ipaddress.ip_network(f'{address}/{24 if address.version==4 else 64}',strict=False))
            except ValueError: network='Unknown'
            now=int(time.time())
            db.execute('INSERT INTO session_details VALUES(?,?,?,?,?,?)',(digest(raw),secrets.token_urlsafe(18),now,now,request.user_agent.string[:300],network))
            db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(user['id'],'signed_in',now))
        res=jsonify(user={k:user[k] for k in ('id','email','admin')},csrf=digest('csrf:'+raw))
        res.set_cookie('jwb_session',raw,max_age=7*86400,secure=app.config['COOKIE_SECURE'],httponly=True,samesite='Lax',path=app.config['BASE_PATH']+'/')
        return res
    def live_session(db):
        valid=db.execute('SELECT 1 FROM sessions s WHERE s.token=? AND s.user_id=? AND s.expires>? AND NOT EXISTS(SELECT 1 FROM user_flags f WHERE f.user_id=s.user_id AND f.disabled=1)',(digest(request.cookies.get('jwb_session','')),g.user['id'],int(time.time()))).fetchone()
        if not valid:raise DomainError('会话已撤销，请重新登录 / Session revoked; sign in again',401)
    def mail_ready(): return app.config['MAIL_MODE'] in ('memory','console') or bool(app.config['SMTP_HOST'] and app.config['MAIL_FROM'])
    def transport_code(address,code,purpose):
        if app.config['MAIL_MODE']=='memory': app.extensions['test_inbox'].append(dict(email=address,code=code,purpose=purpose));return
        if app.config['MAIL_MODE']=='console': app.logger.warning('DEV ONLY OTP %s %s: %s',address,purpose,code);return
        msg=EmailMessage();msg['Subject']='JWB Demo · 邮箱验证码';msg['From']=app.config['MAIL_FROM'];msg['To']=address
        msg.set_content(f'JWB 模拟体验平台 / JWB simulation\n验证码 / Verification code: {code}\n10 分钟内有效。请勿转发。\nValid for 10 minutes. Do not share this code.\n本平台不提供真实银行业务。No real banking services.')
        factory=smtplib.SMTP_SSL if app.config['SMTP_TLS']=='ssl' else smtplib.SMTP
        options={'context':ssl.create_default_context()} if app.config['SMTP_TLS']=='ssl' else {}
        with factory(app.config['SMTP_HOST'],app.config['SMTP_PORT'],timeout=15,**options) as smtp:
            if app.config['SMTP_TLS']=='starttls': smtp.starttls(context=ssl.create_default_context())
            if app.config['SMTP_USER']: smtp.login(app.config['SMTP_USER'],app.config['SMTP_PASSWORD'])
            smtp.send_message(msg)
    def send_code(address,code,purpose):
        try:transport_code(address,code,purpose)
        except Exception as error:
            category='authentication' if isinstance(error,smtplib.SMTPAuthenticationError) else 'certificate' if isinstance(error,ssl.SSLError) else 'recipient' if isinstance(error,smtplib.SMTPRecipientsRefused) else 'timeout' if isinstance(error,TimeoutError) else 'transport'
            with connect() as db:log_mail(db,address,purpose,'failed',category)
            raise
        with connect() as db:log_mail(db,address,purpose,'accepted')
    def verify_code(db,address,purpose,code,consume=True):
        row=db.execute('SELECT * FROM codes WHERE email=? AND purpose=?',(address,purpose)).fetchone()
        if not row or row['expires']<time.time() or row['attempts']>=5: raise DomainError('验证码无效、已过期或尝试次数过多 / Invalid or expired code')
        if not hmac.compare_digest(row['digest'],digest(f'{address}:{purpose}:{code}')):
            db.execute('UPDATE codes SET attempts=attempts+1 WHERE email=? AND purpose=?',(address,purpose));db.commit()
            raise DomainError('验证码错误 / Incorrect code')
        if consume: db.execute('DELETE FROM codes WHERE email=? AND purpose=?',(address,purpose))
    @app.before_request
    def origin_guard():
        if (ROOT/'.update-in-progress').exists() and request.path.startswith('/api/') and request.path!='/api/health':raise DomainError('系统正在更新，请稍后刷新 / System update in progress; refresh shortly',503)
        if request.path.startswith('/api/') and request.method!='GET':
            if request.headers.get('X-JWB-Client')!='web': raise DomainError('请求校验失败 / Request verification failed',403)
            if request.headers.get('Origin') and request.headers['Origin']!=app.config['PUBLIC_ORIGIN']: raise DomainError('来源不允许 / Origin not allowed',403)
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='same-origin'
        response.headers['X-Frame-Options']='DENY';response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
        if app.config['COOKIE_SECURE']: response.headers['Strict-Transport-Security']='max-age=31536000'
        if request.path.startswith('/api/') or request.path in ('/admin','/admin/'): response.headers['Cache-Control']='no-store'
        if response.status_code>=500 and request.path.startswith('/api/') and request.path!='/api/health' and not (ROOT/'.update-in-progress').exists():
            try:
                with connect() as db:
                    db.execute('INSERT INTO http_failures VALUES(?)',(int(time.time()),));db.execute('DELETE FROM http_failures WHERE created<?',(int(time.time())-86400,))
            except Exception:pass
        return response
    @app.errorhandler(DomainError)
    def domain_error(error):
        body={'message':error.message}
        retry=getattr(error,'retry_after',None)
        if retry:body['retryAfter']=retry
        if getattr(error,'rate_limit',None):body['rateLimit']=error.rate_limit
        response=jsonify(body);response.status_code=error.status
        if retry:response.headers['Retry-After']=str(retry)
        return response
    @app.errorhandler(413)
    def too_large(error): return jsonify(message='请求内容过大 / Request too large'),413
    @app.errorhandler(500)
    def server_error(error):
        reference=secrets.token_hex(4)
        app.logger.error('Request failure reference=%s path=%s',reference,request.path)
        return jsonify(message=f'服务暂时异常，请稍后刷新并核对操作结果。错误编号 {reference} / Service unavailable; refresh and check the result. Reference {reference}'),500
    @app.get('/')
    def index(): return send_from_directory(ROOT/'static','index.html')
    @app.get('/assets/<name>')
    def asset(name):
        if name not in ('cloud.js','cloud.css','admin.js','admin.css','fonts.css','suite.js','suite.css','demo.js','ui.js','ui.css','growth.js','growth.css','admin-growth.js','core.js','tailwind-runtime.js','jspdf.umd.min.js','jwb-sans-sc.woff','jwb-inter.woff'): return '',404
        response=send_from_directory(ROOT/'static',name,max_age=31536000 if request.args.get('v')==VERSION else None)
        if request.args.get('v')==VERSION:response.headers['Cache-Control']='public, max-age=31536000, immutable'
        return response
    @app.get('/api/catalog')
    def catalog(): return jsonify(CATALOG)
    @app.get('/api/auth/me')
    def me():
        user=identity()
        with connect() as db: s=settings(db)
        return jsonify(user={k:user[k] for k in ('id','email','admin')} if user else None,csrf=digest('csrf:'+request.cookies.get('jwb_session','')) if user else None,mailReady=mail_ready(),publicRegistration=s['public_registration'])
    @app.post('/api/auth/request-code')
    def request_code():
        data=payload();address=email(data.get('email'));purpose=data.get('purpose')
        if purpose not in ('register','login','reset'): raise DomainError('无效验证码用途 / Invalid code purpose')
        if not mail_ready(): raise DomainError('管理员尚未配置发信服务 / Email delivery has not been configured',503)
        with connect() as db:
            user=db.execute('SELECT id FROM users WHERE email=?',(address,)).fetchone()
            if purpose=='register' and not settings(db)['public_registration']: raise DomainError('注册暂时关闭 / Registration disabled',403)
        cooldown=reserve_mail(address)
        if (purpose=='register' and user) or (purpose!='register' and not user):
            return jsonify(message='如邮箱符合条件，验证码将发送 / A code will be sent if the address is eligible',retryAfter=cooldown)
        with connect() as db:
            code=f'{secrets.randbelow(1000000):06}'
            db.execute('INSERT OR REPLACE INTO codes VALUES(?,?,?,?,?,?)',(address,purpose,digest(f'{address}:{purpose}:{code}'),int(time.time())+600,0,int(time.time())))
        try: send_code(address,code,purpose)
        except Exception:
            app.logger.warning('Mail transport failed; see private delivery category')
            with connect() as db: db.execute('DELETE FROM codes WHERE email=? AND purpose=?',(address,purpose))
            error=DomainError(f'邮件发送失败，请在 {cooldown} 秒后重试 / Email delivery failed; retry in {cooldown} seconds',503)
            error.retry_after=cooldown
            raise error
        return jsonify(message='如邮箱符合条件，验证码将发送 / A code will be sent if the address is eligible',retryAfter=cooldown)
    @app.post('/api/auth/register')
    def register():
        data=payload();address=email(data.get('email'));pw=password(data.get('password'))
        limited('register:'+str(request.remote_addr),10,3600)
        hashed=generate_password_hash(pw)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not settings(db)['public_registration']: raise DomainError('注册暂时关闭 / Registration disabled',403)
            if db.execute('SELECT id FROM users WHERE email=?',(address,)).fetchone(): raise DomainError('无法注册，请登录或找回密码 / Unable to register; sign in or reset your password',409)
            verify_code(db,address,'register',str(data.get('code','')))
            uid=secrets.token_hex(16);db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,address,hashed,0,int(time.time())))
            db.execute('INSERT INTO accounts VALUES(?,?,0)',(uid,json.dumps(empty_state())));db.commit()
            user=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        return session_response(user)
    @app.post('/api/auth/login')
    def login():
        data=payload();address=email(data.get('email'));limited('login-ip:'+str(request.remote_addr),30,900);limited('login:'+address,12,900)
        with connect() as db: user=db.execute('SELECT * FROM users WHERE email=?',(address,)).fetchone()
        # Always evaluate a scrypt hash to reduce account enumeration through timing.
        stored=user['password'] if user else app.config['DUMMY_HASH']
        if not check_password_hash(stored,str(data.get('password',''))[:129]) or not user: raise DomainError('邮箱或密码错误 / Invalid email or password',401)
        return session_response(user)
    @app.post('/api/auth/login-code')
    def login_code():
        data=payload();address=email(data.get('email'));limited('code-login:'+str(request.remote_addr),30,900)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');verify_code(db,address,'login',str(data.get('code','')))
            user=db.execute('SELECT * FROM users WHERE email=?',(address,)).fetchone();db.commit()
        if not user: raise DomainError('邮箱或验证码错误 / Invalid email or code',401)
        return session_response(user)
    @app.post('/api/auth/reset-password')
    def reset_password():
        data=payload();address=email(data.get('email'));raw=password(data.get('password'))
        limited('reset:'+str(request.remote_addr),15,900)
        pw=generate_password_hash(raw)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');verify_code(db,address,'reset',str(data.get('code','')))
            row=db.execute('SELECT id FROM users WHERE email=?',(address,)).fetchone()
            if not row: raise DomainError('无法重置密码 / Unable to reset password')
            verify_factor(app,db,row['id'],data.get('factor'))
            db.execute('UPDATE users SET password=? WHERE id=?',(pw,row['id']));db.execute('DELETE FROM sessions WHERE user_id=?',(row['id'],))
            db.execute('DELETE FROM codes WHERE email=?',(address,))
            db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(row['id'],'password_reset',int(time.time())));db.commit()
        return jsonify(message='密码已更新，所有设备已退出，请重新登录 / Password updated; all sessions revoked')
    @app.post('/api/auth/logout')
    @require
    def logout():
        data=payload()
        with connect() as db:
            if data.get('allDevices'): db.execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],))
            else: db.execute('DELETE FROM sessions WHERE token=?',(digest(request.cookies.get('jwb_session','')),))
        res=jsonify(message='已退出登录 / Signed out');res.delete_cookie('jwb_session',path=app.config['BASE_PATH']+'/');return res

    def security_event(db,event):
        db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(g.user['id'],event,int(time.time())))
    def confirm_password(db,data):
        verify_factor(app,db,g.user['id'],data.get('factor'))
        user=db.execute('SELECT * FROM users WHERE id=?',(g.user['id'],)).fetchone()
        if not user or user['email']!=g.user['email'] or not check_password_hash(user['password'],str(data.get('currentPassword',''))[:129]):
            raise DomainError('当前密码不正确或账户已变更 / Current password is incorrect or account changed',400)
        return user
    @app.get('/api/auth/sessions')
    @require
    def list_sessions():
        current=digest(request.cookies.get('jwb_session',''))
        with connect() as db:
            rows=db.execute('SELECT s.token,s.expires,d.id,d.created,d.last_seen,d.agent,d.network FROM sessions s LEFT JOIN session_details d ON d.token=s.token WHERE s.user_id=? AND s.expires>? ORDER BY COALESCE(d.last_seen,0) DESC',(g.user['id'],int(time.time()))).fetchall()
            events=[dict(row) for row in db.execute('SELECT event,created FROM security_events WHERE user_id=? ORDER BY id DESC LIMIT 20',(g.user['id'],))]
        return jsonify(sessions=[{**{k:row[k] for k in ('id','created','last_seen','agent','network','expires')},'current':row['token']==current} for row in rows],events=events)
    @app.post('/api/auth/revoke-session')
    @require
    def revoke_session():
        data=payload();limited('session-action:'+g.user['id'],30,60)
        current=digest(request.cookies.get('jwb_session',''))
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if data.get('others') is True:
                db.execute('DELETE FROM sessions WHERE user_id=? AND token!=?',(g.user['id'],current))
            else:
                row=db.execute('SELECT s.token FROM sessions s JOIN session_details d ON d.token=s.token WHERE s.user_id=? AND d.id=?',(g.user['id'],data.get('id'))).fetchone()
                if not row: raise DomainError('设备会话已失效 / Device session no longer exists',404)
                if row['token']==current: raise DomainError('请使用退出当前设备 / Use sign out for this device')
                db.execute('DELETE FROM sessions WHERE token=?',(row['token'],))
            verify_factor(app,db,g.user['id'],data.get('factor'))
            security_event(db,'sessions_revoked')
        return jsonify(message='其他设备会话已撤销 / Other device sessions revoked')
    @app.post('/api/auth/change-password')
    @require
    def change_password():
        data=payload();limited('security:'+g.user['id'],10,900)
        new=password(data.get('password'));hashed=generate_password_hash(new)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');user=confirm_password(db,data)
            if check_password_hash(user['password'],new): raise DomainError('新密码不能与当前密码相同 / Choose a different new password')
            db.execute('UPDATE users SET password=? WHERE id=?',(hashed,g.user['id']))
            db.execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],))
            db.execute('DELETE FROM codes WHERE email=?',(g.user['email'],))
            security_event(db,'password_changed')
        res=jsonify(message='密码已更新，请重新登录；所有设备均已退出 / Password updated; all devices signed out. Sign in again')
        res.delete_cookie('jwb_session',path=app.config['BASE_PATH']+'/');return res
    @app.post('/api/auth/change-email/request-code')
    @require
    def change_email_code():
        data=payload();limited('security-mail:'+g.user['id'],20,900)
        with connect() as db: confirm_password(db,data)
        target=data.get('target')
        if target not in ('old','new'): raise DomainError('请选择验证邮箱 / Choose the email to verify')
        address=g.user['email'] if target=='old' else email(data.get('newEmail'))
        if target=='new' and address==g.user['email']: raise DomainError('新邮箱与当前邮箱相同 / New email matches the current address')
        if not mail_ready(): raise DomainError('邮件服务暂不可用 / Email service unavailable',503)
        cooldown=reserve_mail(address)
        purpose='change-'+target+':'+g.user['id']
        code=f'{secrets.randbelow(1000000):06}'
        with connect() as db:
            if target=='new' and db.execute('SELECT id FROM users WHERE email=?',(address,)).fetchone():
                return jsonify(message='如邮箱符合条件，验证码将发送 / A code will be sent if the address is eligible',retryAfter=cooldown)
            db.execute('INSERT OR REPLACE INTO codes VALUES(?,?,?,?,?,?)',(address,purpose,digest(f'{address}:{purpose}:{code}'),int(time.time())+600,0,int(time.time())))
        try: send_code(address,code,purpose)
        except Exception:
            app.logger.warning('Email change transport failed; see private delivery category')
            with connect() as db: db.execute('DELETE FROM codes WHERE email=? AND purpose=?',(address,purpose))
            error=DomainError('邮件发送失败，请等待倒计时后重试 / Email delivery failed; retry after the countdown',503);error.retry_after=cooldown;raise error
        return jsonify(message='如邮箱符合条件，验证码将发送 / A code will be sent if the address is eligible',retryAfter=cooldown)
    @app.post('/api/auth/change-email')
    @require
    def change_email():
        data=payload();limited('security:'+g.user['id'],10,900);address=email(data.get('newEmail'))
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');confirm_password(db,data)
            if address==g.user['email']: raise DomainError('新邮箱与当前邮箱相同 / New email matches the current address')
            if db.execute('SELECT id FROM users WHERE email=?',(address,)).fetchone(): raise DomainError('无法使用此邮箱 / This email cannot be used',409)
            verify_code(db,g.user['email'],'change-old:'+g.user['id'],str(data.get('oldCode','')),False)
            verify_code(db,address,'change-new:'+g.user['id'],str(data.get('newCode','')),False)
            db.execute('UPDATE users SET email=? WHERE id=?',(address,g.user['id']))
            db.execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],))
            db.execute('DELETE FROM codes WHERE email IN (?,?)',(address,g.user['email']))
            security_event(db,'email_changed')
        res=jsonify(message='邮箱已更新，请使用新邮箱重新登录 / Email updated; sign in with your new address')
        res.delete_cookie('jwb_session',path=app.config['BASE_PATH']+'/');return res
    @app.get('/api/experience')
    @require
    def experience():
        with connect() as db:
            pref=db.execute('SELECT guide_hidden,ledger_seen FROM preferences WHERE user_id=?',(g.user['id'],)).fetchone()
            value,_=account(db,g.user['id'])
            events={row[0] for row in db.execute("SELECT DISTINCT event FROM audit WHERE user_id=? AND id>COALESCE((SELECT MAX(id) FROM audit WHERE user_id=? AND event='core/reset:200'),0) AND event IN ('treasury/wire-in:200','pos/authorize:200')",(g.user['id'],g.user['id']))}
        return jsonify(hidden=bool(pref and pref['guide_hidden']),steps={'funds':'treasury/wire-in:200' in events,'card':bool(value['cards']),'purchase':'pos/authorize:200' in events,'ledger':bool(pref and pref['ledger_seen'])})
    @app.post('/api/experience')
    @require
    def save_experience():
        data=payload()
        if any(key not in ('hidden','ledgerSeen') or not isinstance(val,bool) for key,val in data.items()): raise DomainError('无效偏好设置 / Invalid preference')
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');db.execute('INSERT OR IGNORE INTO preferences(user_id) VALUES(?)',(g.user['id'],))
            if 'hidden' in data: db.execute('UPDATE preferences SET guide_hidden=? WHERE user_id=?',(int(data['hidden']),g.user['id']))
            if data.get('ledgerSeen'): db.execute('UPDATE preferences SET ledger_seen=1 WHERE user_id=?',(g.user['id'],))
        return jsonify(saved=True)
    def account(db,uid):
        row=db.execute('SELECT * FROM accounts WHERE user_id=?',(uid,)).fetchone()
        return json.loads(row['state']),row['revision']
    def maintain(db,uid,now):
        value,revision=account(db,uid);original=json.dumps(value,sort_keys=True)
        maintain_lifecycle(db,uid,value,now)
        roll_bills(db,uid,value,now)
        if json.dumps(value,sort_keys=True)!=original:db.execute('UPDATE accounts SET state=?,revision=? WHERE user_id=?',(json.dumps(value),revision+1,uid))
    def maintain_all():
        with connect() as db:users=[r['id'] for r in db.execute('SELECT id FROM users')]
        for uid in users:
            with connect() as db:db.execute('BEGIN IMMEDIATE');maintain(db,uid,clock(app))
        with connect() as db:db.execute('INSERT OR REPLACE INTO task_heartbeats VALUES(?,?,?,?)',('maintenance',clock(app),1,'Accounts processed: '+str(len(users))))
        return len(users)
    app.extensions['run_maintenance']=maintain_all
    @app.get('/api/state')
    @require
    def state():
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');maintain(db,g.user['id'],clock(app));value,revision=account(db,g.user['id'])
            unread=db.execute('SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0',(g.user['id'],)).fetchone()[0]
        return jsonify(db=value,revision=revision,unread=unread)

    def rates():
        if app.config.get('FX_TEST_PROVIDER'): return app.config['FX_TEST_PROVIDER']()
        with fx_lock:
            with connect() as db: row=db.execute('SELECT value FROM fx WHERE id=1').fetchone()
            cached=json.loads(row[0]) if row else None
            if cached and time.time()-datetime.fromisoformat(cached['asOf']).timestamp()<=7*86400 and time.time()-cached['fetchedAt']<app.config['FX_REFRESH_SECONDS']: return cached
            providers=[('ExchangeRate-API open reference','https://open.er-api.com/v6/latest/USD'),('Frankfurter / ECB reference','https://api.frankfurter.dev/v1/latest?base=USD')]
            if app.config['OXR_APP_ID']:
                from urllib.parse import urlencode
                providers.insert(0,('Open Exchange Rates subscription reference','https://openexchangerates.org/api/latest.json?'+urlencode({'app_id':app.config['OXR_APP_ID']})))
            for source,url in providers:
                try:
                    req=urllib.request.Request(url,headers={'User-Agent':'JWB-Demo/5.0'})
                    with urllib.request.urlopen(req,timeout=8) as response: data=json.load(response)
                    if data.get('base',data.get('base_code','USD'))!='USD': raise ValueError('Unexpected rate base')
                    table=data['rates'];table['USD']=1
                    normalized={c:1/float(table[c]) for c in CURRENCIES}
                    if not all(0<float(v)<1e6 for v in normalized.values()): raise ValueError('Bad rate')
                    epoch=data.get('timestamp') or data.get('time_last_update_unix') or datetime.fromisoformat(data['date']).replace(tzinfo=timezone.utc).timestamp()
                    if abs(time.time()-epoch)>7*86400: raise ValueError('Stale rate')
                    value=dict(ratesToUSD=normalized,source=source,asOf=datetime.fromtimestamp(epoch,timezone.utc).isoformat(),fetchedAt=time.time(),mode='reference',stale=False)
                    with connect() as db: db.execute('INSERT OR REPLACE INTO fx VALUES(1,?)',(json.dumps(value),))
                    return value
                except Exception: app.logger.info('Reference provider unavailable: %s',source)
            if cached and time.time()-datetime.fromisoformat(cached['asOf']).timestamp()<=7*86400 and time.time()-cached['fetchedAt']<86400: return dict(cached,stale=True)
            raise DomainError('汇率服务暂不可用，换汇和外币消费已暂停 / Rates unavailable; FX and foreign purchases paused',503)
    def operation_rates(data,route):
        if route in ('pos/refund','cards/close','cards/replace','core/reset'):return {'USD':1}
        # USD-only commands continue to work during provider outages.
        try: return rates()['ratesToUSD']
        except DomainError:
            if route in ('treasury/fx-swap','treasury/accrue-apy') or data.get('currency','USD')!='USD': raise
            return {'USD':1}
    @app.get('/api/rates')
    @require
    def get_rates(): return jsonify(rates())
    @app.post('/api/quotes')
    @require
    def quote():
        limited('quote:'+g.user['id'],120,60)
        data=payload();source=data.get('from');target=data.get('to');amount=money(data.get('amount'),source)
        if target not in CURRENCIES or source==target: raise DomainError('请选择两个不同币种 / Choose different currencies')
        live=rates();table=live['ratesToUSD'];rate=Decimal(str(table[source]))/Decimal(str(table[target]));received=quantize(amount*rate,target)
        if received<=0: raise DomainError('兑换金额过小 / Amount too small')
        q=dict(amount=str(amount),received=str(received),rate=str(rate),usdRate=str(table[source]),source=live['source'],asOf=live['asOf'],**{'from':source,'to':target})
        uid=secrets.token_urlsafe(20);expiry=int(time.time())+60
        with connect() as db:
            db.execute('DELETE FROM quotes WHERE expires<?',(int(time.time())-3600,))
            db.execute('INSERT INTO quotes VALUES(?,?,?,?,0)',(uid,g.user['id'],json.dumps(q),expiry))
        return jsonify(**q,quoteId=uid,expires=expiry,stale=live.get('stale',False),fee=0,markup=0)
    @app.post('/api/assessment')
    @require
    def assessment():
        limited('assessment:'+g.user['id'],120,60)
        data=payload()
        with connect() as db: value,_=account(db,g.user['id']);s=settings(db)
        return jsonify(assess(value,data,operation_rates(data,'assessment'),s))
    @app.post('/api/v1/<path:route>')
    @require
    def command(route):
        limited('command:'+g.user['id'],120,60)
        data=payload();key=request.headers.get('Idempotency-Key','')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{16,100}',key): raise DomainError('需要有效幂等键 / Valid idempotency key required')
        hash_=digest(route+json.dumps({k:v for k,v in data.items() if k not in ('currentPassword','factor')},sort_keys=True,separators=(',',':')))
        # Check replay before an external dependency, so a completed command can always be retrieved.
        with connect() as db:
            row=db.execute('SELECT * FROM commands WHERE user_id=? AND key=?',(g.user['id'],key)).fetchone()
            if row:
                if row['hash']!=hash_: raise DomainError('重复请求参数不一致 / Idempotency key conflicts',409)
                value,revision=account(db,g.user['id']);return jsonify(**json.loads(row['response']),db=value,revision=revision),row['status']
        allowed={'treasury/wire-in','treasury/accrue-apy','treasury/fx-swap','underwriting/issue-card','cards/reallocate-limit','core/reset','cards/security-freeze','cards/rotate-cvv','cards/product-change','cards/repay','pos/authorize','credit/cli-3x','benefits/use','pos/refund','cards/close','cards/replace'}
        if route not in allowed: raise DomainError('接口不存在 / Unknown operation',404)
        if route in ('pos/refund','cards/close','cards/replace','core/reset','cards/rotate-cvv'):limited('sensitive:'+g.user['id'],20,900)
        try:table=operation_rates(data,route)
        except DomainError as error:
            # A dependency failure did not execute a command. Record the attempt without
            # binding its idempotency key, so the same retry can succeed after recovery.
            with connect() as db:
                db.execute('BEGIN IMMEDIATE');value,_=account(db,g.user['id'])
                record_command(db,g.user['id'],None,route,data,{'message':error.message},error.status,value,value,settings(db))
            raise
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            live_session(db)
            maintain(db,g.user['id'],clock(app))
            previous=db.execute('SELECT * FROM commands WHERE user_id=? AND key=?',(g.user['id'],key)).fetchone()
            if previous:
                if previous['hash']!=hash_: raise DomainError('重复请求参数不一致 / Idempotency key conflicts',409)
                value,revision=account(db,g.user['id']);db.commit();return jsonify(**json.loads(previous['response']),db=value,revision=revision),previous['status']
            original,revision=account(db,g.user['id']);value=json.loads(json.dumps(original))
            try:
                if route in ('pos/refund','cards/close','cards/replace','core/reset','cards/rotate-cvv'):sensitive(app,db,g.user['id'],data)
                if route=='treasury/fx-swap':
                    q=db.execute('SELECT * FROM quotes WHERE id=? AND user_id=?',(data.get('quoteId'),g.user['id'])).fetchone()
                    if not q or q['used'] or q['expires']<time.time(): raise DomainError('报价已失效，请重新获取 / Quote expired or unavailable',409)
                    data['_quote']=json.loads(q['payload'])
                result=execute_extended(db,g.user['id'],value,route,data,clock(app)) if route in ('pos/refund','cards/close','cards/replace') else execute(value,route,data,table,{**settings(db),'_now':clock(app)})
                if result.get('issuedCard'):lifecycle_defaults(result['issuedCard'],clock(app))
                status=result.pop('status',200)
                if route=='treasury/fx-swap': db.execute('UPDATE quotes SET used=1 WHERE id=?',(data['quoteId'],))
            except DomainError as error: value=original;result={'message':error.message};status=error.status
            audit_log(value,'/api/v1/'+route,status,result['message']);revision+=1
            if route=='core/reset' and status==200:
                db.execute('UPDATE preferences SET ledger_seen=0 WHERE user_id=?',(g.user['id'],))
                from growth import preferences
                pref=preferences(db,g.user['id']);pref['defaultCard']='';db.execute('INSERT OR REPLACE INTO user_options VALUES(?,?)',(g.user['id'],json.dumps(pref)))
            db.execute('UPDATE accounts SET state=?,revision=? WHERE user_id=?',(json.dumps(value),revision,g.user['id']))
            db.execute('INSERT INTO commands VALUES(?,?,?,?,?)',(g.user['id'],key,hash_,json.dumps(result),status))
            db.execute('INSERT INTO audit(user_id,event,created) VALUES(?,?,?)',(g.user['id'],route+':'+str(status),int(time.time())))
            record_result=dict(result)
            if route=='underwriting/issue-card' and status==422:
                record_result['assessment']=assess(original,data,table,settings(db))
            rid=record_command(db,g.user['id'],key,route,data,record_result,status,original,value,settings(db))
            capture_operation(db,g.user['id'],rid,route,data,record_result,original,value,status,clock(app))
            if status<400:capture_extended(db,g.user['id'],rid,route,result,value,clock(app))
            db.commit()
        return jsonify(**result,db=value,revision=revision),status
    @app.get('/api/admin/overview')
    @require
    def admin_overview():
        if not g.user['admin']: raise DomainError('需要管理员权限 / Admin required',403)
        with connect() as db:
            audit_access(db,g.user['id'],'legacy_overview')
            users=[dict(row) for row in db.execute('SELECT id,email,created FROM users ORDER BY created DESC LIMIT 100')]
            events=[dict(row) for row in db.execute('SELECT user_id,event,created FROM audit ORDER BY id DESC LIMIT 100')]
            return jsonify(users=users,events=events,settings=settings(db),mailReady=mail_ready())
    from operations import run_checks
    app.extensions['run_ops_checks']=lambda **kwargs:run_checks(app,connect,**kwargs)
    app.extensions['session_digest']=lambda:digest(request.cookies.get('jwb_session',''))
    register_security(app,connect,require,limited,payload,live_session,session_response)
    register_growth(app,connect,require,limited,payload,live_session,maintain,ROOT)
    register_admin(app,connect,require,identity,limited,ROOT,mail_ready)
    register_suite(app,connect,require,limited,payload,maintain,live_session,ROOT)
    app.config['DUMMY_HASH']=generate_password_hash(secrets.token_urlsafe(20))
    if app.config['BASE_PATH']: app.wsgi_app=PathPrefix(app.wsgi_app,app.config['BASE_PATH'])
    return app

if __name__=='__main__':
    create_app().run(host='127.0.0.1',port=8895)
