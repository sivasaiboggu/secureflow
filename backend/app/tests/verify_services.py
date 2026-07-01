import pytest
import os
import sys
import numpy as np
from sqlalchemy.orm import Session

# Fix path to load modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.config.database import SessionLocal, Base, engine
from app.database.models import User, Organization, CloudAccount, Scan, Vulnerability
from app.scanners.aws.s3 import S3Scanner
from app.services.ml_service import ml_service

@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database connection for testing context"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()

def test_database_connection(db_session: Session):
    """Verifies connection and database mapping tables"""
    assert db_session is not None
    # Verify table query succeeds
    count = db_session.query(Organization).count()
    assert isinstance(count, int)

def test_s3_scanner_simulation():
    """Validates the simulated telemetry fallback for AWS S3 scanning runs"""
    scanner = S3Scanner("test-org", "test-acc", {})
    assert scanner.is_simulated is True
    
    findings = scanner.scan()
    assert len(findings) > 0
    
    for f in findings:
        assert f["resource_type"] == "S3_BUCKET"
        assert f["cvss_score"] > 0.0
        assert len(f["terraform_fix"]) > 0

def test_ml_severity_prediction():
    """Validates PyTorch Severity model classifications and explainability mappings"""
    # Evaluate S3 Public Access vulnerability
    prediction = ml_service.predict_severity(
        resource_type="S3_BUCKET",
        vuln_type="PUBLIC_ACCESS_NOT_BLOCKED",
        provider="aws",
        cvss_score=9.8,
        exposure_score=0.9
    )
    
    assert prediction["predicted_severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert prediction["confidence"] > 0.0
    assert "resource_type" in prediction["feature_importance"]

def test_ml_log_classification():
    """Validates BERT threat classification scores"""
    payload = "Root identity deleted critical S3 bucket policy"
    result = ml_service.scan_log_for_threats(payload)
    
    assert isinstance(result["is_threat"], bool)
    assert result["confidence"] > 0.5
