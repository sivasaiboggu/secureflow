"""Real orchestration with SQLite, fake scanners, broker and model. No cloud/model work."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.database.models import Organization, CloudAccount, Scan, Vulnerability, Alert

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session=sessionmaker(bind=self.engine)
        db=self.session()
        db.add(Organization(id='org',name='Synthetic'))
        db.add(CloudAccount(id='account',name='Demo',provider='aws',organization_id='org',credentials={'scan_mode':'demo'},is_active=True))
        db.add_all([Scan(id='one',organization_id='org',cloud_account_id='account'),Scan(id='two',organization_id='org',cloud_account_id='account')])
        db.commit();db.close()
        taskmod=types.ModuleType('app.tasks.celery_app')
        taskmod.celery_app=Mock();taskmod.celery_app.task=lambda **kw: lambda fn: fn
        mlmod=types.ModuleType('app.services.ml_service')
        mlmod.ml_service=Mock();mlmod.ml_service.predict_severity.return_value={'predicted_severity':'HIGH'}
        self.patcher=patch.dict(sys.modules,{'app.tasks.celery_app':taskmod,'app.services.ml_service':mlmod})
        self.patcher.start()
        path=Path(__file__).parents[1]/'app/tasks/scan_tasks.py'
        spec=importlib.util.spec_from_file_location('test_real_scan_worker',path)
        self.worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.worker)
        self.worker.SessionLocal=self.session
        self.scanners=[]
        for name in ['S3Scanner','EC2Scanner','IAMScanner','RDSScanner','LambdaScanner','VPCScanner','CloudTrailScanner']:
            cls=Mock();cls.return_value.scan.return_value=[];cls.return_value.get_compliance_checks.return_value=[]
            setattr(self.worker,name,cls);self.scanners.append(cls)
    def tearDown(self):
        self.patcher.stop();self.engine.dispose()
    def test_demo_status_and_distinct_finding_ids_across_runs(self):
        finding=dict(id='same-source-id',resource_type='S3_BUCKET',resource_id='synthetic',resource_name='demo',vulnerability_type='DEMO',cvss_score=1,title='[DEMO] Synthetic',description='Sample only',recommendation='None',remediation_steps=[],terraform_fix='',compliance_frameworks=[],cve_id=None,evidence={'synthetic':True,'scan_mode':'demo'})
        self.scanners[0].return_value.scan.return_value=[finding]
        for sid in ['one','two']:
            self.assertTrue(self.worker.run_cloud_scan_task(Mock(),sid,'account','org'))
        db=self.session()
        self.assertEqual({s.status for s in db.query(Scan).all()},{'DEMO_COMPLETED'})
        self.assertEqual(db.query(Vulnerability).count(),2)
        self.assertEqual({v.scan_id for v in db.query(Vulnerability).all()},{'one','two'})
        db.close()
    def test_real_scan_failure_never_persists_a_completed_result(self):
        from app.scanners.base import ScanUnavailable
        self.scanners[0].return_value.scan.side_effect=ScanUnavailable('Synthetic denied')
        context=Mock();context.retry.side_effect=RuntimeError('retry requested')
        with self.assertRaisesRegex(RuntimeError,'retry requested'):
            self.worker.run_cloud_scan_task(context,'one','account','org')
        db=self.session();self.assertEqual(db.get(Scan,'one').status,'FAILED')
        self.assertEqual(db.query(Vulnerability).count(),0);db.close()
    def test_alert_does_not_claim_external_notification(self):
        self.worker.ml_service.predict_severity.return_value={'predicted_severity':'CRITICAL'}
        self.scanners[0].return_value.scan.return_value=[dict(id='x',resource_type='S3',resource_id='x',resource_name='x',vulnerability_type='X',cvss_score=9,title='[DEMO] x',description='x',recommendation='x',remediation_steps=[],terraform_fix='',compliance_frameworks=[],cve_id=None)]
        self.worker.run_cloud_scan_task(Mock(),'one','account','org')
        db=self.session();self.assertEqual(db.query(Alert).one().channels_sent,['WEBPAGE']);db.close()

    def test_worker_decrypts_for_scanner_without_rewriting_envelope(self):
        import base64, os
        from app.security.credential_store import seal_credentials
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            db=self.session();row=db.get(CloudAccount,'account')
            envelope=seal_credentials({'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'},row.id,row.organization_id,row.provider)
            row.credentials=envelope;db.commit();db.close()
            self.assertTrue(self.worker.run_cloud_scan_task(Mock(),'one','account','org'))
            supplied=self.scanners[0].call_args.args[2]
            self.assertEqual(supplied['aws_secret_access_key'],'synthetic-secret')
            self.assertNotIn('ciphertext',supplied)
            db=self.session();self.assertEqual(db.get(CloudAccount,'account').credentials,envelope);db.close()

    def test_worker_wrong_key_fails_before_scanner_calls(self):
        import base64, os
        from app.security.credential_store import seal_credentials
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            db=self.session();row=db.get(CloudAccount,'account')
            row.credentials=seal_credentials({'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'},row.id,row.organization_id,row.provider)
            db.commit();db.close()
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            context=Mock();context.retry.side_effect=RuntimeError('retry requested')
            with self.assertRaisesRegex(RuntimeError,'retry requested'):
                self.worker.run_cloud_scan_task(context,'one','account','org')
        for scanner in self.scanners:scanner.assert_not_called()
        db=self.session();self.assertEqual(db.get(Scan,'one').status,'FAILED');db.close()


    def test_completed_redelivery_does_not_rescan_or_duplicate_results(self):
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(),'one','account','org'))
        for scanner in self.scanners: scanner.reset_mock()
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(),'one','account','org'))
        for scanner in self.scanners: scanner.assert_not_called()
        db=self.session();self.assertEqual(db.get(Scan,'one').status,'DEMO_COMPLETED');db.close()

    def test_running_scan_is_not_claimed_by_another_delivery(self):
        db=self.session();row=db.get(Scan,'one');row.status='RUNNING';row.progress=35;db.commit();db.close()
        self.assertFalse(self.worker.run_cloud_scan_task(Mock(),'one','account','org'))
        for scanner in self.scanners:scanner.assert_not_called()
        db=self.session();self.assertEqual(db.get(Scan,'one').progress,35);db.close()

    def test_failed_scan_can_retry_and_clear_stale_completion_time(self):
        from datetime import datetime
        db=self.session();row=db.get(Scan,'one');row.status='FAILED';row.completed_at=datetime(2020,1,1);db.commit();db.close()
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(),'one','account','org'))
        db=self.session();row=db.get(Scan,'one');self.assertEqual(row.status,'DEMO_COMPLETED');self.assertGreater(row.completed_at,datetime(2020,1,1));db.close()
