import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IAMScanner:
    """GCP IAM scanner auditing project bindings and service accounts"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        self.organization_id = organization_id
        self.cloud_account_id = cloud_account_id
        self.credentials = credentials
        self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        if self.is_simulated:
            logger.info("Executing simulated GCP IAM scan...")
            return self._generate_simulated_findings()
        return []

    def _create_finding(self, name: str, res_id: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"gcp-iam-{name}-{vtype}".lower(),
            "resource_type": "GCP_SERVICE_ACCOUNT" if "sa" in vtype.lower() else "GCP_PROJECT_POLICY",
            "resource_id": res_id,
            "resource_name": name,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Go to GCP Console -> IAM & Admin -> Service Accounts.",
                "2. Choose the service account key and click delete.",
                "3. Recreate and download rotated keys."
            ],
            "terraform_fix": tf_fix,
            "compliance_frameworks": frameworks,
            "cvss_score": score,
            "cve_id": None,
            "discovered_at": datetime.utcnow().isoformat(),
            "evidence": evidence
        }

    def _generate_simulated_findings(self) -> List[Dict[str, Any]]:
        return [
            self._create_finding(
                "key-deployer-sa", "projects/palo-alto-sandbox/serviceAccounts/key-deployer-sa@gcp.iam.gserviceaccount.com",
                "GCP_SA_KEY_ROTATION_EXCEEDED", "MEDIUM", 6.0,
                "Service Account Key Exceeds 90 Days Rotation Cycle",
                "Service account user key 'key-deployer-sa' has been active for 180 days, exceeding safe credential cycles.",
                "Rotate service account keys and configure automatic key lifetimes.",
                ["CIS GCP 1.15"],
                '# Recreate key resource\nresource "google_service_account_key" "mykey" {{\n  service_account_id = google_service_account.my_sa.name\n}}',
                {"key_age_days": 180}
            )
        ]
