import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class IAMScanner:
    """Azure Active Directory (AD) and IAM Role assignments posture scanner"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        self.organization_id = organization_id
        self.cloud_account_id = cloud_account_id
        self.credentials = credentials
        self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        if self.is_simulated:
            logger.info("Executing simulated Azure IAM scan...")
            return self._generate_simulated_findings()
        return []

    def _create_finding(self, name: str, res_id: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"azure-iam-{name}-{vtype}".lower(),
            "resource_type": "AZURE_USER",
            "resource_id": res_id,
            "resource_name": name,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Go to Azure Portal -> Microsoft Entra ID (Active Directory).",
                "2. Click Users and find the user.",
                "3. In authentication methods tab, assign virtual MFA device."
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
                "partner-billing-auditor", "/subscriptions/123-abc/providers/Microsoft.Authorization/roleAssignments/auditor-role-id",
                "AZURE_USER_MFA_DISABLED", "HIGH", 8.0,
                "Azure Subscription Owner Account Lack MFA Enrolment",
                "Azure user 'partner-billing-auditor' holding administrative owner bindings lacks active MFA credentials validation.",
                "Enforce multi-factor authentication (MFA) using Microsoft Entra conditional access rules.",
                ["CIS Azure 1.1"],
                '# MFA configurations are enforced inside Entra Conditional Access Policies',
                {"mfa_active": False}
            )
        ]
