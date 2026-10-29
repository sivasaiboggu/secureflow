"""Interrupted-worker recovery with SQLite rows and a fake clock. No cloud/model work."""
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.database import Base
from app.database.models import Organization, CloudAccount, Scan

NOW = datetime(2026, 10, 29, 12, 0, 0)

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
        db = self.session()
        db.add(Organization(id='org', name='Synthetic'))
        db.add(CloudAccount(id='account', name='Demo', provider='aws', organization_id='org', credentials={'scan_mode': 'demo'}, is_active=True))
        db.commit(); db.close()
        taskmod = types.ModuleType('app.tasks.celery_app')
        taskmod.celery_app = Mock(); taskmod.celery_app.task = lambda **kw: lambda fn: fn
        mlmod = types.ModuleType('app.services.ml_service')
        mlmod.ml_service = Mock(); mlmod.ml_service.predict_severity.return_value = {'predicted_severity': 'HIGH'}
        self.patcher = patch.dict(sys.modules, {'app.tasks.celery_app': taskmod, 'app.services.ml_service': mlmod})
        self.patcher.start()
        path = Path(__file__).parents[1] / 'app/tasks/scan_tasks.py'
        spec = importlib.util.spec_from_file_location('test_recovery_scan_worker', path)
        self.worker = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.worker)
        self.worker.SessionLocal = self.session
        self.scanners = []
        for name in ['S3Scanner', 'EC2Scanner', 'IAMScanner', 'RDSScanner', 'LambdaScanner', 'VPCScanner', 'CloudTrailScanner']:
            cls = Mock(); cls.return_value.scan.return_value = []; cls.return_value.get_compliance_checks.return_value = []
            setattr(self.worker, name, cls); self.scanners.append(cls)
        with patch.dict(sys.modules, {'app.tasks.scan_tasks': self.worker}):
            path = Path(__file__).parents[1] / 'app/services/scan_service.py'
            spec = importlib.util.spec_from_file_location('test_recovery_scan_service', path)
            self.service_module = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.service_module)
        self.service = self.service_module.scan_service

    def tearDown(self):
        self.patcher.stop(); self.engine.dispose()

    def add_scan(self, sid, **kw):
        db = self.session()
        db.add(Scan(id=sid, organization_id='org', cloud_account_id='account', **kw))
        db.commit(); db.close()

    def row(self, sid):
        db = self.session(); row = db.get(Scan, sid)
        state = (row.status, row.started_at, row.completed_at); db.close(); return state

    def test_stale_running_scan_is_recovered_as_failed(self):
        self.add_scan('stale', status='RUNNING', progress=35.0, started_at=NOW - timedelta(hours=2), created_at=NOW - timedelta(hours=2))
        self.assertEqual(self.service.recover_interrupted_scans(self.session(), now=NOW), 1)
        status, started_at, completed_at = self.row('stale')
        self.assertEqual(status, 'FAILED')
        self.assertEqual(completed_at, NOW)
        self.assertEqual(started_at, NOW - timedelta(hours=2))

    def test_fresh_running_scan_is_never_touched(self):
        self.add_scan('fresh', status='RUNNING', progress=35.0, started_at=NOW - timedelta(minutes=5), created_at=NOW - timedelta(minutes=6))
        self.assertEqual(self.service.recover_interrupted_scans(self.session(), now=NOW), 0)
        self.assertEqual(self.row('fresh'), ('RUNNING', NOW - timedelta(minutes=5), None))

    def test_legacy_row_without_start_time_falls_back_to_creation_time(self):
        self.add_scan('legacy-old', status='RUNNING', progress=20.0, started_at=None, created_at=NOW - timedelta(hours=3))
        self.add_scan('legacy-new', status='RUNNING', progress=20.0, started_at=None, created_at=NOW - timedelta(minutes=2))
        self.assertEqual(self.service.recover_interrupted_scans(self.session(), now=NOW), 1)
        self.assertEqual(self.row('legacy-old')[0], 'FAILED')
        self.assertEqual(self.row('legacy-new'), ('RUNNING', None, None))

    def test_terminal_and_pending_states_are_ignored_even_when_old(self):
        old = NOW - timedelta(days=2)
        for sid, status in [('p', 'PENDING'), ('c', 'COMPLETED'), ('d', 'DEMO_COMPLETED'), ('f', 'FAILED')]:
            self.add_scan(sid, status=status, started_at=old, created_at=old)
        self.assertEqual(self.service.recover_interrupted_scans(self.session(), now=NOW), 0)
        for sid, status in [('p', 'PENDING'), ('c', 'COMPLETED'), ('d', 'DEMO_COMPLETED'), ('f', 'FAILED')]:
            self.assertEqual(self.row(sid)[0], status)

    def test_recovered_scan_can_be_claimed_and_completed_by_a_later_delivery(self):
        self.add_scan('stuck', status='RUNNING', progress=65.0, started_at=NOW - timedelta(hours=1), created_at=NOW - timedelta(hours=1))
        self.assertEqual(self.service.recover_interrupted_scans(self.session(), now=NOW), 1)
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(), 'stuck', 'account', 'org'))
        db = self.session(); row = db.get(Scan, 'stuck')
        self.assertEqual(row.status, 'DEMO_COMPLETED')
        self.assertEqual(row.progress, 100.0)
        # The new claim re-recorded started_at with the real clock, replacing the stale value.
        self.assertNotEqual(row.started_at, NOW - timedelta(hours=1))
        self.assertGreaterEqual(row.completed_at, row.started_at)
        db.close()

    def test_claim_records_start_time_before_scanners_run(self):
        self.add_scan('one')
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(), 'one', 'account', 'org'))
        db = self.session(); row = db.get(Scan, 'one')
        self.assertIsNotNone(row.started_at)
        self.assertLessEqual(row.started_at, row.completed_at)
        db.close()


class SweeperConfigTests(unittest.TestCase):
    def test_soft_time_limit_precedes_hard_limit_and_sweeper_is_registered(self):
        source = (Path(__file__).parents[1] / 'app/tasks/celery_app.py').read_text()
        self.assertIn('task_soft_time_limit=1740', source)
        self.assertIn('task_time_limit=1800', source)
        self.assertIn('reap-interrupted-scans', source)
        self.assertIn('app.tasks.scan_tasks.reap_interrupted_scans', source)
        worker = (Path(__file__).parents[1] / 'app/tasks/scan_tasks.py').read_text()
        self.assertIn('def reap_interrupted_scans', worker)
        self.assertIn('recover_interrupted_scans', worker)


if __name__ == '__main__':
    unittest.main()
