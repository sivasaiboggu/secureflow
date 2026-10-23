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
from app.services.scan_service import ScanService

class TenantAccessTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.db=sessionmaker(bind=self.engine)()
        self.service=ScanService()
        self.db.add_all([Organization(id='org-a',name='A'),Organization(id='org-b',name='B')])
        self.db.add_all([CloudAccount(id='account-a',name='A',provider='aws',organization_id='org-a',credentials={},is_active=True),
            CloudAccount(id='account-b',name='B',provider='aws',organization_id='org-b',credentials={},is_active=True),
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
    def test_cross_tenant_finding_cannot_be_read(self):
        self.assertIsNone(self.service.get_vulnerability(self.db,'vuln-b','org-a'))
        self.assertEqual(self.service.get_vulnerability(self.db,'vuln-b','org-b').id,'vuln-b')
    def test_cross_tenant_remediation_is_denied_without_writes(self):
        with self.assertRaises(ValueError):self.service.apply_remediation(self.db,'vuln-b','user@test.invalid','org-a')
        self.assertEqual(self.db.query(Remediation).count(),0)
        self.assertNotEqual(self.db.query(Vulnerability).first().status,'REMEDIATED')

if __name__=='__main__':unittest.main()
