#!/usr/bin/env python3
"""Root-run, local-only updater. Never replaces .env/data or changes Nginx/SMTP."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import pwd
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
import zipfile

PROTECTED={'.env','data','.venv','gunicorn.conf.py','.git','node_modules'}
TIMERS=('jwb-backup.timer','jwb-maintenance.timer','jwb-ops.timer')
TASKS=('jwb-backup.service','jwb-maintenance.service','jwb-ops.service')

def run(args,**kwargs):return subprocess.run([str(a) for a in args],check=True,**kwargs)
def system(*args):return run(['systemctl',*args],stdout=subprocess.DEVNULL)
def active(unit):return subprocess.run(['systemctl','is-active','--quiet',unit]).returncode==0

def valid_path(name):
    path=PurePosixPath(name)
    return bool(name and str(path)==name.rstrip('/') and not path.is_absolute() and '..' not in path.parts and not any('\x00' in p or '\\' in p for p in path.parts))

def verify_package(archive):
    with zipfile.ZipFile(archive) as z:
        entries=z.infolist()
        if len(entries)>2000 or sum(e.file_size for e in entries)>256*1024*1024:raise ValueError('Archive exceeds limits')
        names=[e.filename for e in entries]
        if len(names)!=len(set(names)):raise ValueError('Duplicate archive entries')
        for e in entries:
            if not valid_path(e.filename) or not e.filename.startswith('jwb-cloud/') or stat.S_ISLNK(e.external_attr>>16):raise ValueError('Unsafe archive path')
        manifest=json.loads(z.read('jwb-cloud/release-manifest.json'))
        if not isinstance(manifest.get('files'),dict) or not manifest['files'] or not str(manifest.get('version','')).startswith('6.'):raise ValueError('Invalid release manifest')
        files={}
        for name,expected in manifest['files'].items():
            if not valid_path(name) or (PurePosixPath(name).parts[0] in PROTECTED and name!='gunicorn.conf.py'):raise ValueError('Protected or unsafe release path')
            data=z.read('jwb-cloud/'+name)
            if len(data)!=expected['size'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('Release checksum mismatch: '+name)
            files[name]=data
        actual={e.filename.removeprefix('jwb-cloud/') for e in entries if not e.is_dir() and e.filename!='jwb-cloud/release-manifest.json'}
        if actual!=set(files):raise ValueError('Archive contains unlisted or missing files')
        for required in ('app.py','manage.py','growth.py','growth_security.py','requirements.txt','static/index.html','static/growth.js','fonts/JWB-NotoSC.ttf'):
            if required not in files:raise ValueError('Missing required file: '+required)
        # Included for fresh installations, but an existing server owns its configuration.
        files.pop('gunicorn.conf.py',None)
        return manifest,files

def env_values(appdir):
    values={}
    for line in (appdir/'.env').read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('"\'')
    return values

def chown_tree(path,uid,gid):
    for file in [path,*path.rglob('*')]:os.chown(file,uid,gid)

def copy_program(source,destination,names):
    destination.mkdir(mode=0o700,parents=True,exist_ok=True)
    for name in names:
        path=source/name
        if path.is_file():
            target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)

def gate(appdir,on):
    path=appdir/'.update-in-progress'
    if on:path.write_text('Update in progress\n');path.chmod(0o644)
    else:path.unlink(missing_ok=True)

def health(appdir,values):
    base=values.get('BASE_PATH','').rstrip('/');url='http://127.0.0.1:8895'+base+'/api/health'
    for _ in range(20):
        try:
            with urllib.request.urlopen(url,timeout=2) as response:
                body=json.load(response)
                if response.status==200 and body.get('ok') and str(body.get('version','')).startswith('6.'):return
        except Exception:pass
        time.sleep(.5)
    raise RuntimeError('New application did not pass loopback health check')

def guard_legacy_rollback(snapshot,appdir,values):
    version=json.loads((snapshot/'metadata.json').read_text()).get('oldVersion','5')
    if str(version).startswith('6.'):return
    import sqlite3
    dbpath=Path(values.get('DATABASE',str(appdir/'data/jwb.sqlite3')))
    with sqlite3.connect(dbpath) as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'mfa' in tables and db.execute('SELECT 1 FROM mfa WHERE enabled=1 LIMIT 1').fetchone():raise RuntimeError('Legacy rollback refused: MFA is enabled; old code cannot enforce MFA')
        if 'refund_totals' in tables and db.execute('SELECT 1 FROM refund_totals LIMIT 1').fetchone():raise RuntimeError('Legacy rollback refused: refund lifecycle data already exists')
        for (raw,) in db.execute('SELECT state FROM accounts'):
            if any(c.get('status') in ('CLOSED','EXPIRED') or c.get('replacementCount',0)>0 for c in json.loads(raw)['cards']):raise RuntimeError('Legacy rollback refused: new card lifecycle states exist')
        if 'business_records' in tables and db.execute("SELECT 1 FROM business_records WHERE route='cards/annual-renewal' LIMIT 1").fetchone():raise RuntimeError('Legacy rollback refused: renewal fees already posted')

def restore(snapshot,appdir,values,account):
    if not (snapshot/'venv').is_dir():raise ValueError('Rollback environment is missing or this snapshot was already restored')
    meta=json.loads((snapshot/'metadata.json').read_text());system('stop','jwb-cloud')
    for timer in (*TIMERS,*TASKS):subprocess.run(['systemctl','stop',timer],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    guard_legacy_rollback(snapshot,appdir,values)
    gate(appdir,True)
    for name in meta['newFiles']:
        if PurePosixPath(name).parts[0] in PROTECTED:continue
        path=appdir/name
        if path.is_file():path.unlink()
    copy_program(snapshot/'program',appdir,meta['oldFiles'])
    if (snapshot/'venv').exists():
        if (appdir/'.venv').exists():shutil.rmtree(appdir/'.venv')
        shutil.move(str(snapshot/'venv'),str(appdir/'.venv'))
    for name in meta['oldFiles']:
        file=appdir/name
        if file.exists():os.chown(file,account.pw_uid,account.pw_gid)
    gate(appdir,False);system('start','jwb-cloud')
    for timer in meta['activeTimers']:subprocess.run(['systemctl','start',timer],check=False)
    print('Program restored; database preserved. Verify the service and sign in again.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('archive',nargs='?');parser.add_argument('--app-dir',default='/www/wwwroot/jwb-cloud');parser.add_argument('--releases-dir',default='/www/backup/jwb-releases');parser.add_argument('--check-only',action='store_true');parser.add_argument('--rollback');parser.add_argument('--user',default='www');args=parser.parse_args()
    if not args.archive and not args.rollback:parser.error('Provide an archive or --rollback snapshot directory')
    if args.rollback and args.archive:parser.error('Choose update or rollback')
    appdir=Path(args.app_dir).resolve();releases=Path(args.releases_dir).resolve()
    if args.check_only:
        manifest,files=verify_package(args.archive);print('Package checks passed:',manifest['version'],len(files),'files');return
    if os.geteuid()!=0:parser.error('Run deployment from a root server terminal')
    if not appdir.is_dir() or not (appdir/'.env').is_file() or not (appdir/'.venv/bin/python').exists():raise ValueError('Existing configured installation required')
    account=pwd.getpwnam(args.user);values=env_values(appdir)
    releases.mkdir(parents=True,exist_ok=True,mode=0o700);releases.chmod(0o700)
    with (releases/'.upgrade.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.rollback:
            snapshot=Path(args.rollback).resolve(strict=True)
            if snapshot.parent!=releases:raise ValueError('Rollback snapshot must be directly inside releases directory')
            restore(snapshot,appdir,values,account);return
        manifest,files=verify_package(args.archive)
        if shutil.disk_usage(appdir).free<sum(len(v) for v in files.values())*3+512*1024*1024:raise ValueError('Insufficient disk space for staged code, dependencies and rollback')
        stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex[:6];snapshot=releases/stamp;snapshot.mkdir(mode=0o700)
        # Program snapshot includes previous source, excluding runtime data and configuration.
        old_files=[str(p.relative_to(appdir)) for p in appdir.rglob('*') if p.is_file() and not any(part in PROTECTED|{'__pycache__'} for part in p.relative_to(appdir).parts) and p.name!='.update-in-progress' and p.suffix not in ('.pyc','.log')]
        copy_program(appdir,snapshot/'program',old_files)
        old_version='5.0.0'
        try:old_version=json.loads((appdir/'release-manifest.json').read_text())['version']
        except (OSError,ValueError,KeyError):pass
        meta={'oldFiles':old_files,'newFiles':[*files,'release-manifest.json'],'oldVersion':old_version,'newVersion':manifest['version'],'activeTimers':[t for t in TIMERS if active(t)]}
        (snapshot/'metadata.json').write_text(json.dumps(meta));(snapshot/'metadata.json').chmod(0o600)
        with tempfile.TemporaryDirectory(prefix='.jwb-stage-',dir=appdir.parent) as folder:
            stage=Path(folder);os.chown(stage,account.pw_uid,account.pw_gid)
            for name,data in files.items():
                dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            shutil.copy2(appdir/'gunicorn.conf.py',stage/'gunicorn.conf.py')
            run([appdir/'.venv/bin/python','-m','venv',stage/'.venv'])
            chown_tree(stage,account.pw_uid,account.pw_gid)
            run(['runuser','-u',args.user,'--',stage/'.venv/bin/python','-m','pip','install','--no-cache-dir','-r',stage/'requirements.txt'])
            run(['runuser','-u',args.user,'--',stage/'.venv/bin/python','-c','import app,growth,growth_security,operations; from reportlab.pdfbase.ttfonts import TTFont; TTFont("Check", "fonts/JWB-NotoSC.ttf"); print("Imports and PDF font OK")'],cwd=stage)
            backup_dir=Path(values.get('BACKUP_DIR','/www/backup/jwb-cloud'))
            backup_target=backup_dir/('before-update-'+stamp+'.sqlite3')
            run(['runuser','-u',args.user,'--',appdir/'.venv/bin/python','manage.py','backup',backup_target],cwd=appdir)
            # Executable shebangs and shell activation scripts must use the final path.
            for file in (stage/'.venv/bin').iterdir():
                if file.is_symlink() or not file.is_file():continue
                try:
                    content=file.read_bytes();prefix=str(stage/'.venv').encode()
                    if b'\x00' not in content and prefix in content:file.write_bytes(content.replace(prefix,str(appdir/'.venv').encode()))
                except OSError:pass
            moved=False;changed=False;activated=False
            try:
                for unit in (*TIMERS,*TASKS):subprocess.run(['systemctl','stop',unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                system('stop','jwb-cloud');gate(appdir,True);changed=True
                shutil.move(str(appdir/'.venv'),str(snapshot/'venv'));moved=True
                shutil.move(str(stage/'.venv'),str(appdir/'.venv'))
                for name in files:
                    dest=appdir/name;dest.parent.mkdir(parents=True,exist_ok=True);os.replace(stage/name,dest);os.chown(dest,account.pw_uid,account.pw_gid)
                (appdir/'release-manifest.json').write_text(json.dumps(manifest));os.chown(appdir/'release-manifest.json',account.pw_uid,account.pw_gid)
                run(['runuser','-u',args.user,'--',appdir/'.venv/bin/python','manage.py','init-db'],cwd=appdir)
                system('start','jwb-cloud');health(appdir,values);gate(appdir,False);activated=True
                run(['runuser','-u',args.user,'--',appdir/'.venv/bin/python','manage.py','maintenance'],cwd=appdir)
                for suffix in ('service','timer'):shutil.copy2(appdir/f'deploy/jwb-ops.{suffix}',Path('/etc/systemd/system')/f'jwb-ops.{suffix}')
                system('daemon-reload');system('enable','--now','jwb-ops.timer')
                for timer in meta['activeTimers']:system('start',timer)
                print('Upgrade passed:',manifest['version']);print('Rollback snapshot:',snapshot);print('Verified database backup:',backup_target)
            except BaseException:
                if activated:
                    for timer in meta['activeTimers']:subprocess.run(['systemctl','start',timer],check=False)
                    print('Application is healthy; post-update maintenance/monitor setup needs attention. Program and database retained.',file=sys.stderr)
                elif changed and moved:
                    try:restore(snapshot,appdir,values,account)
                    except Exception as recovery:print('Automatic program recovery could not complete:',type(recovery).__name__,file=sys.stderr);print('Keep services stopped and retain snapshot:',snapshot,file=sys.stderr)
                elif changed:
                    gate(appdir,False);system('start','jwb-cloud')
                    for timer in meta['activeTimers']:subprocess.run(['systemctl','start',timer])
                raise

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError,zipfile.BadZipFile,KeyError) as error:
        print('Update stopped:',str(error),file=sys.stderr);sys.exit(1)
