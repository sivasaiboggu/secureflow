from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any, List
from app.database.models import Vulnerability, Scan

class AnalyticsService:
    """Calculates posture compliance trends and groups vulnerability metrics for dashboard widgets"""
    
    def get_summary_stats(self, db: Session, org_id: str) -> Dict[str, Any]:
        # Count totals
        total_vulns = db.query(Vulnerability).join(Scan).filter(
            Scan.organization_id == org_id,
            Vulnerability.status == "OPEN"
        ).count()
        
        avg_cvss = db.query(func.avg(Vulnerability.cvss_score)).join(Scan).filter(
            Scan.organization_id == org_id,
            Vulnerability.status == "OPEN"
        ).scalar() or 0.0
        
        # Group by severity
        severity_counts = db.query(
            Vulnerability.severity, func.count(Vulnerability.id)
        ).join(Scan).filter(
            Scan.organization_id == org_id,
            Vulnerability.status == "OPEN"
        ).group_by(Vulnerability.severity).all()
        
        # Group by resource type
        resource_counts = db.query(
            Vulnerability.resource_type, func.count(Vulnerability.id)
        ).join(Scan).filter(
            Scan.organization_id == org_id,
            Vulnerability.status == "OPEN"
        ).group_by(Vulnerability.resource_type).all()
        
    def get_scan_pass_rates(self, db: Session, org_id: str) -> List[Dict[str, Any]]:
        """Real per-scan pass rates from completed scans that evaluated at least one check."""
        scans = db.query(Scan).filter(
            Scan.organization_id == org_id,
            Scan.status == "COMPLETED"
        ).order_by(Scan.completed_at.asc()).all()
        points = []
        for s in scans:
            total = (s.passed_checks or 0) + (s.failed_checks or 0)
            if total > 0:
                points.append({
                    "date": s.completed_at.isoformat() if s.completed_at else None,
                    "score": round(s.passed_checks / total * 100.0, 2),
                })
        return points

        return {
            "total_open_vulnerabilities": total_vulns,
            "average_cvss_score": round(float(avg_cvss), 2),
            "severity_distribution": {r[0]: r[1] for r in severity_counts},
            "resource_distribution": {r[0]: r[1] for r in resource_counts}
        }

analytics_service = AnalyticsService()
