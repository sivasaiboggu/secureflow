"""No AWS calls: every SDK client is a mock with synthetic credentials."""
import unittest
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError
from app.scanners.base import ScanUnavailable
from app.scanners.aws.s3 import S3Scanner
from app.scanners.aws.ec2 import EC2Scanner
from app.scanners.aws.iam import IAMScanner
from app.scanners.aws.rds_scanner import RDSScanner
from app.scanners.aws.lambda_scanner import LambdaScanner
from app.scanners.aws.vpc_scanner import VPCScanner
from app.scanners.aws.cloudtrail_scanner import CloudTrailScanner

SCANNERS = [S3Scanner, EC2Scanner, IAMScanner, RDSScanner, LambdaScanner, VPCScanner, CloudTrailScanner]
CREDS = {'aws_access_key_id': 'synthetic-key', 'aws_secret_access_key': 'synthetic-secret'}

def denied():
    return ClientError({'Error': {'Code': 'AccessDenied', 'Message': 'private-provider-detail'}}, 'SyntheticCheck')

class ScannerModeTests(unittest.TestCase):
    def test_missing_credentials_never_silently_select_demo(self):
        with patch('boto3.Session') as session:
            for cls in SCANNERS:
                with self.subTest(scanner=cls.__name__), self.assertRaises(ScanUnavailable):
                    cls('org', 'account', {})
            session.assert_not_called()

    def test_explicit_demo_has_no_client_and_labels_every_finding(self):
        with patch('boto3.Session') as session:
            for cls in SCANNERS:
                with self.subTest(scanner=cls.__name__):
                    findings = cls('org', 'demo', {'scan_mode': 'demo'}).scan()
                    self.assertGreater(len(findings), 0)
                    for finding in findings:
                        self.assertTrue(finding['title'].startswith('[DEMO]'))
                        self.assertTrue(finding['evidence']['synthetic'])
                        self.assertEqual(finding['evidence']['scan_mode'], 'demo')
            session.assert_not_called()

    def test_client_initialization_failure_does_not_fabricate_findings(self):
        with patch('boto3.Session', side_effect=RuntimeError('private-provider-detail')):
            for cls in SCANNERS:
                with self.subTest(scanner=cls.__name__), self.assertRaises(ScanUnavailable) as error:
                    cls('org', 'account', CREDS)
                self.assertNotIn('private-provider-detail', str(error.exception))

    def test_provider_listing_failure_is_not_demo_or_a_pass(self):
        for cls in SCANNERS:
            client = Mock()
            for operation in ['list_buckets', 'describe_instances', 'list_users', 'describe_db_instances', 'list_functions', 'describe_vpcs', 'describe_trails']:
                getattr(client, operation).side_effect = denied()
            with self.subTest(scanner=cls.__name__), patch('boto3.Session') as session:
                session.return_value.client.return_value = client
                scanner = cls('org', 'account', CREDS)
                with self.assertRaises(ScanUnavailable):
                    scanner.scan()
                self.assertEqual(scanner.findings, [])
                self.assertFalse(scanner.is_simulated)

    def test_unreadable_s3_resource_check_does_not_pass(self):
        with patch('boto3.Session') as session:
            client = session.return_value.client.return_value
            scanner = S3Scanner('org', 'account', CREDS)
            checks = {'_check_public_access_block':'get_public_access_block', '_check_bucket_acl':'get_bucket_acl', '_check_bucket_policy':'get_bucket_policy', '_check_encryption':'get_bucket_encryption', '_check_versioning':'get_bucket_versioning', '_check_logging':'get_bucket_logging', '_check_ssl_enforcement':'get_bucket_policy'}
            for check, operation in checks.items():
                getattr(client, operation).side_effect = denied()
                with self.subTest(check=check), self.assertRaises(ScanUnavailable):
                    getattr(scanner, check)('synthetic-bucket')

    def test_empty_real_s3_listing_remains_real(self):
        with patch('boto3.Session') as session:
            session.return_value.client.return_value.list_buckets.return_value = {'Buckets': []}
            scanner = S3Scanner('org', 'account', CREDS)
            self.assertEqual(scanner.scan(), [])
            self.assertFalse(scanner.is_simulated)

    def test_iam_mfa_finding_uses_valid_arguments(self):
        with patch('boto3.Session') as session:
            client = session.return_value.client.return_value
            client.list_mfa_devices.return_value = {'MFADevices': []}
            client.list_access_keys.return_value = {'AccessKeyMetadata': []}
            scanner = IAMScanner('org', 'account', CREDS)
            finding = scanner._scan_user('synthetic-user')[0]
            self.assertEqual(finding['vulnerability_type'], 'IAM_USER_MFA_DISABLED')
            self.assertEqual(finding['resource_name'], 'synthetic-user')

    def test_session_token_is_forwarded(self):
        with patch('boto3.Session') as session:
            S3Scanner('org', 'account', {**CREDS, 'aws_session_token':'synthetic-session'})
            self.assertEqual(session.call_args.kwargs['aws_session_token'], 'synthetic-session')
