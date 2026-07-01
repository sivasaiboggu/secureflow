from typing import Dict, Any

NIST_800_53_CONTROLS = {
    "AC-2": {
        "title": "Account Management",
        "description": "Establish and manage credentials, privileges, and MFA controls for administrative and standard users.",
        "severity": "HIGH"
    },
    "AC-3": {
        "title": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access to information system resources (e.g., S3 public blocks).",
        "severity": "CRITICAL"
    },
    "AU-2": {
        "title": "Event Logging",
        "description": "Generate audit logs containing activity timestamps and identities (e.g., Flow logs and CloudTrail).",
        "severity": "MEDIUM"
    },
    "SC-7": {
        "title": "Boundary Protection",
        "description": "Restrict routing access at public network gateways and block wildcard database accesses.",
        "severity": "HIGH"
    },
    "IA-2": {
        "title": "Identification and Authentication (Organizational Users)",
        "description": "Enforce multi-factor authentication (MFA) to identify administrative accounts.",
        "severity": "HIGH"
    }
}

class NIST80053Evaluator:
    def get_control(self, cid: str) -> Dict[str, Any]:
        return NIST_800_53_CONTROLS.get(cid, {
            "title": "Custom NIST Security Control",
            "description": "Corporate audit verification requirement",
            "severity": "MEDIUM"
        })
nist_evaluator = NIST80053Evaluator()
