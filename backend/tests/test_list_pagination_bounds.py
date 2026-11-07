"""Paging bounds on list endpoints with isolated services only. No AWS endpoint is contacted."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.config.database import get_db
import app.database.models  # keep models registered across isolated endpoint loads

ENDPOINTS = Path(__file__).parents[1] / 'app/api/v1/endpoints'


def load_module(name, path, modules):
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def fake_deps():
    deps = types.ModuleType('app.api.deps')
    deps.get_current_user = lambda: types.SimpleNamespace(organization_id='org', email='synthetic@example.com')
    return deps


class ListPagingBoundsTests(unittest.TestCase):
    def make_client(self, module, prefix):
        app = FastAPI()
        app.include_router(module.router, prefix=prefix)
        app.dependency_overrides[get_db] = lambda: Mock()
        return TestClient(app)

    def test_scan_history_defaults_and_explicit_paging_reach_service(self):
        service = types.ModuleType('app.services.scan_service')
        service.scan_service = Mock()
        service.scan_service.list_scans.return_value = []
        service.ScanDispatchUnknown = type('ScanDispatchUnknown', (RuntimeError,), {})
        module = load_module('test_scans_paging', ENDPOINTS / 'scans.py',
                             {'app.api.deps': fake_deps(), 'app.services.scan_service': service})
        client = self.make_client(module, '/scans')
        try:
            result = client.get('/scans')
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(service.scan_service.list_scans.call_args.args[2:], (0, 50))
            result = client.get('/scans', params={'skip': 5, 'limit': 10})
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(service.scan_service.list_scans.call_args.args[2:], (5, 10))
        finally:
            client.close()

    def test_vulnerability_list_defaults_reach_service(self):
        service = types.ModuleType('app.services.scan_service')
        service.scan_service = Mock()
        service.scan_service.list_vulnerabilities.return_value = []
        ml = types.ModuleType('app.services.ml_service')
        ml.ml_service = Mock()
        module = load_module('test_vulns_paging', ENDPOINTS / 'vulnerabilities.py',
                             {'app.api.deps': fake_deps(), 'app.services.scan_service': service,
                              'app.services.ml_service': ml})
        client = self.make_client(module, '/vulnerabilities')
        try:
            result = client.get('/vulnerabilities')
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(service.scan_service.list_vulnerabilities.call_args.args[2:], (None, None, 0, 50))
        finally:
            client.close()

    def test_out_of_range_paging_rejected_before_touching_services(self):
        service = types.ModuleType('app.services.scan_service')
        service.scan_service = Mock()
        service.scan_service.list_scans.return_value = []
        service.ScanDispatchUnknown = type('ScanDispatchUnknown', (RuntimeError,), {})
        module = load_module('test_scans_paging_reject', ENDPOINTS / 'scans.py',
                             {'app.api.deps': fake_deps(), 'app.services.scan_service': service})
        client = self.make_client(module, '/scans')
        try:
            for params in ({'skip': -1}, {'limit': 0}, {'limit': -5}, {'limit': 201}, {'limit': 10**9}):
                with self.subTest(params=params):
                    result = client.get('/scans', params=params)
                    self.assertEqual(result.status_code, 422, result.text)
            service.scan_service.list_scans.assert_not_called()
        finally:
            client.close()


if __name__ == '__main__':
    unittest.main()
