"""Regression: Terraform remediation output must never interpolate an
unvalidated resource identifier into HCL, and placeholder account/region
values must be explicit, never a plausible-looking fake ARN."""
import unittest

from app.remediation.terraform_generator import TerraformRemediationGenerator

GEN = TerraformRemediationGenerator()


class TerraformGeneratorTests(unittest.TestCase):
    def test_s3_fix_uses_safe_bucket_name(self):
        code = GEN.generate_s3_block_fix('my.app-bucket')
        self.assertIn('bucket = "my.app-bucket"', code)
        self.assertIn('my_app_bucket_remediated', code)

    def test_quote_in_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            GEN.generate_s3_block_fix('bucket"; malicious = "x')
        with self.assertRaises(ValueError):
            GEN.get_remediation_code('PUBLIC_ACCESS', 'arn:aws:s3:::bad";x')

    def test_interpolation_and_whitespace_are_rejected(self):
        for bad in ('bucket${var.x}', 'bucket; rm -rf /', 'bucket name', ''):
            with self.assertRaises(ValueError, msg=bad):
                GEN.generate_s3_encryption_fix(bad)

    def test_flow_logs_placeholders_are_explicit(self):
        code = GEN.generate_vpc_flow_logs_fix('vpc-123abc')
        self.assertNotIn('your-account', code)
        self.assertIn('REPLACE_WITH_ACCOUNT_ID', code)
        self.assertIn('REPLACE_WITH_REGION', code)

    def test_flow_logs_accepts_real_account_and_region(self):
        code = GEN.generate_vpc_flow_logs_fix('vpc-123abc', account_id='123456789012', region='eu-west-1')
        self.assertIn('arn:aws:iam::123456789012:role/vpc-flow-logs-service-role', code)
        self.assertIn('arn:aws:logs:eu-west-1:123456789012:log-group/vpc-flow-logs', code)

    def test_flow_logs_rejects_malformed_account_and_region(self):
        with self.assertRaises(ValueError):
            GEN.generate_vpc_flow_logs_fix('vpc-123abc', account_id='not-an-account')
        with self.assertRaises(ValueError):
            GEN.generate_vpc_flow_logs_fix('vpc-123abc', region='not a region')

    def test_unknown_category_still_returns_review_note(self):
        code = GEN.get_remediation_code('SOMETHING_ELSE', 'i-0123456789abcdef0')
        self.assertIn('Manual review required', code)

    def test_fallback_comment_cannot_break_out_with_newlines(self):
        # A crafted finding type must not inject plan lines through the
        # `#` comment in the manual-review fallback: the whole value is
        # collapsed onto the one comment line, so no generated line
        # starts a resource block or any other HCL.
        code = GEN.get_remediation_code('EVIL\nresource "aws_s3_bucket" "x" {\n bucket = "pwned"', 'i-0123456789abcdef0')
        non_comment = [line for line in code.splitlines() if line and not line.startswith('#')]
        self.assertEqual(non_comment, [])
        self.assertIn('EVIL resource "aws_s3_bucket" "x" { bucket = "pwned"', code.splitlines()[0])


if __name__ == '__main__':
    unittest.main()
