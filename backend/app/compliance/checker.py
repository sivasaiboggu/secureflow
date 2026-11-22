from typing import List, Dict, Any

class ComplianceEngine:
    """Calculates overall framework scores and evaluates audit rules alignment"""

    def __init__(self):
        self.frameworks = ["CIS", "NIST", "PCI_DSS", "HIPAA", "GDPR"]

    def calculate_scores(self, checks: List[Dict[str, Any]]) -> Dict[str, float]:
        """Returns compliance percentages only for frameworks with evaluated checks"""
        counts = {fw: {"pass": 0, "fail": 0} for fw in self.frameworks}
        
        for check in checks:
            fw = check["framework"].upper()
            if fw in counts:
                if check["status"] == "PASS":
                    counts[fw]["pass"] += 1
                else:
                    counts[fw]["fail"] += 1
                    
        # Only frameworks with at least one evaluated check earn a score.
        # An unchecked framework reports nothing, never a default 100.
        return {
            fw: round((counts[fw]["pass"] / (counts[fw]["pass"] + counts[fw]["fail"])) * 100.0, 2)
            for fw in self.frameworks
            if counts[fw]["pass"] + counts[fw]["fail"] > 0
        }

compliance_engine = ComplianceEngine()
