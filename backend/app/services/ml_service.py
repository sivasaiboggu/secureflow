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
        """Explicit CVSS review rule, not inference on fabricated model features."""
        if not isinstance(cvss_score, (int, float)) or isinstance(cvss_score, bool) or not np.isfinite(cvss_score) or not 0 <= cvss_score <= 10:
            raise ValueError("A finite CVSS score from 0 to 10 is required.")
        severity = "CRITICAL" if cvss_score >= 9 else "HIGH" if cvss_score >= 7 else "MEDIUM" if cvss_score >= 4 else "LOW"
        # The available scanner input has no exploitability/impact/age/history
        # features. Do not invent those or label static weights as explanations.
        return {
            "predicted_severity": severity,
            "confidence": None,
            "feature_importance": {},
            "method": "cvss_threshold_review_rule",
            "calibrated": False,
            "explanation_available": False
        }

    def analyze_api_logs(self, api_metrics: List[float]) -> Dict[str, Any]:
        """An unavailable detector must never report normal behavior."""
        sample = np.asarray(api_metrics, dtype=np.float64)
        if sample.shape != (8,) or not np.isfinite(sample).all():
            raise ValueError("Exactly eight finite numeric metrics are required.")
        detector = self.anomaly_detector
        if detector.autoencoder is None or detector.isolation_forest is None:
            return {
                "is_anomaly": None, "anomaly_score": None,
                "method": "unavailable", "calibrated": False,
                "error": "No local anomaly model is available. No assessment was performed."
            }
        is_anomaly, score = detector.predict_anomaly(sample.reshape(1, -1))
        if not isinstance(is_anomaly, (bool, np.bool_)) or not isinstance(score, (int, float)) or not np.isfinite(score) or score < 0:
            raise ValueError("Anomaly detector returned an invalid assessment.")
        return {
            "is_anomaly": bool(is_anomaly), "anomaly_score": float(score),
            "algorithm": "Autoencoder + Isolation Forest", "calibrated": False
        }

    def scan_log_for_threats(self, log_payload: str) -> Dict[str, Any]:
        """Flags a log for human review. A heuristic or optional local-model flag is not verified threat detection."""
        is_threat, confidence = self.threat_classifier.predict_threat(log_payload)
        return {
            "is_threat": is_threat,
            "confidence": confidence,
            "classification": "FLAGGED" if is_threat else "UNFLAGGED",
            "method": self.threat_classifier.method,
            "calibrated": False
        }

ml_service = MLService()
