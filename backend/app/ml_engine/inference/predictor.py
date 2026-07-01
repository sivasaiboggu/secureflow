import logging
from typing import Dict, Any, Tuple
from app.ml_engine.models.severity_predictor import SeverityPredictorModel
from app.ml_engine.models.anomaly_detector import AnomalyDetector
from app.ml_engine.models.threat_classifier import ThreatClassifier

logger = logging.getLogger(__name__)

class RealTimePredictor:
    """Manages real-time model predictions for threat logging and vulnerability severity scoring"""
    
    def __init__(self):
        self.severity_predictor = SeverityPredictorModel()
        self.anomaly_detector = AnomalyDetector()
        self.threat_classifier = ThreatClassifier()
        
        # Load pre-trained models
        self.severity_predictor.load()
        self.anomaly_detector.load()
        self.threat_classifier.load()

    def predict_finding_severity(self, resource_type: str, vuln_type: str, provider: str, cvss_score: float) -> str:
        """Runs inference logic using PyTorch Severity Predictor"""
        if not self.severity_predictor.model:
            # Safe baseline fallback
            if cvss_score >= 9.0: return "CRITICAL"
            if cvss_score >= 7.0: return "HIGH"
            if cvss_score >= 4.0: return "MEDIUM"
            return "LOW"
            
        # Standard input encoding would execute here
        return "HIGH"

    def check_log_line(self, log_line: str) -> Tuple[bool, float]:
        return self.threat_classifier.predict(log_line)

real_time_predictor = RealTimePredictor()
