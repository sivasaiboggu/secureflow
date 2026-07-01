from typing import Dict, Any, List

# CIS AWS Foundations Benchmark v1.5 Control Catalog
CIS_AWS_CONTROLS = {
    "1.2": {
        "title": "Ensure multi-factor authentication (MFA) is enabled for all IAM users that have a password",
        "section": "Identity and Access Management",
        "severity": "HIGH",
        "description": "Multi-factor authentication (MFA) adds an extra layer of protection on top of username/password access.",
        "remediation": "Enable virtual or hardware MFA devices inside IAM console settings for matching accounts."
    },
    "1.8": {
        "title": "Ensure IAM password policy requires minimum length of 14 or greater",
        "section": "Identity and Access Management",
        "severity": "MEDIUM",
        "description": "Password policy constraints enforce minimum characters complex standards to prevent dictionary cracking.",
        "remediation": "Update account password policy with strict character validation controls."
    },
    "1.14": {
        "title": "Ensure access keys are rotated every 90 days or less",
        "section": "Identity and Access Management",
        "severity": "MEDIUM",
        "description": "Access credentials active beyond 90 days are prone to leaks and exposure.",
        "remediation": "Rotate access key profiles via IAM CLI or AWS security console."
    },
    "1.16": {
        "title": "Ensure IAM policies that allow full '*:*' administrative privileges are not created",
        "section": "Identity and Access Management",
        "severity": "CRITICAL",
        "description": "Universal wildcard authorizations break least privilege rules, introducing excessive breach risks.",
        "remediation": "Scope IAM action policies to specific, documented resources and API configurations."
    },
    "2.1.1": {
        "title": "Ensure all S3 buckets employ default server-side encryption",
        "section": "Storage",
        "severity": "HIGH",
        "description": "Default server-side encryption automatically encrypts all new objects placed inside bucket disks.",
        "remediation": "Apply sse-algorithm encryption configurations (SSE-S3 or SSE-KMS) inside bucket settings."
    },
    "2.1.2": {
        "title": "Ensure S3 Bucket Policy forces secure transfer (HTTPS)",
        "section": "Storage",
        "severity": "MEDIUM",
        "description": "Enforcing HTTPS prevents man-in-the-middle sniffing of object transfers.",
        "remediation": "Add an explicit Deny bucket policy statement mapping SecureTransport to false."
    },
    "2.1.5": {
        "title": "Ensure S3 buckets block public write/read permissions",
        "section": "Storage",
        "severity": "CRITICAL",
        "description": "Publicly accessible buckets expose company data assets to unauthorized leakage risks.",
        "remediation": "Enable Account or Bucket Block Public Access parameters."
    },
    "4.3": {
        "title": "Ensure VPC Flow Logs are enabled in all VPC networks",
        "section": "Logging & Monitoring",
        "severity": "MEDIUM",
        "description": "Flow Logs record network transactions mapping target IPs, which is crucial for alert diagnostics.",
        "remediation": "Create a flow log destination mapping the target VPC to a CloudWatch log group or S3 target."
    }
}

class CISBenchmarkEvaluator:
    """Validator mapping scanning rules to official CIS foundation benchmark controls"""
    
    def get_control_details(self, control_id: str) -> Dict[str, Any]:
        return CIS_AWS_CONTROLS.get(control_id, {
            "title": "Custom Posture Control Audit",
            "section": "Security Audits",
            "severity": "MEDIUM",
            "description": "Custom resource compliance posture check",
            "remediation": "Check configuration constraints and apply standard least privilege hardening."
        })
        
    def evaluate_compliance(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        failed_controls = []
        passed_controls = []
        
        # Simple validation mapper
        for cid, details in CIS_AWS_CONTROLS.items():
            failed = False
            violating_resources = []
            
            for f in findings:
                frameworks = f.get("compliance_frameworks", [])
                for fw in frameworks:
                    if cid in fw:
                        failed = True
                        violating_resources.append(f["resource_id"])
                        
            control_check = {
                "control_id": cid,
                "title": details["title"],
                "section": details["section"],
                "severity": details["severity"]
            }
            
            if failed:
                control_check["status"] = "FAIL"
                control_check["violating_resources"] = list(set(violating_resources))
                failed_controls.append(control_check)
            else:
                control_check["status"] = "PASS"
                passed_controls.append(control_check)
                
        total = len(CIS_AWS_CONTROLS)
        score = round((len(passed_controls) / total) * 100.0, 2) if total > 0 else 100.0
        
        return {
            "score": score,
            "failed_controls": failed_controls,
            "passed_controls": passed_controls
        }
cis_evaluator = CISBenchmarkEvaluator()
