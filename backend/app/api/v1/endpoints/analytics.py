from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.config.database import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.services.analytics_service import analytics_service
from app.ml.risk_forecaster import risk_forecaster

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
def get_dashboard_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Compiles total open vulnerability findings and counts sorted by categories"""
    return analytics_service.get_summary_stats(db, current_user.organization_id)

@router.get("/forecast", response_model=Dict[str, Any])
def get_compliance_score_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Projects posture drift from real completed-scan pass rates; an unavailable projection names its reason instead of inventing history."""
    points = analytics_service.get_scan_pass_rates(db, current_user.organization_id)
    historical = [p["score"] for p in points]
    scores = risk_forecaster.forecast_next_30_days(historical)
    if scores is None:
        return {
            "available": False,
            "scores": [],
            "method": "unavailable",
            "calibrated": False,
            "detail": "A locally trained LSTM and at least seven completed scans with evaluated checks are required. No projection was invented.",
        }
    return {"available": True, "scores": scores, "method": "local_lstm_uncalibrated", "calibrated": False}
