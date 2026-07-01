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

@router.get("/forecast", response_model=List[float])
def get_compliance_score_forecast(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Invokes PyTorch LSTM to project security score drift over the next 30 days"""
    from app.database.models import Scan
    
    # Query past scores sequence
    scans = db.query(Scan).filter(
        Scan.organization_id == current_user.organization_id,
        Scan.status == "COMPLETED"
    ).order_by(Scan.completed_at.asc()).all()
    
    historical = []
    for s in scans:
        total = s.passed_checks + s.failed_checks
        score = (s.passed_checks / total * 100.0) if total > 0 else 100.0
        historical.append(score)
        
    if not historical:
        historical = [100.0, 95.0, 92.0, 85.0]
        
    return risk_forecaster.forecast_next_30_days(historical)
