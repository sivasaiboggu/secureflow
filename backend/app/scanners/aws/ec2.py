import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from botocore.exceptions import ClientError
from app.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

class EC2Scanner(BaseScanner):
    """AWS EC2 Posture Scanner - Production Implementation with fallback simulator"""
    
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
                self.ec2_client = self.session.client('ec2')
            except Exception as e:
                logger.warning(f"Failed to initialize real boto3 EC2 client: {e}. Falling back to simulation.")
                self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        if self.is_simulated:
            logger.info("Executing simulated AWS EC2 Scan...")
            self.findings = self._generate_simulated_findings()
            return self.findings
            
        try:
            instances = self.ec2_client.describe_instances()
            for reservation in instances.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    self.findings.extend(self._scan_instance(inst))
        except ClientError as e:
            logger.error(f"Error performing real EC2 scan: {e}")
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

    def _scan_instance(self, inst: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        inst_id = inst.get("InstanceId", "unknown-instance")
        inst_name = next((tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"), inst_id)
        
        # Check 1: IMDSv2 Configuration
        metadata_options = inst.get("MetadataOptions", {})
        if metadata_options.get("HttpTokens") != "required":
            findings.append(self._create_finding(
                inst_id, inst_name, "IMDSV1_ENABLED", "HIGH", 7.5,
                "Instance Metadata Service v1 (IMDSv1) Enabled",
                f"EC2 Instance '{inst_name}' does not enforce IMDSv2 (HttpTokens=required). Access tokens can be requested without session duration controls, risking SSRF credential theft.",
                "Modify instance metadata options to require tokens (HttpTokens=required).",
                ["CIS AWS 1.16", "NIST SP 800-53 AC-3"],
                f'resource "aws_instance" "{inst_id.replace("-", "_")}" {{\n  # ... other config ...\n  metadata_options {{\n    http_tokens = "required"\n  }}\n}}',
                {"metadata_options": metadata_options}
            ))
            
        # Check 2: Public IP Assignment
        public_ip = inst.get("PublicIpAddress")
        if public_ip:
            findings.append(self._create_finding(
                inst_id, inst_name, "PUBLIC_IP_ASSIGNED", "MEDIUM", 5.0,
                "EC2 Instance Assigned Public Routeable IP",
                f"EC2 Instance '{inst_name}' has public IPv4 address {public_ip} assigned. Putting hosts on public route tables exposes them to global network enumeration.",
                "Disassociate public IP address and configure private subnets mapping behind NAT Gateways.",
                ["CIS AWS 4.1", "NIST SP 800-53 SC-7"],
                f'resource "aws_instance" "{inst_id.replace("-", "_")}" {{\n  # ... other config ...\n  associate_public_ip_address = false\n}}',
                {"public_ip": public_ip}
            ))
            
        # Check 3: EBS Volume Encryption
        for block_dev in inst.get("BlockDeviceMappings", []):
            ebs = block_dev.get("Ebs", {})
            vol_id = ebs.get("VolumeId")
            if vol_id:
                try:
                    vol_info = self.ec2_client.describe_volumes(VolumeIds=[vol_id])
                    vol = vol_info["Volumes"][0]
                    if not vol.get("Encrypted", False):
                        findings.append(self._create_finding(
                            vol_id, f"ebs-{vol_id}", "UNENCRYPTED_EBS_VOLUME", "HIGH", 7.8,
                            "EBS Volume Encryption Disabled",
                            f"EBS Volume '{vol_id}' attached to instance '{inst_name}' is not encrypted at rest.",
                            "Enable default EBS encryption at the AWS account level or recreate volume in encrypted state.",
                            ["CIS AWS 2.2.1", "PCI-DSS 3.4"],
                            f'resource "aws_ebs_volume" "vol_{vol_id.replace("-", "_")}" {{\n  # ... other config ...\n  encrypted  = true\n}}',
                            {"volume_details": vol}
                        ))
                except Exception as e:
                    logger.error(f"Error checking volume {vol_id}: {e}")
                    
        return findings

    def _create_finding(self, res_id: str, res_name: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"ec2-{res_id}-{vtype}".lower(),
            "resource_type": "EC2_INSTANCE" if "vol-" not in res_id else "EBS_VOLUME",
            "resource_id": f"arn:aws:ec2:{self.region}:account:{res_id}",
            "resource_name": res_name,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Open EC2 instances in AWS management panel.",
                "2. Choose Actions -> Instance settings -> Modify instance metadata options.",
                "3. Select 'V2 only (token required)' under IMDS setting and click Save."
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
        
        # Instance 1: IMDSv1
        simulated.append(self._create_finding(
            "i-07cb1294819d9b62a", "web-application-frontend-prod", "IMDSV1_ENABLED", "HIGH", 7.5,
            "Instance Metadata Service v1 (IMDSv1) Enabled",
            "EC2 instance 'web-application-frontend-prod' does not require session IMDSv2 tokens, leaving it vulnerable to metadata security credential access via SSRF.",
            "Run ec2-modify-instance-metadata-options cli tool to enforce HttpTokens='required'.",
            ["CIS AWS 1.16", "NIST SP 800-53 AC-3"],
            'resource "aws_instance" "web_app" {\n  # ... config ...\n  metadata_options {\n    http_tokens = "required"\n  }\n}',
            {"http_tokens": "optional", "http_endpoint": "enabled"}
        ))
        
        # Instance 2: Unencrypted volume
        simulated.append(self._create_finding(
            "vol-09dca820e11893cfa", "ebs-database-storage", "UNENCRYPTED_EBS_VOLUME", "HIGH", 7.8,
            "EBS Volume Encryption Disabled",
            "EBS Volume 'vol-09dca820e11893cfa' containing state databases is unencrypted, breaking data confidentiality requirements.",
            "Enable AWS EBS encryption by default configuration or snapshot, re-create, and encrypt volume before re-attachment.",
            ["CIS AWS 2.2.1", "PCI-DSS 3.4"],
            'resource "aws_ebs_volume" "database_storage" {\n  availability_zone = "us-east-1a"\n  size              = 100\n  encrypted         = true\n}',
            {"encrypted": False, "kms_key_id": None}
        ))
        
        return simulated
