"""Organization user directory route: real rows only, tenant-scoped. Isolated SQLite."""
import importlib.util
from datetime import datetime
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base, get_db
from app.database.models import Organization, User

class UserRouteTests(unittest.TestCase):
    def setUp(self):
        deps = types.ModuleType('app.api.deps')
        deps.get_current_user = lambda: types.SimpleNamespace(id='u1', organization_id='org', email='founder@example.com')
        with patch.dict(sys.modules, {'app.api.deps': deps}):
            path = Path(__file__).parents[1] / 'app/api/v1/endpoints/users.py'
            spec = importlib.util.spec_from_file_location('test_real_user_routes', path)
            module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add_all([Organization(id='org', name='Synthetic'), Organization(id='other', name='Other')])
        self.db.add_all([
            User(id='u1', email='founder@example.com', hashed_password='x', full_name='Founder One', role='admin', organization_id='org', is_active=True, created_at=datetime(2026, 1, 1)),
            User(id='u2', email='second@example.com', hashed_password='x', full_name='Second Member', role='user', organization_id='org', is_active=True, created_at=datetime(2026, 1, 2)),
            User(id='u3', email='outsider@example.com', hashed_password='x', full_name='Outside Person', role='admin', organization_id='other', is_active=True, created_at=datetime(2026, 1, 3)),
        ])
        self.db.commit()
        app = FastAPI(); app.include_router(module.router, prefix='/users')
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close(); self.db.close(); self.engine.dispose()

    def test_lists_only_the_callers_organization(self):
        result = self.client.get('/users')
        self.assertEqual(result.status_code, 200, result.text)
        body = result.json()
        self.assertEqual([u['email'] for u in body], ['founder@example.com', 'second@example.com'])
        self.assertNotIn('outsider', result.text)

    def test_response_never_contains_password_material(self):
        result = self.client.get('/users')
        self.assertNotIn('hashed_password', result.text)

    def test_empty_organization_returns_an_empty_list(self):
        self.db.query(User).delete(); self.db.commit()
        result = self.client.get('/users')
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json(), [])


if __name__ == '__main__':
    unittest.main()
