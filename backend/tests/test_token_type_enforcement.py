"""Token-type contract: only access tokens authenticate API calls. Isolated SQLite only."""
import unittest
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.api.v1.dependencies import get_current_active_user
from app.config.database import Base, get_db
from app.config.settings import settings
from app.core.exceptions import CustomException
from app.core.security import create_access_token, create_refresh_token
from app.database.models import Organization, User


class TokenTypeEnforcementTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db = self.session_factory()
        self.db.add(Organization(id='org-1', name='Synthetic Org'))
        self.db.add(User(id='user-1', email='member@example.com', hashed_password='synthetic-hash',
                         full_name='Synthetic Member', role='admin', organization_id='org-1', is_active=True))
        self.db.commit()

        app = FastAPI()

        @app.exception_handler(CustomException)
        async def custom_exception_handler(request, exc):
            return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

        @app.get('/whoami-main')
        def whoami_main(user: User = Depends(get_current_user)):
            return {'id': user.id}

        @app.get('/whoami-v1')
        def whoami_v1(user: User = Depends(get_current_active_user)):
            return {'id': user.id}

        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self):
        self.client.close()
        self.db.close()
        self.engine.dispose()

    def bearer(self, token):
        return {'Authorization': f'Bearer {token}'}

    def unsigned_type_token(self, token_type):
        claims = {'exp': datetime.utcnow() + timedelta(minutes=5), 'sub': 'user-1'}
        if token_type is not None:
            claims['type'] = token_type
        return jwt.encode(claims, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def test_access_token_authenticates_both_dependencies(self):
        token = create_access_token('user-1')
        for path in ('/whoami-main', '/whoami-v1'):
            result = self.client.get(path, headers=self.bearer(token))
            self.assertEqual(result.status_code, 200, result.text)
            self.assertEqual(result.json()['id'], 'user-1')

    def test_refresh_token_is_rejected_by_both_dependencies(self):
        token = create_refresh_token('user-1')
        for path in ('/whoami-main', '/whoami-v1'):
            result = self.client.get(path, headers=self.bearer(token))
            self.assertEqual(result.status_code, 401, result.text)

    def test_token_without_type_claim_is_rejected(self):
        token = self.unsigned_type_token(None)
        for path in ('/whoami-main', '/whoami-v1'):
            result = self.client.get(path, headers=self.bearer(token))
            self.assertEqual(result.status_code, 401, result.text)

    def test_forged_access_type_still_needs_a_real_user(self):
        token = create_access_token('no-such-user')
        for path in ('/whoami-main', '/whoami-v1'):
            result = self.client.get(path, headers=self.bearer(token))
            self.assertEqual(result.status_code, 401, result.text)


if __name__ == '__main__':
    unittest.main()
