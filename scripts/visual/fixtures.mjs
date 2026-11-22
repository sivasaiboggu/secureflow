// Synthetic records for repeatable browser captures. No live cloud or database access.
const SCANS = [
  { id: 'a1b2c3d4-e5f6-4a5b-8c9d-001122334455', cloud_account_id: 'demo-account-id', status: 'DEMO_COMPLETED', progress: 100, vulnerabilities_found: 5, passed_checks: 1, failed_checks: 7, created_at: '2026-11-21T10:00:00Z', completed_at: '2026-11-21T10:04:00Z' },
  { id: 'b2c3d4e5-f6a7-4b5c-9d0e-112233445566', cloud_account_id: 'prod-account-id', status: 'COMPLETED', progress: 100, vulnerabilities_found: 2, passed_checks: 6, failed_checks: 2, created_at: '2026-11-20T09:00:00Z', completed_at: '2026-11-20T09:05:00Z' },
  { id: 'c3d4e5f6-a7b8-4c5d-0e1f-223344556677', cloud_account_id: 'demo-account-id', status: 'RUNNING', progress: 45, vulnerabilities_found: 0, passed_checks: 0, failed_checks: 0, created_at: '2026-11-22T00:00:00Z', completed_at: null },
];
const TF_S3 = 'resource "aws_s3_bucket_public_access_block" "customer_invoice_uploads_temp_remediated" {\n  bucket = "customer-invoice-uploads-temp"\n\n  block_public_acls       = true\n  block_public_policy     = true\n  ignore_public_acls      = true\n  restrict_public_buckets = true\n}\n';
const VULNS = [
  { id: 'v-1', resource_type: 'S3', resource_id: 'customer-invoice-uploads-temp', resource_name: 'customer-invoice-uploads-temp', vulnerability_type: 'PUBLIC_ACCESS_NOT_BLOCKED', severity: 'CRITICAL', title: 'S3 Bucket Public Access Not Fully Blocked', description: "S3 bucket 'customer-invoice-uploads-temp' is configured with public write/read permissions, allowing global directory exposure.", recommendation: 'Enable all S3 Block Public Access policies immediately at the account or bucket level. Then verify the bucket policy denies public access.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.5', 'PCI-DSS 3.4'], cvss_score: 9.8, status: 'OPEN', evidence: {} },
  { id: 'v-2', resource_type: 'S3', resource_id: 'corp-internal-wiki-docs', resource_name: 'corp-internal-wiki-docs', vulnerability_type: 'NO_ENCRYPTION_AT_REST', severity: 'HIGH', title: 'S3 Bucket Default Encryption Disabled', description: "S3 bucket 'corp-internal-wiki-docs' is not configured with default server-side encryption (SSE). Unencrypted files pose structural compliance failures.", recommendation: 'Configure default bucket encryption with AES-256 (SSE-S3) or an AWS KMS key (SSE-KMS).', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.1', 'HIPAA 164.312'], cvss_score: 7.5, status: 'OPEN', evidence: {} },
  { id: 'v-3', resource_type: 'S3', resource_id: 'secureflow-production-assets', resource_name: 'secureflow-production-assets', vulnerability_type: 'SSL_NOT_ENFORCED', severity: 'MEDIUM', title: 'S3 Bucket Does Not Enforce SSL/TLS', description: "S3 bucket 'secureflow-production-assets' does not enforce encryption-in-transit, leaving endpoints vulnerable to interception.", recommendation: 'Deploy a bucket policy setting aws:SecureTransport parameter to false in a Deny rule block.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 2.1.2', 'PCI-DSS 4.1'], cvss_score: 5.3, status: 'OPEN', evidence: {} },
  { id: 'v-4', resource_type: 'VPC', resource_id: 'vpc-0a1b2c3d4e5f6a7b8', resource_name: 'prod-vpc', vulnerability_type: 'FLOW_LOGS_DISABLED', severity: 'HIGH', title: 'VPC Flow Logs Disabled', description: 'VPC prod-vpc has no flow logs enabled, so network traffic cannot be audited after an incident.', recommendation: 'Enable VPC flow logs to CloudWatch Logs for all production VPCs. Review the logs weekly.', terraform_fix: TF_S3, compliance_frameworks: ['CIS AWS 3.9'], cvss_score: 7.1, status: 'OPEN', evidence: {} },
  { id: 'v-5', resource_type: 'IAM', resource_id: 'AKIAIOSFODNN7EXAMPLE', resource_name: 'deploy-user', vulnerability_type: 'OLD_ACCESS_KEY', severity: 'MEDIUM', title: 'IAM Access Key Older Than 90 Days', description: 'Access key for deploy-user was created more than 90 days ago and has not been rotated.', recommendation: 'Rotate the access key and remove the old one. Then confirm the user can still deploy.', terraform_fix: '', compliance_frameworks: ['CIS AWS 1.4'], cvss_score: 5.0, status: 'OPEN', evidence: {} },
];
const SUMMARY = { total_open_vulnerabilities: 5, average_cvss_score: 6.94, severity_distribution: { CRITICAL: 1, HIGH: 2, MEDIUM: 2, LOW: 0 }, resource_distribution: { S3: 3, VPC: 1, IAM: 1 } };
// (9.8 + 7.5 + 5.3 + 7.1 + 5.0) / 5 = 6.94 — the mean of the five
// canned findings above, not a rounded guess.
// Latest scan is the demo one, so the summary is its control-level CIS
// score only: 1 of 8 controls pass. Other frameworks have no
// control-level rows and earn no score.
const COMPLIANCE = { CIS: 12.5 };
const ACCOUNTS = [
  { id: 'demo-account-id', name: 'Demo AWS Account', provider: 'aws', is_active: true },
  { id: 'prod-account-id', name: 'Production AWS Account', provider: 'aws', is_active: true },
];
const USERS = [
  { email: 'siva@example.com', full_name: 'Sivasai Boggu', role: 'admin', is_active: true },
  { email: 'teammate@example.com', full_name: 'Teammate One', role: 'user', is_active: true },
];

export function fixture(p, method) {
  if (method === 'POST' && p === '/auth/login') return { access_token: 'synthetic-shot-token', refresh_token: 'synthetic-shot-refresh', token_type: 'bearer', user: USERS[0] };
  if (method === 'POST' && p === '/scans') return { id: 'queued-scan', status: 'PENDING' };
  if (method === 'POST' && p === '/scans/cloud-accounts') return { id: 'new-account' };
  if (method === 'POST' && p === '/vulnerabilities/remediate') return { status: 'PLAN_SAVED' };
  if (p === '/scans') return SCANS;
  if (p === '/vulnerabilities') return VULNS;
  if (p === '/analytics/summary') return SUMMARY;
  if (p === '/compliance/summary') return COMPLIANCE;
  if (p === '/scans/cloud-accounts') return ACCOUNTS;
  if (p === '/users') return USERS;
  if (p === '/vulnerabilities/analyze-log') return { is_threat: true, confidence: null, classification: 'FLAGGED', method: 'heuristic_rules', calibrated: false };
  if (p === '/vulnerabilities/analyze-metrics') return { is_anomaly: null, anomaly_score: null, method: 'unavailable', calibrated: false, error: 'No local anomaly model is available. No assessment was performed.' };
  return null;
}
