"""Route matching and credential registration with isolated SQLite only."""
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
from app.database.models import Organization, CloudAccount

class ScanRouteTests(unittest.TestCase):
    def setUp(self):
        deps=types.ModuleType('app.api.deps');deps.get_current_user=lambda: types.SimpleNamespace(organization_id='org')
        service=types.ModuleType('app.services.scan_service');service.scan_service=Mock()
        with patch.dict(sys.modules,{'app.api.deps':deps,'app.services.scan_service':service}):
            path=Path(__file__).parents[1]/'app/api/v1/endpoints/scans.py'
            spec=importlib.util.spec_from_file_location('test_real_scan_routes',path)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)()
        self.db.add(Organization(id='org',name='Synthetic'));self.db.commit()
        app=FastAPI();app.include_router(module.router,prefix='/scans')
        app.dependency_overrides[get_db]=lambda:self.db
        self.client=TestClient(app)
    def tearDown(self):self.client.close();self.db.close();self.engine.dispose()
    def test_cloud_accounts_route_not_shadowed_by_scan_id(self):
        result=self.client.get('/scans/cloud-accounts')
        self.assertEqual(result.status_code,200);self.assertEqual(result.json(),[])
    def test_demo_registration_discards_keys_and_response_has_no_credentials(self):
        result=self.client.post('/scans/cloud-accounts',json={'name':'Demo','provider':'aws','credentials':{'scan_mode':'demo','aws_secret_access_key':'synthetic-not-a-secret'}})
        self.assertEqual(result.status_code,200,result.text)
        self.assertNotIn('credentials',result.json())
        self.assertEqual(self.db.query(CloudAccount).one().credentials,{'scan_mode':'demo'})
    def test_real_missing_keys_and_unsupported_provider_rejected(self):
        for provider,credentials in [('aws',{}),('azure',{'scan_mode':'demo'}),('aws',{'scan_mode':'unknown'})]:
            result=self.client.post('/scans/cloud-accounts',json={'name':'Rejected','provider':provider,'credentials':credentials})
            self.assertEqual(result.status_code,400,result.text)
        self.assertEqual(self.db.query(CloudAccount).count(),0)

    def test_real_registration_requires_key_before_any_write(self):
        with patch.dict('os.environ', {'CLOUD_CREDENTIALS_KEY':''}):
            result=self.client.post('/scans/cloud-accounts',json={'name':'Real','provider':'aws','credentials':{'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'}})
        self.assertEqual(result.status_code,503)
        self.assertNotIn('synthetic-secret',result.text)
        self.assertEqual(self.db.query(CloudAccount).count(),0)

    def test_real_registration_persists_only_authenticated_envelope(self):
        import base64, os, json
        from app.security.credential_store import open_credentials
        credentials={'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret'}
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            result=self.client.post('/scans/cloud-accounts',json={'name':'Real','provider':'aws','credentials':credentials})
            self.assertEqual(result.status_code,200,result.text)
            row=self.db.query(CloudAccount).one()
            self.assertEqual(row.credentials['format'],'aesgcm-v1')
            self.assertNotIn('synthetic-secret',json.dumps(row.credentials))
            self.assertEqual(open_credentials(row.credentials,row.id,'org','aws')['aws_secret_access_key'],'synthetic-secret')
            listed=self.client.get('/scans/cloud-accounts')
            self.assertNotIn('ciphertext',listed.text)
            self.assertNotIn('credentials',listed.text)
