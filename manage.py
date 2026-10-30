"""Administrative commands, run as the same OS user as the application."""
import argparse
import getpass
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from werkzeug.security import generate_password_hash
from app import create_app
from domain import empty_state
from backup_tools import backup_database, daily_backup, verify_backup, restore_database

parser=argparse.ArgumentParser()
sub=parser.add_subparsers(dest='command',required=True)
sub.add_parser('init-db')
sub.add_parser('maintenance')
ops=sub.add_parser('ops-check');ops.add_argument('--no-heartbeat',action='store_true');ops.add_argument('--no-mail',action='store_true')
mfa=sub.add_parser('disable-mfa');mfa.add_argument('email');mfa.add_argument('--confirm',action='store_true')
u=sub.add_parser('create-user');u.add_argument('email');u.add_argument('--admin',action='store_true')
b=sub.add_parser('backup');b.add_argument('destination')
d=sub.add_parser('backup-daily');d.add_argument('directory');d.add_argument('--keep',type=int,default=14)
v=sub.add_parser('verify-backup');v.add_argument('source')
r=sub.add_parser('restore');r.add_argument('source');r.add_argument('--safety-copy',required=True);r.add_argument('--service-stopped',action='store_true')
s=sub.add_parser('settings');s.add_argument('--registration',choices=['open','closed']);s.add_argument('--min-income',type=int)
args=parser.parse_args();app=create_app();db=sqlite3.connect(app.config['DATABASE'])
try:
    if args.command=='maintenance':
        print('Accounts processed:',app.extensions['run_maintenance']())
    elif args.command=='ops-check':
        print(json.dumps(app.extensions['run_ops_checks'](heartbeat=not args.no_heartbeat,send=not args.no_mail),ensure_ascii=False,indent=2))
    elif args.command=='disable-mfa':
        if not args.confirm:parser.error('Pass --confirm only after verifying account ownership through your server recovery process')
        row=db.execute('SELECT id FROM users WHERE email=?',(args.email.strip().lower(),)).fetchone()
        if not row:parser.error('User not found')
        with db:
            db.execute('DELETE FROM mfa WHERE user_id=?',(row[0],));db.execute('DELETE FROM mfa_challenges WHERE user_id=?',(row[0],));db.execute('DELETE FROM sessions WHERE user_id=?',(row[0],));db.execute('INSERT INTO security_events(user_id,event,created) VALUES(?,?,?)',(row[0],'mfa_server_recovery',int(time.time())))
        print('MFA removed and all sessions revoked; account must sign in again')
    elif args.command=='create-user':
        email=args.email.strip().lower()
        if '@' not in email: parser.error('Valid email required')
        pw=getpass.getpass('Password (10–128 characters): ')
        if not 10<=len(pw)<=128: parser.error('Password length must be 10–128')
        if pw!=getpass.getpass('Repeat password: '): parser.error('Passwords differ')
        uid=secrets.token_hex(16)
        with db:
            db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,email,generate_password_hash(pw),int(args.admin),int(time.time())))
            db.execute('INSERT INTO accounts VALUES(?,?,0)',(uid,json.dumps(empty_state())))
        print('Created empty account:',email)
    elif args.command=='backup':
        print(json.dumps(backup_database(app.config['DATABASE'],args.destination),indent=2))
        print('Verified backup saved:',Path(args.destination).resolve())
    elif args.command=='backup-daily':
        target,report=daily_backup(app.config['DATABASE'],args.directory,args.keep)
        print('Verified backup saved:',target);print(json.dumps(report,indent=2))
    elif args.command=='verify-backup':
        print(json.dumps(verify_backup(args.source),indent=2))
    elif args.command=='restore':
        if not args.service_stopped: parser.error('Stop jwb-cloud first, then pass --service-stopped. This flag is your explicit confirmation, not a service-state detector.')
        db.close()
        print(json.dumps(restore_database(args.source,app.config['DATABASE'],args.safety_copy),indent=2))
        print('Restored; all sessions and email codes revoked. Start the application and sign in again.')
    elif args.command=='settings':
        value=json.loads(db.execute('SELECT value FROM settings WHERE id=1').fetchone()[0])
        if args.registration: value['public_registration']=args.registration=='open'
        if args.min_income is not None:
            if not 0<=args.min_income<=1000000000: parser.error('Invalid minimum income')
            value['min_income']=args.min_income
        with db: db.execute('UPDATE settings SET value=? WHERE id=1',(json.dumps(value),))
        print(json.dumps(value,ensure_ascii=False))
    else: print('Database initialized')
finally: db.close()
