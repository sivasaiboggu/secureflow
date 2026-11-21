"""Application entrypoint: working readiness probe, honest API contract, private failures."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from fastapi import APIRouter
from fastapi.testclient import TestClient

SECRET = 'PRIVATE_DB_USER_HOST_DSN'

def load_main():
    """Load app/main.py without the cloud/model router import chain.

    Only the router module itself is stubbed. (A previous version used
    ``patch.dict(sys.modules, ...)`` around the exec, which restores
    ``sys.modules`` on exit and evicts every module imported during the
    exec — ``app.config.database``, ``psycopg`` and the SQLAlchemy
    dialect included. The loaded app then kept the first-import engine
    while ``/ready`` re-imported a second ``psycopg`` module, whose
    ``Connection`` class failed the first engine's ``isinstance`` check
    (``TypeError: expected Connection or AsyncConnection``), so the
    readiness probe 503'd even with a working database.)
    """
    router = types.ModuleType('app.api.v1.router')
    router.api_router = APIRouter()
    _sentinel = object()
    old = sys.modules.get('app.api.v1.router', _sentinel)
    sys.modules['app.api.v1.router'] = router
    try:
        path = Path(__file__).parents[1] / 'app/main.py'
        spec = importlib.util.spec_from_file_location('test_app_entrypoint_main', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    finally:
        if old is _sentinel:
            sys.modules.pop('app.api.v1.router', None)
        else:
            sys.modules['app.api.v1.router'] = old
    return module

class EntrypointTests(unittest.TestCase):
    def test_readiness_reports_ready_with_a_working_database(self):
        module = load_main()
        client = TestClient(module.app)
        result = client.get('/ready')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), {'status': 'ready'})
        client.close()

    def test_readiness_failure_never_leaks_driver_details(self):
        module = load_main()
        broken = Mock()
        broken.execute.side_effect = RuntimeError(SECRET)
        with patch('app.config.database.SessionLocal', return_value=broken):
            client = TestClient(module.app)
            result = client.get('/ready')
            client.close()
        self.assertEqual(result.status_code, 503, result.text)
        self.assertEqual(result.json(), {'status': 'not ready'})
        self.assertNotIn(SECRET, result.text)
        self.assertNotIn('error', result.json())

    def test_api_contract_does_not_claim_ai_powered_or_repairs(self):
        source = (Path(__file__).parents[1] / 'app/main.py').read_text()
        self.assertNotIn('AI-Powered', source)
        self.assertIn('research prototype', source)
        self.assertIn('review-only remediation plans', source)

    def test_startup_table_failure_log_stays_sanitized(self):
        source = (Path(__file__).parents[1] / 'app/main.py').read_text()
        self.assertNotIn('f"Error creating database tables: {e}"', source)


if __name__ == '__main__':
    unittest.main()
