"""Versioned authenticated envelopes for AWS connector secrets.

No key is generated or persisted here. API and workers need the same separately
managed 32-byte key. Legacy plaintext rows are deliberately not auto-migrated.
"""
import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CredentialStorageError(ValueError):
    pass


def _key():
    try:
        raw = base64.b64decode(os.environ.get('CLOUD_CREDENTIALS_KEY', ''), validate=True)
        if len(raw) != 32:
            raise ValueError()
        return raw
    except (ValueError, TypeError):
        raise CredentialStorageError('Cloud credential storage key is not configured correctly.') from None


def _context(account_id, organization_id, provider):
    return json.dumps([str(account_id), str(organization_id), str(provider).lower()],
                      separators=(',', ':')).encode()


def seal_credentials(credentials, account_id, organization_id, provider):
    if credentials.get('scan_mode') == 'demo':
        return {'scan_mode': 'demo'}
    allowed = {'aws_access_key_id', 'aws_secret_access_key', 'aws_session_token', 'aws_default_region'}
    value = {k: v for k, v in credentials.items() if k in allowed and v is not None}
    if not all(isinstance(value.get(k), str) and value[k].strip()
               for k in ('aws_access_key_id', 'aws_secret_access_key')):
        raise CredentialStorageError('AWS credentials are required for a real connector.')
    if any(not isinstance(v, str) for v in value.values()):
        raise CredentialStorageError('AWS credential fields must be text.')
    nonce = os.urandom(12)
    ciphertext = AESGCM(_key()).encrypt(nonce, json.dumps(value, separators=(',', ':')).encode(),
                                      _context(account_id, organization_id, provider))
    return {'scan_mode': 'real', 'format': 'aesgcm-v1',
            'nonce': base64.b64encode(nonce).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode()}


def open_credentials(envelope, account_id, organization_id, provider):
    if not isinstance(envelope, dict):
        raise CredentialStorageError('Cloud credentials are unavailable.')
    if envelope == {'scan_mode': 'demo'}:
        return {'scan_mode': 'demo'}
    if envelope.get('format') != 'aesgcm-v1' or envelope.get('scan_mode') != 'real':
        raise CredentialStorageError('Legacy cloud credentials require an explicit secure re-registration.')
    key = _key()
    try:
        nonce = base64.b64decode(envelope['nonce'], validate=True)
        ciphertext = base64.b64decode(envelope['ciphertext'], validate=True)
        value = json.loads(AESGCM(key).decrypt(nonce, ciphertext,
                           _context(account_id, organization_id, provider)))
        if not isinstance(value, dict) or not all(isinstance(value.get(k), str) and value[k].strip()
                for k in ('aws_access_key_id', 'aws_secret_access_key')):
            raise ValueError()
        return {**value, 'scan_mode': 'real'}
    except Exception:
        raise CredentialStorageError('Cloud credentials could not be verified. Check configuration or re-register securely.') from None
