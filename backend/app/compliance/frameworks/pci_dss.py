from typing import Dict, Any

PCI_DSS_CONTROLS = {
    "1.2": {
        "title": "Network connections restrict unauthorized routing",
        "description": "Ensure public routing paths block access to database networks and private resources.",
        "severity": "CRITICAL"
    },
    "2.2": {
        "title": "Default system configurations hardened",
        "description": "Avoid default VPC networks or generic admin policy settings.",
        "severity": "HIGH"
    },
    "3.4": {
        "title": "Sensitive cardholder data encrypted at rest",
        "description": "Force storage encryption configurations on S3, EBS, and database partitions.",
        "severity": "CRITICAL"
    },
    "8.3": {
        "title": "Multi-factor authentication (MFA) enabled",
        "description": "Enforce MFA for all administrative systems access.",
        "severity": "HIGH"
    },
    "10.2": {
        "title": "Audit log traces active",
        "description": "Log all access credentials activity using global trace tools (CloudTrail).",
        "severity": "MEDIUM"
    }
}

class PCIDSS5Evaluator:
    def get_control(self, cid: str) -> Dict[str, Any]:
        return PCI_DSS_CONTROLS.get(cid, {
            "title": "Custom PCI Security Audit Requirement",
            "description": "Cardholder data environment protection check",
            "severity": "MEDIUM"
        })
pci_evaluator = PCIDSS5Evaluator()
