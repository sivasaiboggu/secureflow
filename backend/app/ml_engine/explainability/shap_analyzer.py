import numpy as np
from typing import Dict, List

class SHAPAnalyzer:
    """Estimates and graphs SHAP value approximations explaining predictions"""
    
    def explain_severity(self, cat_features: List[str], num_features: List[float]) -> Dict[str, float]:
        # Mimicking relative feature importances
        importances = {
            "vulnerability_type": 0.45,
            "cvss_base_score": 0.35,
            "resource_type": 0.12,
            "cloud_provider": 0.08
        }
        return importances

shap_analyzer = SHAPAnalyzer()
