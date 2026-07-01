import uuid
from typing import List, Dict, Any
from datetime import datetime

class ComplianceEngine:
    """Calculates overall framework scores and evaluates audit rules alignment"""
    
    def __init__(self):
        self.frameworks = ["CIS", "NIST", "PCI_DSS", "HIPAA", "GDPR"]

    def evaluate_findings(self, scan_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maps vulnerabilities to compliance checks, marking failures where resources violate guidelines"""
        compliance_checks = []
        
        for finding in findings:
            frameworks = finding.get("compliance_frameworks", [])
            for fw in frameworks:
                # E.g. "CIS AWS 1.2"
                parts = fw.split()
                fw_name = parts[0] if parts else "CIS"
                control_id = parts[-1] if len(parts) > 1 else "Unknown"
                
                compliance_checks.append({
                    "id": str(uuid.uuid4()),
                    "scan_id": scan_id,
                    "framework": fw_name.upper(),
                    "control_id": control_id,
                    "title": finding["title"],
                    "status": "FAIL",
                    "resource_id": finding["resource_id"],
                    "evidence": {
                        "vulnerability_type": finding["vulnerability_type"],
                        "severity": finding["severity"],
                        "description": finding["description"],
                        "recommendation": finding["recommendation"]
                    },
                    "checked_at": datetime.utcnow().isoformat()
                })
                
        return compliance_checks

    def calculate_scores(self, checks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Returns compliance percentages per framework category"""
        scores = {fw: 100.0 for fw in self.frameworks}
        counts = {fw: {"pass": 0, "fail": 0} for fw in self.frameworks}
        
        for check in checks:
            fw = check["framework"].upper()
            if fw in counts:
                if check["status"] == "PASS":
                    counts[fw]["pass"] += 1
                else:
                    counts[fw]["fail"] += 1
                    
        for fw in self.frameworks:
            total = counts[fw]["pass"] + counts[fw]["fail"]
            if total > 0:
                scores[fw] = round((counts[fw]["pass"] / total) * 100.0, 2)
            else:
                # Default baseline score for unviolated structures
                scores[fw] = 100.0
                
        return scores

compliance_engine = ComplianceEngine()
