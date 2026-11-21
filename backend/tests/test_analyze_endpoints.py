"""Analysis endpoints: authenticated, and client errors stay 400s. SQLite only."""
import importlib.util
from pathlib import Path
import types
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.api.deps import get_current_user
from app.database.models import Organization


class AnalyzeEndpointTests(unittest.TestCase):
    def load_app(self):
        path = Path(__file__).parents[1] / 'app/api/v1/endpoints/vulnerabilities.py'
        spec = importlib.util.spec_from_file_location('test_real_analyze_endpoints', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.module = module
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(Organization(id='org', name='Synthetic'))
        self.db.commit()
        self.app = FastAPI()
        self.app.include_router(module.router, prefix='/api')
        self.app.dependency_overrides[get_db] = lambda: self.db
        return TestClient(self.app)

    def tearDown(self):
        if hasattr(self, 'db'):
            self.db.close()
            self.engine.dispose()

    def authenticated(self, client):
        self.app.dependency_overrides[get_current_user] = lambda: types.SimpleNamespace(
            organization_id='org', email='synthetic@example.com')
        return client

    def test_analyze_log_requires_authentication(self):
        result = self.load_app().post('/api/analyze-log', json={'log_payload': 'test event'})
        self.assertEqual(result.status_code, 401, result.text)

    def test_analyze_metrics_requires_authentication(self):
        result = self.load_app().post(
            '/api/analyze-metrics', json={'metrics': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]})
        self.assertEqual(result.status_code, 401, result.text)

    def test_analyze_metrics_wrong_count_is_400_not_500(self):
        client = self.authenticated(self.load_app())
        result = client.post('/api/analyze-metrics', json={'metrics': [0.1, 0.2]})
        self.assertEqual(result.status_code, 400, result.text)
        self.assertIn('eight', result.json()['detail'])

    def test_analyze_metrics_eight_values_reports_unavailable_detector_honestly(self):
        client = self.authenticated(self.load_app())
        result = client.post(
            '/api/analyze-metrics', json={'metrics': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()['method'], 'unavailable')
        self.assertIsNone(result.json()['is_anomaly'])

    def test_analyze_log_flags_suspicious_keyword(self):
        client = self.authenticated(self.load_app())
        result = client.post('/api/analyze-log', json={'log_payload': 'user called delete_bucket on prod backups'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertTrue(result.json()['is_threat'])

    def test_list_rejects_unknown_severity_and_status(self):
        client = self.authenticated(self.load_app())
        result = client.get('/api', params={'severity': 'BOGUS'})
        self.assertEqual(result.status_code, 400, result.text)
        result = client.get('/api', params={'status': 'BOGUS'})
        self.assertEqual(result.status_code, 400, result.text)

    def test_list_accepts_known_filters(self):
        client = self.authenticated(self.load_app())
        result = client.get('/api', params={'severity': 'HIGH', 'status': 'OPEN'})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), [])


if __name__ == '__main__':
    unittest.main()
