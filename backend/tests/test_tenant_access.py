"""SQLite service regression tests, with cloud task dispatch replaced by a mock."""
import os
import sys
import types
import unittest
from unittest.mock import Mock

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
# Avoid importing cloud SDKs/models or sending Celery work during tests.
task_module = types.ModuleType('app.tasks.scan_tasks')
task_module.run_cloud_scan_task = Mock()
sys.modules['app.tasks.scan_tasks'] = task_module

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.database.models import Organization, CloudAccount, Scan, Vulnerability, Remediation
from app.services.scan_service import ScanService, ScanDispatchUnknown

class TenantAccessTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        self.service=ScanService()
        self.db.add_all([Organization(id='org-a',name='A'),Organization(id='org-b',name='B')])
        self.db.add_all([CloudAccount(id='account-a',name='A',provider='aws',organization_id='org-a',credentials={"scan_mode":"demo"},is_active=True),
            CloudAccount(id='account-b',name='B',provider='aws',organization_id='org-b',credentials={"scan_mode":"demo"},is_active=True),
            CloudAccount(id='inactive-a',name='Off',provider='aws',organization_id='org-a',credentials={},is_active=False)])
        self.db.add(Scan(id='scan-b',organization_id='org-b',cloud_account_id='account-b'))
        self.db.add(Vulnerability(id='vuln-b',scan_id='scan-b',resource_id='bucket',resource_type='s3',vulnerability_type='PUBLIC',severity='HIGH',cvss_score=8,title='Finding',description='Demo'))
        self.db.commit();task_module.run_cloud_scan_task.reset_mock()
    def tearDown(self):self.db.close();self.engine.dispose()
    def test_cross_tenant_scan_is_denied_before_dispatch(self):
        with self.assertRaises(ValueError):self.service.trigger_scan(self.db,'account-b','org-a')
        task_module.run_cloud_scan_task.delay.assert_not_called()
        self.assertEqual(self.db.query(Scan).count(),1)
    def test_inactive_and_missing_accounts_are_denied(self):
        for account in ['inactive-a','unknown']:
            with self.assertRaises(ValueError):self.service.trigger_scan(self.db,account,'org-a')
        task_module.run_cloud_scan_task.delay.assert_not_called()
    def test_owned_scan_dispatches(self):
        scan=self.service.trigger_scan(self.db,'account-a','org-a')
        self.assertEqual(scan.organization_id,'org-a')
        task_module.run_cloud_scan_task.delay.assert_called_once_with(scan.id,'account-a','org-a')
    def test_missing_real_credentials_rejected_before_record_or_dispatch(self):
        self.db.query(CloudAccount).filter_by(id='account-a').first().credentials={}
        self.db.commit()
        with self.assertRaises(ValueError): self.service.trigger_scan(self.db,'account-a','org-a')
        task_module.run_cloud_scan_task.delay.assert_not_called()
        self.assertEqual(self.db.query(Scan).count(),1)

    def test_broker_failure_preserves_pending_record_without_untracked_thread(self):
        task_module.run_cloud_scan_task.delay.side_effect=RuntimeError('synthetic broker down')
        try:
            with self.assertRaises(ScanDispatchUnknown) as caught: self.service.trigger_scan(self.db,'account-a','org-a')
            failed=self.db.query(Scan).filter_by(organization_id='org-a').one()
            self.assertEqual(failed.status,'PENDING')
            self.assertIsNone(failed.completed_at)
            self.assertEqual(caught.exception.scan_id,failed.id)
        finally:
            task_module.run_cloud_scan_task.delay.side_effect=None

    def test_unsupported_provider_rejected_before_dispatch(self):
        self.db.query(CloudAccount).filter_by(id='account-a').first().provider='azure'
        self.db.commit()
        with self.assertRaises(ValueError): self.service.trigger_scan(self.db,'account-a','org-a')
        task_module.run_cloud_scan_task.delay.assert_not_called()

    def test_cross_tenant_finding_cannot_be_read(self):
        self.assertIsNone(self.service.get_vulnerability(self.db,'vuln-b','org-a'))
        self.assertEqual(self.service.get_vulnerability(self.db,'vuln-b','org-b').id,'vuln-b')
    def test_cross_tenant_remediation_is_denied_without_writes(self):
        with self.assertRaises(ValueError):self.service.apply_remediation(self.db,'vuln-b','user@test.invalid','org-a')
        self.assertEqual(self.db.query(Remediation).count(),0)
        self.assertNotEqual(self.db.query(Vulnerability).first().status,'REMEDIATED')

    def test_plan_is_pending_and_does_not_claim_execution(self):
        vuln=self.db.query(Vulnerability).first()
        vuln.terraform_fix='resource "example" "synthetic" {}'
        self.db.commit()
        plan=self.service.apply_remediation(self.db,'vuln-b','user@test.invalid','org-b')
        self.assertEqual(plan.status,'PENDING')
        self.assertIsNone(plan.executed_at)
        self.assertIsNone(plan.executed_by)
        self.assertEqual(vuln.status,'OPEN')
    def test_plan_without_code_is_rejected(self):
        with self.assertRaises(ValueError):self.service.apply_remediation(self.db,'vuln-b','user@test.invalid','org-b')
        self.assertEqual(self.db.query(Remediation).count(),0)

    def test_legacy_plaintext_never_dispatches(self):
        row=self.db.get(CloudAccount,'account-a')
        row.credentials={'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'}
        self.db.commit()
        with self.assertRaisesRegex(ValueError,'re-registration'):
            self.service.trigger_scan(self.db,'account-a','org-a')
        task_module.run_cloud_scan_task.delay.assert_not_called()
        self.assertEqual(self.db.query(Scan).count(),1)

    def test_encrypted_owned_account_dispatches_only_ids(self):
        import base64
        from unittest.mock import patch
        from app.security.credential_store import seal_credentials
        row=self.db.get(CloudAccount,'account-a')
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            row.credentials=seal_credentials({'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'},row.id,row.organization_id,row.provider)
            self.db.commit()
            scan=self.service.trigger_scan(self.db,'account-a','org-a')
        task_module.run_cloud_scan_task.delay.assert_called_once_with(scan.id,'account-a','org-a')



    def test_lost_publish_response_does_not_overwrite_worker_completion(self):
        def accepted_then_lost(scan_id,*_):
            self.db.query(Scan).filter_by(id=scan_id).update({'status':'DEMO_COMPLETED','progress':100})
            self.db.commit()
            raise RuntimeError('synthetic lost response')
        task_module.run_cloud_scan_task.delay.side_effect=accepted_then_lost
        try:
            with self.assertRaises(ScanDispatchUnknown):self.service.trigger_scan(self.db,'account-a','org-a')
            row=self.db.query(Scan).filter_by(organization_id='org-a').one()
            self.assertEqual(row.status,'DEMO_COMPLETED');self.assertEqual(row.progress,100)
        finally:task_module.run_cloud_scan_task.delay.side_effect=None
