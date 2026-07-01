import numpy as np
import logging
from typing import Dict, Any, Tuple, List
from app.ml.severity_model import SeverityPredictionModel
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.threat_classifier import ThreatClassifier

logger = logging.getLogger(__name__)

class MLService:
    """Consolidated orchestration API for threat log classifiers, severity, and anomaly detection"""
    
    def __init__(self):
        self.severity_model = SeverityPredictionModel(model_dir="./models/severity")
        self.anomaly_detector = AnomalyDetector(model_dir="./models/anomaly")
        self.threat_classifier = ThreatClassifier(model_dir="./models/threat")
        
        # Proactively load models
        self.severity_model.load()
        self.anomaly_detector.load()
        self.threat_classifier.load()

    def predict_severity(self, resource_type: str, vuln_type: str, provider: str, 
                         cvss_score: float, exposure_score: float) -> Dict[str, Any]:
        """Runs the neural model and generates explainable CVSS estimations with confidence scores"""
        cat_features = [resource_type, vuln_type, provider, "CIS", "us-east-1"]
        # Match numerical dimensions: cvss_base_score, exploitability, impact, age, prev_vulns, exposure
        num_features = [cvss_score, 1.2, 3.4, 30.0, 5.0, exposure_score]
        
        severity, confidence = self.severity_model.predict(cat_features, num_features)
        explanation = self.severity_model.get_explainability(cat_features, num_features)
        
        return {
            "predicted_severity": severity,
            "confidence": confidence,
            "feature_importance": explanation
        }

    def analyze_api_logs(self, api_metrics: List[float]) -> Dict[str, Any]:
        """Evaluates whether API sequence is anomalous using the autoencoder & Isolation Forest"""
        sample = np.array([api_metrics], dtype=np.float32)
        is_anomaly, score = self.anomaly_detector.predict_anomaly(sample)
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "algorithm": "Autoencoder + Isolation Forest"
        }

    def scan_log_for_threats(self, log_payload: str) -> Dict[str, Any]:
        """Parses CloudTrail or system payloads to classify presence of immediate attacker intent"""
        is_threat, confidence = self.threat_classifier.predict_threat(log_payload)
        return {
            "is_threat": is_threat,
            "confidence": confidence,
            "classification": "SUSPICIOUS" if is_threat else "NORMAL"
        }

ml_service = MLService()
