import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from botocore.exceptions import ClientError
from app.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

class RDSScanner(BaseScanner):
    """AWS RDS security posture scanner with boto3 and simulated fallback"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        super().__init__(organization_id, cloud_account_id, credentials)
        self.access_key = credentials.get("aws_access_key_id")
        self.secret_key = credentials.get("aws_secret_access_key")
        self.region = credentials.get("aws_default_region", "us-east-1")
        
        self.is_simulated = not (self.access_key and self.secret_key)
        self.findings: List[Dict[str, Any]] = []
        
        if not self.is_simulated:
            try:
                self.session = boto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self.rds_client = self.session.client('rds')
            except Exception as e:
                logger.warning(f"Failed to initialize RDS client: {e}. Simulating.")
                self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        if self.is_simulated:
            logger.info("Executing simulated AWS RDS scan...")
            self.findings = self._generate_simulated_findings()
            return self.findings
            
        try:
            instances = self.rds_client.describe_db_instances().get("DBInstances", [])
            for db_inst in instances:
                self.findings.extend(self._scan_db_instance(db_inst))
        except ClientError as e:
            logger.error(f"Error performing RDS scan: {e}")
            self.is_simulated = True
            self.findings = self._generate_simulated_findings()
            
        return self.findings

    def get_compliance_checks(self) -> List[Dict[str, Any]]:
        checks = []
        for finding in self.findings:
            frameworks = finding.get("compliance_frameworks", [])
            for fw in frameworks:
                parts = fw.split()
                fw_name = parts[0] if parts else "CIS"
                control_id = parts[-1] if len(parts) > 1 else "Unknown"
                checks.append({
                    "id": str(uuid.uuid4()),
                    "framework": fw_name,
                    "control_id": control_id,
                    "title": finding["title"],
                    "status": "FAIL",
                    "resource_id": finding["resource_id"],
                    "evidence": {
                        "vulnerability_type": finding["vulnerability_type"],
                        "severity": finding["severity"]
                    }
                })
        return checks

    def _scan_db_instance(self, db: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        db_id = db.get("DBInstanceIdentifier", "unknown-db")
        arn = db.get("DBInstanceArn", f"arn:aws:rds:{self.region}:account:db:{db_id}")
        
        # Check 1: Storage Encryption
        if not db.get("StorageEncrypted", False):
            findings.append(self._create_finding(
                db_id, arn, "RDS_UNENCRYPTED", "HIGH", 7.8,
                "RDS Database Instance Storage Encryption Disabled",
                f"RDS Instance '{db_id}' does not have storage encryption enabled. Data stored at rest is vulnerable to offline leaks.",
                "Recreate the DB instance from an encrypted snapshot or enable storage encryption during database creation.",
                ["CIS AWS 2.3.1", "PCI-DSS 3.4"],
                f'resource "aws_db_instance" "{db_id.replace("-", "_")}" {{\n  # ... other config ...\n  storage_encrypted = true\n}}',
                {"storage_encrypted": False}
            ))
            
        # Check 2: Public accessibility
        if db.get("PubliclyAccessible", False):
            findings.append(self._create_finding(
                db_id, arn, "RDS_PUBLICLY_ACCESSIBLE", "CRITICAL", 9.3,
                "RDS Database Instance Publicly Accessible",
                f"RDS Instance '{db_id}' has public accessibility enabled. This permits connection requests from any IP address globally.",
                "Modify the database instance parameters to set PubliclyAccessible to false and route via private VPC subnets.",
                ["CIS AWS 4.3", "NIST SP 800-53 SC-7"],
                f'resource "aws_db_instance" "{db_id.replace("-", "_")}" {{\n  # ... other config ...\n  publicly_accessible = false\n}}',
                {"publicly_accessible": True}
            ))
            
        # Check 3: Backup retention period
        backup_retention = db.get("BackupRetentionPeriod", 0)
        if backup_retention < 7:
            findings.append(self._create_finding(
                db_id, arn, "RDS_INSUFFICIENT_BACKUP_RETENTION", "MEDIUM", 5.0,
                "RDS Database Backup Retention Period Less Than 7 Days",
                f"RDS Instance '{db_id}' has a backup retention period of {backup_retention} days. Disasters or ransom events may exceed recovery scopes.",
                "Configure backup retention period to at least 7 days.",
                ["CIS AWS 2.3.2"],
                f'resource "aws_db_instance" "{db_id.replace("-", "_")}" {{\n  # ... other config ...\n  backup_retention_period = 7\n}}',
                {"backup_retention_period": backup_retention}
            ))
            
        return findings

    def _create_finding(self, db_id: str, arn: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"rds-{db_id}-{vtype}".lower(),
            "resource_type": "RDS_DB_INSTANCE",
            "resource_id": arn,
            "resource_name": db_id,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Go to RDS dashboard inside AWS console.",
                "2. Click Databases and select the instance.",
                "3. Click Modify and change the encryption / public settings.",
                "4. Select Apply Immediately and save changes."
            ],
            "terraform_fix": tf_fix,
            "compliance_frameworks": frameworks,
            "cvss_score": score,
            "cve_id": None,
            "discovered_at": datetime.utcnow().isoformat(),
            "evidence": evidence
        }

    def _generate_simulated_findings(self) -> List[Dict[str, Any]]:
        simulated = []
        
        # Instance 1: Public RDS
        simulated.append(self._create_finding(
            "postgres-production-cluster",
            "arn:aws:rds:us-east-1:123456789:db:postgres-production-cluster",
            "RDS_PUBLICLY_ACCESSIBLE", "CRITICAL", 9.3,
            "RDS Database Instance Publicly Accessible",
            "RDS Instance 'postgres-production-cluster' is configured with public routing enabled, allowing network entry from all public subnets.",
            "Disable public accessibility in RDS configuration settings.",
            ["CIS AWS 4.3", "PCI-DSS 1.2"],
            'resource "aws_db_instance" "prod_db" {\n  # ... config ...\n  publicly_accessible = false\n}',
            {"publicly_accessible": True}
        ))
        
        # Instance 2: Backup retention
        simulated.append(self._create_finding(
            "customer-billing-db",
            "arn:aws:rds:us-east-1:123456789:db:customer-billing-db",
            "RDS_INSUFFICIENT_BACKUP_RETENTION", "MEDIUM", 5.0,
            "RDS Database Backup Retention Period Less Than 7 Days",
            "RDS Instance 'customer-billing-db' has a backup retention window of only 2 days, violating business continuity targets.",
            "Set the backup retention parameter to a minimum of 7 days.",
            ["CIS AWS 2.3.2"],
            'resource "aws_db_instance" "billing_db" {\n  # ... config ...\n  backup_retention_period = 7\n}',
            {"backup_retention_period": 2}
        ))
        
        return simulated
