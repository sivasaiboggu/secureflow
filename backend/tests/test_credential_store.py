"""Generated disposable keys and synthetic credentials only. No AWS calls."""
import base64
import copy
import json
import os
import unittest
from unittest.mock import patch
from app.security.credential_store import seal_credentials, open_credentials, CredentialStorageError

CREDS={'aws_access_key_id':'synthetic-access','aws_secret_access_key':'synthetic-secret',
       'aws_session_token':'synthetic-session','aws_default_region':'us-east-1'}

class CredentialStoreTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()})
        self.env.start();self.addCleanup(self.env.stop)
    def seal(self):return seal_credentials(CREDS,'account','org','aws')
    def test_roundtrip_and_no_plaintext_in_envelope(self):
        envelope=self.seal()
        for value in CREDS.values():self.assertNotIn(value,json.dumps(envelope))
        self.assertEqual(open_credentials(envelope,'account','org','aws'),{**CREDS,'scan_mode':'real'})
    def test_fresh_nonce_each_time(self):
        self.assertNotEqual(self.seal(),self.seal())
    def test_tampering_wrong_key_and_wrong_context_fail_closed(self):
        envelope=self.seal()
        for context in [('different','org','aws'),('account','other','aws'),('account','org','azure')]:
            with self.assertRaises(CredentialStorageError):open_credentials(envelope,*context)
        bad=copy.deepcopy(envelope);bad['ciphertext']='AAAA'
        with self.assertRaises(CredentialStorageError):open_credentials(bad,'account','org','aws')
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':base64.b64encode(os.urandom(32)).decode()}):
            with self.assertRaises(CredentialStorageError):open_credentials(envelope,'account','org','aws')
    def test_missing_invalid_key_never_saves_plaintext(self):
        for key in ['', 'bad',base64.b64encode(b'short').decode()]:
            with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':key}),self.assertRaises(CredentialStorageError):self.seal()
    def test_demo_discards_secrets_without_a_key(self):
        with patch.dict(os.environ,{'CLOUD_CREDENTIALS_KEY':''}):
            self.assertEqual(seal_credentials({**CREDS,'scan_mode':'demo'},'a','o','aws'),{'scan_mode':'demo'})
            self.assertEqual(open_credentials({'scan_mode':'demo'},'a','o','aws'),{'scan_mode':'demo'})
    def test_plaintext_or_secret_bearing_demo_is_not_silently_read(self):
        for value in [CREDS,{**CREDS,'scan_mode':'demo'},None,{}]:
            with self.assertRaises(CredentialStorageError):open_credentials(value,'a','o','aws')
