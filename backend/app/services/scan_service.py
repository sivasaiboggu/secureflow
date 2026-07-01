import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database.models import Scan, CloudAccount, Vulnerability, ComplianceCheck, Remediation
from app.tasks.scan_tasks import run_cloud_scan_task

class ScanService:
    """Business logic orchestrator managing scanning runs, fetching findings, and remediations"""
    
    def trigger_scan(self, db: Session, cloud_account_id: str, organization_id: str) -> Scan:
        # Check cloud account existence
        account = db.query(CloudAccount).filter(CloudAccount.id == cloud_account_id).first()
        if not account:
            raise ValueError(f"Cloud account '{cloud_account_id}' does not exist.")
            
        scan_id = str(uuid.uuid4())
        scan = Scan(
            id=scan_id,
            organization_id=organization_id,
            cloud_account_id=cloud_account_id,
            status="PENDING",
            progress=0.0
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        # Dispatch to background queue, fallback to local thread if broker is offline
        import logging
        logger = logging.getLogger(__name__)
        try:
            run_cloud_scan_task.delay(scan_id, cloud_account_id, organization_id)
        except Exception as e:
            logger.warning(f"Celery broker offline: {e}. Executing scan via local background thread.")
            import threading
            # Call the task function directly inside a background thread
            thread = threading.Thread(
                target=run_cloud_scan_task,
                args=(None, scan_id, cloud_account_id, organization_id),
                kwargs={}
            )
            thread.daemon = True
            thread.start()
        
        # Update last scanned at timestamp
        account.last_scanned_at = datetime.utcnow()
        db.commit()
        
        return scan

    def get_scan(self, db: Session, scan_id: str) -> Optional[Scan]:
        return db.query(Scan).filter(Scan.id == scan_id).first()

    def list_scans(self, db: Session, organization_id: str, skip: int = 0, limit: int = 50) -> List[Scan]:
        return db.query(Scan).filter(Scan.organization_id == organization_id)\
                             .order_by(Scan.created_at.desc())\
                             .offset(skip).limit(limit).all()

    def get_scan_vulnerabilities(self, db: Session, scan_id: str) -> List[Vulnerability]:
        return db.query(Vulnerability).filter(Vulnerability.scan_id == scan_id).all()

    def list_vulnerabilities(self, db: Session, organization_id: str, severity: Optional[str] = None, 
                             status: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Vulnerability]:
        query = db.query(Vulnerability).join(Scan).filter(Scan.organization_id == organization_id)
        if severity:
            query = query.filter(Vulnerability.severity == severity.upper())
        if status:
            query = query.filter(Vulnerability.status == status.upper())
        return query.order_by(Vulnerability.cvss_score.desc()).offset(skip).limit(limit).all()

    def apply_remediation(self, db: Session, vulnerability_id: str, user_email: str) -> Remediation:
        vuln = db.query(Vulnerability).filter(Vulnerability.id == vulnerability_id).first()
        if not vuln:
            raise ValueError(f"Vulnerability '{vulnerability_id}' not found.")
            
        # Create a new remediation request
        rem_id = str(uuid.uuid4())
        remediation = Remediation(
            id=rem_id,
            vulnerability_id=vulnerability_id,
            remediation_type="TERRAFORM",
            code=vuln.terraform_fix or "# No Terraform template provided",
            status="APPLIED",
            executed_by=user_email,
            executed_at=datetime.utcnow()
        )
        db.add(remediation)
        
        # Mark vulnerability as resolved/remediated
        vuln.status = "REMEDIATED"
        db.commit()
        db.refresh(remediation)
        return remediation

scan_service = ScanService()
