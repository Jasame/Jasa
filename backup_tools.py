"""Consistent SQLite backups, verification and explicit offline restore."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3

REQUIRED = {
    'users': {'id','email','password','admin','created'},
    'accounts': {'user_id','state','revision'},
    'sessions': {'token','user_id','expires'},
    'codes': {'email','purpose','digest','expires','attempts','created'},
    'limits': {'key','count','until'},
    'commands': {'user_id','key','hash','response','status'},
    'quotes': {'id','user_id','payload','expires','used'},
    'settings': {'id','value'}, 'fx': {'id','value'},
    'audit': {'id','user_id','event','created'},
}

def readonly(path):
    path=Path(path).resolve(strict=True)
    return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=20)

def checksum(path):
    digest=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def verify_backup(path):
    """Restore into a separate database and validate schema, integrity and data."""
    path=Path(path).resolve(strict=True)
    sidecar=path.with_suffix(path.suffix+'.json')
    digest=checksum(path)
    if sidecar.exists() and json.loads(sidecar.read_text())['sha256']!=digest:
        raise ValueError('Backup SHA-256 mismatch')
    with closing(readonly(path)) as source, closing(sqlite3.connect(':memory:')) as drill:
        source.backup(drill)
        if drill.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]: raise ValueError('SQLite integrity check failed')
        if drill.execute('PRAGMA foreign_key_check').fetchone(): raise ValueError('Foreign key check failed')
        for table,columns in REQUIRED.items():
            actual={row[1] for row in drill.execute(f'PRAGMA table_info({table})')}
            if not columns<=actual: raise ValueError('Not a compatible JWB backup: '+table)
        if drill.execute('SELECT 1 FROM users LEFT JOIN accounts ON users.id=accounts.user_id WHERE accounts.user_id IS NULL').fetchone():
            raise ValueError('Account state is missing')
        for (state,) in drill.execute('SELECT state FROM accounts'):
            value=json.loads(state)
            if not isinstance(value.get('cards'),list) or not isinstance(value.get('treasuryWallets'),dict): raise ValueError('Invalid account state')
        settings=json.loads(drill.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])
        if 'public_registration' not in settings or 'min_income' not in settings: raise ValueError('Invalid settings')
        return {'sha256':digest,'users':drill.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                'accounts':drill.execute('SELECT COUNT(*) FROM accounts').fetchone()[0],
                'verifiedAt':datetime.now(timezone.utc).isoformat(),'restoreDrill':'passed'}

def backup_database(source,target):
    target=Path(target).absolute()
    if target.exists() or target.is_symlink(): raise FileExistsError('Destination exists; use a new filename')
    # Exclusive creation prevents accidental overwrites; partial files are not valid backups.
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    try:
        with closing(readonly(source)) as original, closing(sqlite3.connect(target)) as backup:
            original.backup(backup)
        report=verify_backup(target)
        with open(target,'rb') as stream: os.fsync(stream.fileno())
        with open(target.with_suffix(target.suffix+'.json'),'x') as stream:
            os.chmod(stream.name,0o600);json.dump(report,stream,indent=2);stream.flush();os.fsync(stream.fileno())
        return report
    except BaseException:
        target.unlink(missing_ok=True)
        raise

def daily_backup(source,directory,keep=14):
    import fcntl
    directory=Path(directory).resolve();directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    if directory.stat().st_mode & 0o077: raise ValueError('Backup directory must be private (chmod 700)')
    if not 2<=keep<=365: raise ValueError('Keep must be between 2 and 365')
    with open(directory/'.backup.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4)
        target=directory/('jwb-auto-'+stamp+'.sqlite3')
        report=backup_database(source,target)
        # Only prune this tool's own names, and only after the new backup passed verification.
        owned=sorted((p for p in directory.iterdir() if re.fullmatch(r'jwb-auto-\d{8}T\d{6}Z-[a-f0-9]{8}\.sqlite3',p.name)),key=lambda p:p.stat().st_mtime,reverse=True)
        for old in owned[keep:]:
            old.unlink();old.with_suffix(old.suffix+'.json').unlink(missing_ok=True)
        return target,report

def restore_database(source,destination,safety_copy):
    """Caller must stop the application first. Preserve current state before restoring."""
    if Path(source).resolve()==Path(destination).resolve(): raise ValueError('Source and destination must differ')
    report=verify_backup(source)
    backup_database(destination,safety_copy)
    with closing(readonly(source)) as original, closing(sqlite3.connect(destination,timeout=20)) as target:
        original.backup(target)
        # Restored sessions/codes must never resurrect access that was revoked after the backup.
        target.execute('DELETE FROM sessions');target.execute('DELETE FROM codes')
        if target.execute("SELECT 1 FROM sqlite_master WHERE name='session_details'").fetchone(): target.execute('DELETE FROM session_details')
        if target.execute("SELECT 1 FROM sqlite_master WHERE name='mfa_challenges'").fetchone(): target.execute('DELETE FROM mfa_challenges')
        target.commit()
    os.chmod(destination,0o600)
    verify_backup(destination)
    return report
