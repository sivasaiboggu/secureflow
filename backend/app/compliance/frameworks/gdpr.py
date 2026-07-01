from typing import Dict, Any

GDPR_REQUIREMENTS = {
    "Art.32(1)(a)": {
        "title": "Pseudonymisation and Encryption",
        "description": "Implement encryption of personal data to protect sensitive privacy information at rest.",
        "severity": "CRITICAL"
    },
    "Art.32(1)(b)": {
        "title": "Confidentiality and Integrity of Systems",
        "description": "Ensure ongoing confidentiality, integrity, availability, and resilience of processing systems.",
        "severity": "HIGH"
    },
    "Art.32(1)(d)": {
        "title": "Evaluation of Security Effectiveness",
        "description": "Establish a process for regularly testing and evaluating the effectiveness of technical measures.",
        "severity": "MEDIUM"
    }
}

class GDPREvaluator:
    def get_requirement(self, cid: str) -> Dict[str, Any]:
        return GDPR_REQUIREMENTS.get(cid, {
            "title": "Custom GDPR Privacy Safeguard",
            "description": "Privacy data control check",
            "severity": "MEDIUM"
        })
gdpr_evaluator = GDPREvaluator()
