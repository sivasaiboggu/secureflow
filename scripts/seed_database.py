import sys
import os
import uuid
import datetime

# Add backend directory to load application libraries
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.config.database import SessionLocal, Base, engine
from app.database.models import User, Organization, CloudAccount, Scan, Vulnerability, ComplianceCheck
from app.core.security import get_password_hash

def seed_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Clear existing seed records
        db.query(Vulnerability).delete()
        db.query(ComplianceCheck).delete()
        db.query(Scan).delete()
        db.query(CloudAccount).delete()
        db.query(User).delete()
        db.query(Organization).delete()
        db.commit()
        print("Cleared stale records.")

        # 2. Add Organization
        org_id = str(uuid.uuid4())
        org = Organization(id=org_id, name="Nexus Sandbox Org")
        db.add(org)
        print("Created organization.")

        # 3. Add Admin User
        user_id = str(uuid.uuid4())
        admin = User(
            id=user_id,
            email="admin@secureflow.io",
            hashed_password=get_password_hash("password123"),
            full_name="Post Posture Auditor",
            role="admin",
            organization_id=org_id,
            is_active=True
        )
        db.add(admin)
        print("Created administrator account: admin@secureflow.io")

        # 4. Add Cloud Account (empty credentials = triggers simulator mode)
        acc_id = str(uuid.uuid4())
        cloud_acc = CloudAccount(
            id=acc_id,
            name="AWS Production Workspace",
            provider="aws",
            organization_id=org_id,
            credentials={"aws_access_key_id": "", "aws_secret_access_key": ""},
            is_active=True,
            last_scanned_at=datetime.datetime.utcnow()
        )
        db.add(cloud_acc)
        print("Created AWS connection profile.")

        # 5. Add historical Scan Record
        scan_id = str(uuid.uuid4())
        history_scan = Scan(
            id=scan_id,
            organization_id=org_id,
            cloud_account_id=acc_id,
            status="COMPLETED",
            progress=100.0,
            vulnerabilities_found=3,
            failed_checks=3,
            passed_checks=12,
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            completed_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1.8)
        )
        db.add(history_scan)
        
        # 6. Add associated vulnerabilities for seeding charts
        vulns = [
            Vulnerability(
                id=f"seed-s3-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="S3_BUCKET",
                resource_id="arn:aws:s3:::customer-invoice-uploads-temp",
                resource_name="customer-invoice-uploads-temp",
                vulnerability_type="PUBLIC_ACCESS_NOT_BLOCKED",
                severity="CRITICAL",
                title="S3 Bucket Public Access Not Fully Blocked",
                description="S3 bucket is configured with public write/read permissions, allowing global directory exposure.",
                recommendation="Enable all S3 Block Public Access policies immediately at the account or bucket level.",
                remediation_steps=["1. Go to S3 tab", "2. Click Permissions", "3. Enable Block Public Access"],
                terraform_fix="resource \"aws_s3_bucket_public_access_block\" \"invoice_block\" {\n  bucket = \"customer-invoice-uploads-temp\"\n  block_public_acls = true\n  block_public_policy = true\n}",
                compliance_frameworks=["CIS AWS 2.1.5", "NIST 800-53"],
                cvss_score=9.8,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-ec2-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="EC2_INSTANCE",
                resource_id="arn:aws:ec2:us-east-1:i-07cb1294819d9b62a",
                resource_name="web-application-frontend-prod",
                vulnerability_type="IMDSV1_ENABLED",
                severity="HIGH",
                title="Instance Metadata Service v1 (IMDSv1) Enabled",
                description="EC2 instance does not require session IMDSv2 tokens, leaving it vulnerable to metadata credential extraction.",
                recommendation="Enforce IMDSv2 only.",
                remediation_steps=["1. Open EC2 settings", "2. Select Modify IMDS", "3. Enable token required"],
                terraform_fix="resource \"aws_instance\" \"app\" {\n  metadata_options {\n    http_tokens = \"required\"\n  }\n}",
                compliance_frameworks=["CIS AWS 1.16"],
                cvss_score=7.5,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-iam-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="IAM_USER",
                resource_id="arn:aws:iam::account:admin-user-jenkins",
                resource_name="admin-user-jenkins",
                vulnerability_type="IAM_USER_MFA_DISABLED",
                severity="MEDIUM",
                title="MFA Disabled for Admin IAM User 'admin-user-jenkins'",
                description="IAM user has administrative credentials but has not registered a multi-factor authentication hardware/virtual device.",
                recommendation="Enforce MFA registration.",
                remediation_steps=["1. Go to IAM console", "2. Select Jenkins user", "3. Enable MFA virtual device"],
                terraform_fix="# MFA requires active console setup",
                compliance_frameworks=["CIS AWS 1.2"],
                cvss_score=6.2,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-rds-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="RDS_DB_INSTANCE",
                resource_id="arn:aws:rds:us-east-1:123456789:db:postgres-production-cluster",
                resource_name="postgres-production-cluster",
                vulnerability_type="RDS_PUBLICLY_ACCESSIBLE",
                severity="CRITICAL",
                title="RDS Database Instance Publicly Accessible",
                description="RDS Instance is configured with public routing enabled, allowing network entry from all public subnets.",
                recommendation="Disable public accessibility in RDS configuration settings.",
                remediation_steps=["1. Go to RDS dashboard", "2. Modify instance", "3. Set publicly accessible to false"],
                terraform_fix="resource \"aws_db_instance\" \"prod_db\" {\n  publicly_accessible = false\n}",
                compliance_frameworks=["CIS AWS 4.3", "PCI-DSS 1.2"],
                cvss_score=9.3,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-lambda-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="LAMBDA_FUNCTION",
                resource_id="arn:aws:lambda:us-east-1:123456789:function:legacy-payment-reconciliation-job",
                resource_name="legacy-payment-reconciliation-job",
                vulnerability_type="LAMBDA_DEPRECATED_RUNTIME",
                severity="MEDIUM",
                title="Lambda Function Using Deprecated Runtime Environment",
                description="Lambda function runs on deprecated environment runtime 'python3.7' which has reached end of life support.",
                recommendation="Upgrade to python3.11 runtime environment version.",
                remediation_steps=["1. Open Lambda console", "2. Under runtime settings, select python3.11", "3. Save"],
                terraform_fix="resource \"aws_lambda_function\" \"payment_job\" {\n  runtime = \"python3.11\"\n}",
                compliance_frameworks=["CIS AWS 2.9.1"],
                cvss_score=6.1,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-vpc-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="VPC",
                resource_id="arn:aws:ec2:us-east-1:123456789:vpc/vpc-0a88091176bfa2e82",
                resource_name="vpc-0a88091176bfa2e82",
                vulnerability_type="VPC_FLOW_LOGS_DISABLED",
                severity="MEDIUM",
                title="VPC Flow Logs Disabled",
                description="VPC lacks active Flow Logs. Without flow log traces, incident forensic analysis cannot record ingress/egress patterns.",
                recommendation="Configure VPC flow logging with traffic options set to 'ALL'.",
                remediation_steps=["1. Go to VPC dashboard", "2. Click Create Flow Log", "3. Save"],
                terraform_fix="resource \"aws_flow_log\" \"main_vpc_log\" {\n  traffic_type = \"ALL\"\n  vpc_id       = \"vpc-0a88091176bfa2e82\"\n}",
                compliance_frameworks=["CIS AWS 4.3", "NIST SP 800-53"],
                cvss_score=5.2,
                status="OPEN"
            ),
            Vulnerability(
                id=f"seed-cloudtrail-{str(uuid.uuid4())[:8]}",
                scan_id=scan_id,
                resource_type="CLOUDTRAIL_TRAIL",
                resource_id="arn:aws:cloudtrail:us-east-1:123456789:trail/corporate-audit-trail",
                resource_name="corporate-audit-trail",
                vulnerability_type="CLOUDTRAIL_LOG_VALIDATION_DISABLED",
                severity="HIGH",
                title="CloudTrail Log File Validation Disabled",
                description="Audit log trail does not validate log files, leaving trace configurations vulnerable to covert log tampers.",
                recommendation="Set enable_log_file_validation configuration parameter to true.",
                remediation_steps=["1. Open CloudTrail settings", "2. Enable log validation option", "3. Click save"],
                terraform_fix="resource \"aws_cloudtrail\" \"corporate_trail\" {\n  enable_log_file_validation = true\n}",
                compliance_frameworks=["CIS AWS 3.2", "NIST SP 800-53"],
                cvss_score=7.2,
                status="OPEN"
            )
        ]
        
        for v in vulns:
            db.add(v)
            
        # 7. Add compliance check status values
        checks = [
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="2.1.5",
                title="S3 Bucket Public Access Blocked", status="FAIL", resource_id="arn:aws:s3:::customer-invoice-uploads-temp"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="1.16",
                title="IMDSv2 Enforced", status="FAIL", resource_id="arn:aws:ec2:us-east-1:i-07cb1294819d9b62a"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="1.2",
                title="MFA for admin users", status="FAIL", resource_id="arn:aws:iam::account:admin-user-jenkins"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="4.3",
                title="RDS Public Access Disabled", status="FAIL", resource_id="arn:aws:rds:us-east-1:123456789:db:postgres-production-cluster"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="2.9.1",
                title="Lambda Supported Runtime Active", status="FAIL", resource_id="arn:aws:lambda:us-east-1:123456789:function:legacy-payment-reconciliation-job"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="4.3",
                title="VPC Flow Logs Enabled", status="FAIL", resource_id="arn:aws:ec2:us-east-1:123456789:vpc/vpc-0a88091176bfa2e82"
            ),
            ComplianceCheck(
                id=str(uuid.uuid4()), scan_id=scan_id, framework="CIS", control_id="3.2",
                title="CloudTrail Log File Validation Enabled", status="FAIL", resource_id="arn:aws:cloudtrail:us-east-1:123456789:trail/corporate-audit-trail"
            )
        ]
        for c in checks:
            db.add(c)
            
        db.commit()
        print("Database seeded with baseline items successfully.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
