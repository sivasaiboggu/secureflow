from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.database.models import Scan, Vulnerability, ComplianceCheck
from app.database.repositories.scan_repo import scan_repo
from app.database.repositories.vulnerability_repo import vulnerability_repo

class ReportingService:
    """Formats scan results and compliance audit logs into downloadable JSON files"""
    
    def generate_json_compliance_report(self, db: Session, scan_id: str) -> Dict[str, Any]:
        scan = scan_repo.get_by_id(db, scan_id)
        if not scan:
            raise ValueError(f"Scan '{scan_id}' not found.")
            
        vulns = vulnerability_repo.list_by_scan(db, scan_id)
        checks = db.query(ComplianceCheck).filter(ComplianceCheck.scan_id == scan_id).all()
        
        report = {
            "report_metadata": {
                "scan_id": scan_id,
                "cloud_account_id": scan.cloud_account_id,
                "generated_at": datetime_now_iso(),
                "status": scan.status
            },
            "posture_summary": {
                "total_vulnerabilities": len(vulns),
                "passed_compliance_checks": scan.passed_checks,
                "failed_compliance_checks": scan.failed_checks
            },
            "vulnerabilities_list": [
                {
                    "id": v.id,
                    "title": v.title,
                    "severity": v.severity,
                    "resource_id": v.resource_id,
                    "cvss_score": v.cvss_score
                }
                for v in vulns
            ],
            "compliance_checks_list": [
                {
                    "framework": c.framework,
                    "control_id": c.control_id,
                    "title": c.title,
                    "status": c.status,
                    "resource_id": c.resource_id
                }
                for c in checks
            ]
        }
        return report

def datetime_now_iso() -> str:
    import datetime
    return datetime.datetime.utcnow().isoformat()

reporting_service = ReportingService()
