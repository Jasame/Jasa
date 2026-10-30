"""TOTP and recovery codes. Secrets encrypted with an APP_SECRET-derived Fernet key."""
import base64
import hashlib
import hmac
import json
import re
import secrets
import struct
from urllib.parse import quote,urlencode
from cryptography.fernet import Fernet,InvalidToken
from flask import request,jsonify,g
from werkzeug.security import check_password_hash
from domain import DomainError
from suite import clock

def init_security(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS mfa(user_id TEXT PRIMARY KEY REFERENCES users(id),secret TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 0,pending TEXT,pending_until INTEGER,last_counter INTEGER DEFAULT -1,recovery TEXT NOT NULL DEFAULT '[]');
    CREATE TABLE IF NOT EXISTS mfa_challenges(digest TEXT PRIMARY KEY,user_id TEXT REFERENCES users(id),expires INTEGER,password_snapshot TEXT);
    ''')

def totp_code(secret,counter):
    key=base64.b32decode(secret+'='*((-len(secret))%8));value=hmac.new(key,struct.pack('>Q',counter),hashlib.sha1).digest();offset=value[-1]&15
    return f'{(struct.unpack(">I",value[offset:offset+4])[0]&0x7fffffff)%1000000:06}'

def cipher(app):return Fernet(base64.urlsafe_b64encode(hmac.new(app.config['SECRET_KEY'].encode(),b'JWB/TOTP/Fernet/v1',hashlib.sha256).digest()))
def mac(app,value):return hmac.new(app.config['SECRET_KEY'].encode(),value.encode(),hashlib.sha256).hexdigest()
def enabled(db,uid):return bool(db.execute('SELECT 1 FROM mfa WHERE user_id=? AND enabled=1',(uid,)).fetchone())
def decrypt(app,token):
    try:return cipher(app).decrypt(token.encode()).decode()
    except (InvalidToken,ValueError):raise DomainError('验证器密钥无法解密，请使用服务器恢复流程 / Authenticator key unavailable; use server recovery',503)

def matching_counter(secret,code,now,last=-1):
    if not re.fullmatch(r'\d{6}',str(code)):return None
    for counter in [now//30,now//30-1,now//30+1]:
        if counter>=0 and counter>last and hmac.compare_digest(totp_code(secret,counter),str(code)):return counter
    return None

def verify_factor(app,db,uid,value):
    row=db.execute('SELECT * FROM mfa WHERE user_id=? AND enabled=1',(uid,)).fetchone()
    if not row:return
    value=str(value or '').strip()
    counter=matching_counter(decrypt(app,row['secret']),value,clock(app),row['last_counter'])
    if counter is not None:
        db.execute('UPDATE mfa SET last_counter=? WHERE user_id=?',(counter,uid));return
    normalized=re.sub(r'[-\s]','',value).upper();hashed=mac(app,'recovery:'+uid+':'+normalized);codes=json.loads(row['recovery'])
    match=next((entry for entry in codes if hmac.compare_digest(entry,hashed)),None)
    if match:
        codes.remove(match);db.execute('UPDATE mfa SET recovery=? WHERE user_id=?',(json.dumps(codes),uid));return
    raise DomainError('验证器或恢复码无效、已使用或已过期 / Invalid, used or expired authenticator/recovery code',400)

def sensitive(app,db,uid,data):
    user=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    if not user or not check_password_hash(user['password'],str(data.get('currentPassword',''))[:129]):raise DomainError('请验证当前账户密码 / Verify your current password',400)
    verify_factor(app,db,uid,data.get('factor'))

def register_security(app,connect,require,limited,payload,live_session,session_response):
    @app.post('/api/auth/mfa-login')
    def mfa_login():
        data=payload();limited('mfa-login-ip:'+str(request.remote_addr),30,300);digest=mac(app,'challenge:'+str(data.get('challenge','')))
        with connect() as db:row=db.execute('SELECT * FROM mfa_challenges WHERE digest=?',(digest,)).fetchone()
        if not row or row['expires']<clock(app):raise DomainError('登录验证已过期，请重新登录 / Login challenge expired',401)
        limited('mfa-login:'+row['user_id'],10,300)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM mfa_challenges WHERE digest=?',(digest,)).fetchone()
            if not row or row['expires']<clock(app):raise DomainError('登录验证已过期 / Login challenge expired',401)
            user=db.execute('SELECT * FROM users WHERE id=?',(row['user_id'],)).fetchone()
            if not user or mac(app,user['password'])!=row['password_snapshot']:raise DomainError('账户已变更，请重新登录 / Account changed; sign in again',401)
            verify_factor(app,db,user['id'],data.get('factor'));db.execute('DELETE FROM mfa_challenges WHERE digest=?',(digest,));db.commit()
        return session_response(user,mfa_verified=True)
    @app.get('/api/security/mfa')
    @require
    def mfa_status():
        with connect() as db:row=db.execute('SELECT enabled,recovery FROM mfa WHERE user_id=?',(g.user['id'],)).fetchone()
        return jsonify(enabled=bool(row and row['enabled']),recoveryRemaining=len(json.loads(row['recovery'])) if row and row['enabled'] else 0)
    @app.post('/api/security/mfa/setup')
    @require
    def mfa_setup():
        data=payload();limited('mfa-setup:'+g.user['id'],8,900)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);sensitive(app,db,g.user['id'],data)
            if enabled(db,g.user['id']):raise DomainError('请先关闭现有验证器 / Disable the existing authenticator first',409)
            secret=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
            db.execute('INSERT INTO mfa(user_id,secret,pending,pending_until) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET pending=excluded.pending,pending_until=excluded.pending_until',(g.user['id'],'',cipher(app).encrypt(secret.encode()).decode(),clock(app)+600))
        uri='otpauth://totp/'+quote('JWB:'+g.user['email'],safe='')+'?'+urlencode({'secret':secret,'issuer':'JWB Simulation','algorithm':'SHA1','digits':6,'period':30})
        return jsonify(secret=secret,uri=uri,expiresIn=600)
    @app.post('/api/security/mfa/enable')
    @require
    def mfa_enable():
        data=payload();limited('mfa-enable:'+g.user['id'],10,300)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);sensitive(app,db,g.user['id'],data)
            row=db.execute('SELECT * FROM mfa WHERE user_id=?',(g.user['id'],)).fetchone()
            if not row or row['enabled'] or not row['pending'] or row['pending_until']<clock(app):raise DomainError('设置已过期，请重新开始 / Setup expired; start again',409)
            counter=matching_counter(decrypt(app,row['pending']),data.get('code'),clock(app))
            if counter is None:raise DomainError('验证码无效 / Invalid authenticator code')
            codes=[secrets.token_hex(8).upper() for _ in range(10)];hashes=[mac(app,'recovery:'+g.user['id']+':'+code) for code in codes]
            db.execute('UPDATE mfa SET enabled=1,secret=pending,pending=NULL,pending_until=NULL,last_counter=?,recovery=? WHERE user_id=?',(counter,json.dumps(hashes),g.user['id']))
            db.execute('DELETE FROM sessions WHERE user_id=? AND token!=?',(g.user['id'],app.extensions['session_digest']()))
            db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(g.user['id'],'mfa_enabled',clock(app)))
        return jsonify(message='二次验证已启用；其他设备已退出，请离线保存恢复码 / MFA enabled; other sessions revoked. Save recovery codes offline',recoveryCodes=['-'.join(c[i:i+4] for i in range(0,16,4)) for c in codes])
    @app.post('/api/security/mfa/disable')
    @require
    def mfa_disable():
        data=payload();limited('mfa-disable:'+g.user['id'],10,300)
        with connect() as db:
            db.execute('BEGIN IMMEDIATE');live_session(db);sensitive(app,db,g.user['id'],data)
            db.execute('DELETE FROM mfa WHERE user_id=?',(g.user['id'],));db.execute('DELETE FROM mfa_challenges WHERE user_id=?',(g.user['id'],))
            db.execute('DELETE FROM sessions WHERE user_id=? AND token!=?',(g.user['id'],app.extensions['session_digest']()))
            db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(g.user['id'],'mfa_disabled',clock(app)))
        return jsonify(message='二次验证已关闭，其他设备已退出 / MFA disabled; other sessions revoked')
