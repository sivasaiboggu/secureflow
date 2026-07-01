import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from botocore.exceptions import ClientError
from app.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

class CloudTrailScanner(BaseScanner):
    """AWS CloudTrail security posture scanner verifying logging policies"""
    
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
                self.ct_client = self.session.client('cloudtrail')
            except Exception as e:
                logger.warning(f"Failed to initialize CloudTrail client: {e}. Simulating.")
                self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        if self.is_simulated:
            logger.info("Executing simulated AWS CloudTrail scan...")
            self.findings = self._generate_simulated_findings()
            return self.findings
            
        try:
            trails = self.ct_client.describe_trails().get("trailList", [])
            if not trails:
                # No trails configured at all
                self.findings.append(self._create_finding(
                    "no-trail", "GLOBAL", "CLOUDTRAIL_DISABLED", "CRITICAL", 9.5,
                    "No AWS CloudTrail Logging Configured",
                    "There are no CloudTrail paths active in the account. Global API and administrative executions are not logged.",
                    "Deploy at least one CloudTrail logging path covering all regions.",
                    ["CIS AWS 3.1", "NIST SP 800-53 AU-2"],
                    'resource "aws_cloudtrail" "global" {\n  name                          = "global-audit-trail"\n  s3_bucket_name                = "audit-logs-storage"\n  include_global_service_events = true\n  is_multi_region_trail         = true\n}',
                    {"trails_found": 0}
                ))
            else:
                for trail in trails:
                    self.findings.extend(self._scan_trail(trail))
        except ClientError as e:
            logger.error(f"Error performing CloudTrail scan: {e}")
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

    def _scan_trail(self, trail: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        name = trail.get("Name", "unknown-trail")
        arn = trail.get("TrailARN", f"arn:aws:cloudtrail:{self.region}:account:trail/{name}")
        
        # Check 1: Multi-region configuration
        if not trail.get("IsMultiRegionTrail", False):
            findings.append(self._create_finding(
                name, arn, "CLOUDTRAIL_NOT_MULTI_REGION", "MEDIUM", 5.0,
                "CloudTrail Lacks Multi-Region Configuration",
                f"CloudTrail trail '{name}' records activities in the local region only. Hostile actions in other regions are unmonitored.",
                "Modify the CloudTrail logging path properties, enabling Multi-Region options.",
                ["CIS AWS 3.1"],
                f'resource "aws_cloudtrail" "{name.replace("-", "_")}" {{\n  # ... other config ...\n  is_multi_region_trail = true\n}}',
                {"is_multi_region": False}
            ))
            
        # Check 2: Log File Validation
        if not trail.get("LogFileValidationEnabled", False):
            findings.append(self._create_finding(
                name, arn, "CLOUDTRAIL_LOG_VALIDATION_DISABLED", "HIGH", 7.2,
                "CloudTrail Log File Validation Disabled",
                f"CloudTrail '{name}' has log file validation disabled. Attackers can alter or delete logged actions without flagging trace failures.",
                "Enable log file validation to ensure cryptographic integrity audits.",
                ["CIS AWS 3.2", "NIST SP 800-53 AU-9"],
                f'resource "aws_cloudtrail" "{name.replace("-", "_")}" {{\n  # ... other config ...\n  enable_log_file_validation = true\n}}',
                {"log_file_validation": False}
            ))
            
        return findings

    def _create_finding(self, name: str, arn: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"cloudtrail-{name}-{vtype}".lower(),
            "resource_type": "CLOUDTRAIL_TRAIL",
            "resource_id": arn,
            "resource_name": name,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Open CloudTrail service inside AWS console.",
                "2. Click Trails and select the specific configuration.",
                "3. Edit settings and select Enable Log File Validation and Multi-Region settings.",
                "4. Click Save Changes."
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
        
        # Instance 1: Validation disabled
        simulated.append(self._create_finding(
            "corporate-audit-trail",
            "arn:aws:cloudtrail:us-east-1:123456789:trail/corporate-audit-trail",
            "CLOUDTRAIL_LOG_VALIDATION_DISABLED", "HIGH", 7.2,
            "CloudTrail Log File Validation Disabled",
            "Audit log trail 'corporate-audit-trail' does not validate log files, leaving trace configurations vulnerable to covert log tampers.",
            "Set enable_log_file_validation configuration parameter to true.",
            ["CIS AWS 3.2", "NIST SP 800-53 AU-9"],
            'resource "aws_cloudtrail" "corporate_trail" {\n  # ... config ...\n  enable_log_file_validation = true\n}',
            {"log_file_validation": False}
        ))
        
        return simulated
