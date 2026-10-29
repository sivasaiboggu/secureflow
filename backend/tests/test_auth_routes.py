"""Registration contract: server-assigned founder role, private failures. Isolated SQLite only."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.database.models import User, Organization

SECRET = 'PRIVATE_DSN_OR_SQL_PARAMETERS'

class AuthRouteTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).parents[1] / 'app/api/v1/endpoints/auth.py'
        spec = importlib.util.spec_from_file_location('test_real_auth_routes', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.module = module
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()
        app = FastAPI(); app.include_router(module.router, prefix='/auth')
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self.client.close(); self.db.close(); self.engine.dispose()

    def payload(self, **kw):
        base = {'email': 'founder@example.com', 'password': 'synthetic-pass-123', 'full_name': 'Synthetic Founder', 'organization_name': 'Synthetic Org'}
        base.update(kw)
        return base

    def test_client_supplied_role_is_never_stored(self):
        result = self.client.post('/auth/register', json=self.payload(role='user'))
        self.assertEqual(result.status_code, 201, result.text)
        user = self.db.query(User).filter(User.email == 'founder@example.com').one()
        self.assertEqual(user.role, 'admin')

    def test_default_registration_assigns_founder_role(self):
        result = self.client.post('/auth/register', json=self.payload())
        self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(self.db.query(User).one().role, 'admin')

    def test_successful_registration_returns_tokens_without_password_material(self):
        result = self.client.post('/auth/register', json=self.payload())
        self.assertEqual(result.status_code, 201, result.text)
        body = result.json()
        self.assertTrue(body['access_token'])
        self.assertTrue(body['refresh_token'])
        self.assertNotIn('hashed_password', result.text)
        self.assertNotIn('synthetic-pass-123', result.text)

    def test_duplicate_email_is_rejected_before_any_write(self):
        self.assertEqual(self.client.post('/auth/register', json=self.payload()).status_code, 201)
        result = self.client.post('/auth/register', json=self.payload())
        self.assertEqual(result.status_code, 400, result.text)
        self.assertEqual(self.db.query(Organization).count(), 1)
        self.assertEqual(self.db.query(User).count(), 1)

    def test_registration_failure_stays_generic_in_response_and_logs(self):
        original_commit = self.db.commit
        def failing_commit():
            raise RuntimeError(SECRET)
        self.db.commit = failing_commit
        try:
            with self.assertLogs(self.module.logger, level='ERROR') as captured:
                result = self.client.post('/auth/register', json=self.payload(email='other@example.com'))
            self.assertEqual(result.status_code, 500, result.text)
            self.assertEqual(result.json()['detail'], 'Registration failed. Check server logs.')
            self.assertNotIn(SECRET, result.text)
            self.assertNotIn(SECRET, ' '.join(captured.output))
        finally:
            self.db.commit = original_commit
        self.db.rollback()
        self.assertEqual(self.db.query(User).count(), 0)


if __name__ == '__main__':
    unittest.main()
