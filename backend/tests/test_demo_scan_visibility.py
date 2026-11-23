"""Demo scans are finished scans: compliance, forecast and list bounds.

A DEMO_COMPLETED scan used to be invisible to the compliance summary, the
pass-rate history behind the forecast, and the dashboard score/trend — the
dashboard showed empty states after every demo scan even though checks had
been evaluated. The two growing list endpoints also returned every row
with no pagination. Isolated SQLite only.
"""
import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.database.models import (
    Organization, CloudAccount, Scan, Vulnerability, ComplianceCheck, Remediation, AuditLog,
)
from app.services.analytics_service import analytics_service

BASE = datetime(2026, 10, 1, 9, 0, 0)


def load_endpoint(name, filename):
    """Load one real endpoint module with get_current_user stubbed."""
    deps = types.ModuleType('app.api.deps')
    deps.get_current_user = lambda: types.SimpleNamespace(
        id='u1', organization_id='org', email='founder@example.com')
    with patch.dict(sys.modules, {'app.api.deps': deps}):
        path = Path(__file__).parents[1] / 'app/api/v1/endpoints' / filename
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


class DemoScanVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Organization(id='org', name='Synthetic'))
        self.db.add(CloudAccount(id='account', name='Demo', provider='aws',
                                 organization_id='org', credentials={'scan_mode': 'demo'},
                                 is_active=True))
        self.db.commit()
        compliance = load_endpoint('test_real_compliance_routes', 'compliance.py')
        remediation = load_endpoint('test_real_remediation_routes', 'remediation.py')
        findings = load_endpoint('test_real_finding_routes', 'vulnerabilities.py')
        app = FastAPI()
        app.include_router(compliance.router, prefix='/compliance')
        app.include_router(remediation.router, prefix='/remediation')
        app.include_router(findings.router, prefix='/vulnerabilities')
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def _scan(self, sid, status, passed, failed, offset_days):
        self.db.add(Scan(id=sid, cloud_account_id='account', organization_id='org',
                         status=status, passed_checks=passed, failed_checks=failed,
                         completed_at=BASE + timedelta(days=offset_days)))
        self.db.commit()

    def _check(self, cid, scan_id, framework, status, offset_hours=0):
        self.db.add(ComplianceCheck(
            id=cid, scan_id=scan_id, framework=framework, control_id='1.1',
            title='Synthetic control', status=status, resource_id='r1',
            checked_at=BASE + timedelta(hours=offset_hours)))
        self.db.commit()

    def test_compliance_summary_uses_latest_demo_scan(self):
        self._scan('s1', 'DEMO_COMPLETED', 3, 1, 1)
        self._check('c1', 's1', 'CIS', 'PASS')
        self._check('c2', 's1', 'CIS', 'FAIL')
        self._check('c3', 's1', 'CIS', 'PASS')
        result = self.client.get('/compliance/summary')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), {'CIS': 66.67})

    def test_compliance_summary_empty_when_only_failed_scans(self):
        self._scan('s1', 'FAILED', 0, 0, 1)
        self._check('c1', 's1', 'CIS', 'PASS')
        result = self.client.get('/compliance/summary')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), {})

    def test_pass_rates_include_demo_scans(self):
        self._scan('s1', 'DEMO_COMPLETED', 8, 2, 2)
        self._scan('s2', 'FAILED', 9, 1, 3)
        self._scan('s3', 'COMPLETED', 5, 5, 1)
        points = analytics_service.get_scan_pass_rates(self.db, 'org')
        self.assertEqual([p['score'] for p in points], [50.0, 80.0])

    def test_compliance_checks_honor_limit_and_skip(self):
        self._scan('s1', 'DEMO_COMPLETED', 3, 1, 1)
        for i in range(5):
            self._check(f'c{i}', 's1', 'CIS', 'PASS', offset_hours=i)
        page1 = self.client.get('/compliance/checks?limit=2')
        self.assertEqual(page1.status_code, 200, page1.text)
        self.assertEqual(len(page1.json()), 2)
        # Newest first: the last-written check leads.
        self.assertEqual(page1.json()[0]['id'], 'c4')
        page2 = self.client.get('/compliance/checks?limit=2&skip=2')
        self.assertEqual([c['id'] for c in page2.json()], ['c2', 'c1'])
        over = self.client.get('/compliance/checks?limit=500')
        self.assertEqual(over.status_code, 422, over.text)

    def test_policy_scope_distinguishes_sample_controls_and_resource_evidence(self):
        self._scan('s1', 'DEMO_COMPLETED', 1, 1, 1)
        self._scan('s2', 'FAILED', 0, 0, 2)
        self._check('failed', 's1', 'CIS', 'FAIL')
        self._check('old-evidence', 's1', 'CIS', 'FAIL')
        self._check('passed', 's1', 'CIS', 'PASS')
        self._check('unfinished', 's2', 'CIS', 'FAIL')
        self.db.get(ComplianceCheck, 'failed').evidence = {
            'control_level': True, 'violating_resources': ['r1', 'r2'],
        }
        self.db.commit()
        result = self.client.get('/compliance/checks', params={'scan_id': 's1', 'status': 'fail'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual([row['id'] for row in result.json()], ['failed', 'old-evidence'])
        first, legacy = result.json()
        self.assertTrue(first['sample'])
        self.assertTrue(first['control_level'])
        self.assertEqual(first['violating_resources'], ['r1', 'r2'])
        self.assertFalse(legacy['control_level'])
        self.assertEqual(legacy['violating_resources'], [])
        finished = self.client.get('/compliance/checks?finished_only=true').json()
        self.assertNotIn('unfinished', [row['id'] for row in finished])

    def test_triage_is_audited_conflict_checked_and_tenant_scoped(self):
        self._scan('s1', 'COMPLETED', 0, 0, 1)
        self.db.add(Organization(id='other-org', name='Other'))
        self.db.add(Scan(id='s2', organization_id='other-org', cloud_account_id='account'))
        for finding_id, scan_id in [('mine', 's1'), ('foreign', 's2')]:
            self.db.add(Vulnerability(id=finding_id, scan_id=scan_id, resource_id='100%private',
                                      resource_type='S3', vulnerability_type='PUBLIC', severity='HIGH',
                                      cvss_score=8, title='Bucket finding'))
        self.db.add(Vulnerability(id='second', scan_id='s1', resource_id='100Xprivate',
                                  resource_type='S3', vulnerability_type='PUBLIC', severity='HIGH',
                                  cvss_score=8, title='Bucket finding'))
        self.db.commit()
        searched = self.client.get('/vulnerabilities', params={'search': '%PRI'}).json()
        self.assertEqual([row['id'] for row in searched], ['mine'])
        second_page = self.client.get('/vulnerabilities', params={'search': 'bucket', 'skip': 1, 'limit': 1}).json()
        self.assertEqual([row['id'] for row in second_page], ['second'])
        change = {'status': 'IN_PROGRESS', 'expected_status': 'OPEN'}
        self.assertEqual(self.client.patch('/vulnerabilities/foreign/triage', json=change).status_code, 404)
        path = '/vulnerabilities/mine/triage'
        self.assertEqual(self.client.patch(path, json={**change, 'status': 'BAD'}).status_code, 422)
        saved = self.client.patch(path, json=change)
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()['status'], 'IN_PROGRESS')
        self.assertEqual(self.client.patch(path, json=change).status_code, 200)
        self.assertEqual(self.client.patch(path, json={**change, 'status': 'IGNORED'}).status_code, 409)
        audit = self.db.query(AuditLog).one()
        self.assertEqual(audit.user_id, 'u1')
        self.assertEqual(audit.details, {'vulnerability_id': 'mine', 'old_status': 'OPEN', 'new_status': 'IN_PROGRESS'})

    def test_remediation_history_honors_limit(self):
        self._scan('s1', 'COMPLETED', 0, 0, 1)
        self.db.add(Vulnerability(id='v1', scan_id='s1', resource_id='b1',
                                  resource_type='S3_BUCKET', vulnerability_type='PUBLIC',
                                  severity='HIGH', cvss_score=8.0, title='Finding'))
        for i in range(3):
            self.db.add(Remediation(id=f'r{i}', vulnerability_id='v1',
                                    remediation_type='TERRAFORM', code='x = 1',
                                    status='PENDING'))
        self.db.commit()
        result = self.client.get('/remediation/history?limit=2')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(len(result.json()), 2)
        result = self.client.get('/remediation/history?limit=2&skip=2')
        self.assertEqual(len(result.json()), 1)


if __name__ == '__main__':
    unittest.main()
