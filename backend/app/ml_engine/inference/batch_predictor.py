import logging
from typing import List, Dict, Any
from app.ml_engine.inference.predictor import real_time_predictor

logger = logging.getLogger(__name__)

class BatchPredictor:
    """Orchestrates batch inference tasks on list of vulnerabilities in backend workers"""
    
    def process_batch(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info(f"Processing batch of {len(findings)} findings through security ML predictor...")
        processed = []
        for f in findings:
            severity = real_time_predictor.predict_finding_severity(
                f.get("resource_type", "S3_BUCKET"),
                f.get("vulnerability_type", "PUBLIC_ACCESS"),
                f.get("provider", "aws"),
                f.get("cvss_score", 5.0)
            )
            f["severity"] = severity
            processed.append(f)
        return processed

batch_predictor = BatchPredictor()
