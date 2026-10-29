"""Remediation review-plan routes: error privacy and truthful contract. SQLite + mocked service only."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.database.models import Organization

SECRET = 'PRIVATE_SQL_PARAMETERS_OR_PROVIDER_URL'

class RemediationRouteTests(unittest.TestCase):
    def load_app(self, endpoint_name):
        deps = types.ModuleType('app.api.deps')
        deps.get_current_user = lambda: types.SimpleNamespace(organization_id='org', email='synthetic@example.com')
        self.service = types.ModuleType('app.services.scan_service')
        self.service.scan_service = Mock()
        mlmod = types.ModuleType('app.services.ml_service')
        mlmod.ml_service = Mock()
        with patch.dict(sys.modules, {'app.api.deps': deps, 'app.services.scan_service': self.service, 'app.services.ml_service': mlmod}):
            path = Path(__file__).parents[1] / f'app/api/v1/endpoints/{endpoint_name}'
            spec = importlib.util.spec_from_file_location(f'test_routes_{endpoint_name}', path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Organization(id='org', name='Synthetic')); self.db.commit()
        app = FastAPI(); app.include_router(module.router, prefix='/api')
        app.dependency_overrides[get_db] = lambda: self.db
        return TestClient(app)

    def tearDown(self):
        if hasattr(self, 'db'):
            self.db.close(); self.engine.dispose()

    def check_500_privacy(self, client, url):
        self.service.scan_service.apply_remediation.side_effect = RuntimeError(SECRET)
        result = client.post(url, json={'vulnerability_id': 'synthetic-finding'})
        self.assertEqual(result.status_code, 500, result.text)
        self.assertNotIn(SECRET, result.text)
        self.assertEqual(result.json()['detail'], 'The remediation plan could not be saved. Review the finding and try again.')

    def check_400_keeps_intended_validation_message(self, client, url):
        self.service.scan_service.apply_remediation.side_effect = ValueError('No Terraform template is available for review.')
        result = client.post(url, json={'vulnerability_id': 'synthetic-finding'})
        self.assertEqual(result.status_code, 400, result.text)
        self.assertEqual(result.json()['detail'], 'No Terraform template is available for review.')

    def test_apply_endpoint_500_never_leaks_exception_details(self):
        self.check_500_privacy(self.load_app('remediation.py'), '/api/apply')

    def test_apply_endpoint_400_keeps_validation_message(self):
        self.check_400_keeps_intended_validation_message(self.load_app('remediation.py'), '/api/apply')

    def test_remediate_endpoint_500_never_leaks_exception_details(self):
        self.check_500_privacy(self.load_app('vulnerabilities.py'), '/api/remediate')

    def test_remediate_endpoint_400_keeps_validation_message(self):
        self.check_400_keeps_intended_validation_message(self.load_app('vulnerabilities.py'), '/api/remediate')

    def test_routes_do_not_claim_execution_in_their_contract(self):
        for name in ['remediation.py', 'vulnerabilities.py']:
            source = (Path(__file__).parents[1] / f'app/api/v1/endpoints/{name}').read_text()
            self.assertNotIn('Executes automated remediation', source)
            self.assertNotIn('tasks executed', source)


if __name__ == '__main__':
    unittest.main()
