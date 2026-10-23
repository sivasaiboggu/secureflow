from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ScanUnavailable(RuntimeError):
    """A real scan could not verify its scope. No synthetic results are substituted."""


class BaseScanner(ABC):
    """Abstract base class for cloud posture scanners"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        self.organization_id = organization_id
        self.cloud_account_id = cloud_account_id
        self.credentials = credentials
        
    def configure_aws_client(self, service: str):
        """Demo is explicit; credential or provider failures never select it."""
        import boto3
        self.region = self.credentials.get("aws_default_region", "us-east-1")
        self.is_simulated = self.credentials.get("scan_mode") == "demo"
        self.findings = []
        if self.is_simulated:
            return None
        if not (self.credentials.get("aws_access_key_id") and self.credentials.get("aws_secret_access_key")):
            raise ScanUnavailable("AWS credentials are required for a real scan. Select demo explicitly for sample data.")
        try:
            self.session = boto3.Session(
                aws_access_key_id=self.credentials["aws_access_key_id"],
                aws_secret_access_key=self.credentials["aws_secret_access_key"],
                aws_session_token=self.credentials.get("aws_session_token"),
                region_name=self.credentials.get("aws_default_region", "us-east-1"),
            )
            return self.session.client(service)
        except Exception:
            raise ScanUnavailable("AWS client could not be initialized. No scan results were produced.") from None

    def demo_findings(self):
        findings = self._generate_simulated_findings()
        for finding in findings:
            finding["title"] = "[DEMO] " + finding["title"]
            finding["evidence"] = {**finding.get("evidence", {}), "scan_mode": "demo", "synthetic": True}
        return findings

    @abstractmethod
    def scan(self) -> List[Dict[str, Any]]:
        """Run scanning operation and return list of findings/vulnerabilities"""
        pass
        
    @abstractmethod
    def get_compliance_checks(self) -> List[Dict[str, Any]]:
        """Map scanning findings to structured compliance checks (CIS, NIST, etc.)"""
        pass
