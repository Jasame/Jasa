import hashlib,importlib.util,json,tempfile,unittest,zipfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('jwb_updater',Path(__file__).resolve().parents[1]/'deploy/update.py');updater=importlib.util.module_from_spec(spec);spec.loader.exec_module(updater)
class UpdaterTests(unittest.TestCase):
    def package(self,folder,mutate=None):
        names=['app.py','manage.py','growth.py','growth_security.py','requirements.txt','static/index.html','static/growth.js','fonts/JWB-NotoSC.ttf']
        files={n:('content:'+n).encode() for n in names};manifest={'version':'6.0.0','files':{n:{'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)} for n,data in files.items()}}
        if mutate:mutate(files,manifest)
        path=Path(folder)/'package.zip'
        with zipfile.ZipFile(path,'w') as z:
            for n,data in files.items():z.writestr('jwb-cloud/'+n,data)
            z.writestr('jwb-cloud/release-manifest.json',json.dumps(manifest))
        return path
    def test_manifest_checksum_and_unlisted_files(self):
        with tempfile.TemporaryDirectory() as folder:
            version,files=updater.verify_package(self.package(folder));self.assertEqual(version['version'],'6.0.0');self.assertEqual(len(files),8)
            for mutate in [lambda f,m:f.update({'app.py':b'tampered'}),lambda f,m:f.update({'unlisted.py':b'extra'})]:
                with self.assertRaises(ValueError):updater.verify_package(self.package(folder,mutate))
    def test_protected_and_traversal_paths(self):
        for name in ['../.env','/etc/passwd','a/../b','a//b','a\\b']:
            self.assertFalse(updater.valid_path(name))
        with tempfile.TemporaryDirectory() as folder:
            def mutate(files,manifest):
                files['.env']=b'private';manifest['files']['.env']={'sha256':hashlib.sha256(b'private').hexdigest(),'size':7}
            with self.assertRaises(ValueError):updater.verify_package(self.package(folder,mutate))
    def test_server_config_is_validated_but_never_installed(self):
        with tempfile.TemporaryDirectory() as folder:
            def mutate(files,manifest):
                data=b'config template';files['gunicorn.conf.py']=data;manifest['files']['gunicorn.conf.py']={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data)}
            manifest,files=updater.verify_package(self.package(folder,mutate))
            self.assertIn('gunicorn.conf.py',manifest['files']);self.assertNotIn('gunicorn.conf.py',files)
    def test_legacy_rollback_refuses_mfa_or_refunds(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);snapshot=root/'snapshot';snapshot.mkdir();(snapshot/'metadata.json').write_text('{"oldVersion":"5.0.0"}')
            values={'DATABASE':str(root/'db')}
            with sqlite3.connect(values['DATABASE']) as db:
                db.executescript('CREATE TABLE accounts(state TEXT);CREATE TABLE mfa(enabled INTEGER);CREATE TABLE refund_totals(record_id TEXT);INSERT INTO mfa VALUES(1);')
            with self.assertRaisesRegex(RuntimeError,'MFA'):updater.guard_legacy_rollback(snapshot,root,values)
            with sqlite3.connect(values['DATABASE']) as db:db.executescript("DELETE FROM mfa;INSERT INTO refund_totals VALUES('refund');")
            with self.assertRaisesRegex(RuntimeError,'refund'):updater.guard_legacy_rollback(snapshot,root,values)
