import uuid
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database.models import Scan, CloudAccount, Vulnerability, ComplianceCheck, Remediation
from app.tasks.scan_tasks import run_cloud_scan_task
from app.security.credential_store import open_credentials

class ScanDispatchUnknown(RuntimeError):
    """The broker response did not establish whether a job was accepted."""

    def __init__(self, scan_id: str):
        self.scan_id = scan_id
        super().__init__('Queue acceptance could not be confirmed. Check this scan before trying again.')


class ScanService:
    """Business logic orchestrator managing scanning runs, fetching findings, and remediations"""
    
    def trigger_scan(self, db: Session, cloud_account_id: str, organization_id: str) -> Scan:
        # Check cloud account existence
        account = db.query(CloudAccount).filter(
            CloudAccount.id == cloud_account_id,
            CloudAccount.organization_id == organization_id,
            CloudAccount.is_active.is_(True),
        ).first()
        if not account:
            raise ValueError('Cloud account not found or inactive.')
            
        credentials = open_credentials(account.credentials or {}, account.id, account.organization_id, account.provider)
        if account.provider.lower() != "aws":
            raise ValueError("Only AWS scans are supported. Other providers are not ready.")
        mode = credentials.get("scan_mode", "real")
        if mode not in ("real", "demo"):
            raise ValueError("Scan mode must be real or demo.")
        if mode == "real" and not (credentials.get("aws_access_key_id") and credentials.get("aws_secret_access_key")):
            raise ValueError("AWS credentials are missing. Choose an explicit demo account for sample data.")

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
        
        # Never spawn an untracked scan thread after an ambiguous broker error.
        try:
            run_cloud_scan_task.delay(scan_id, cloud_account_id, organization_id)
        except Exception:
            # A publish response can be lost after acceptance. Do not overwrite
            # RUNNING/completed worker state or label an unconfirmed job failed.
            db.rollback()
            raise ScanDispatchUnknown(scan_id) from None

        # Update last scanned at timestamp
        account.last_scanned_at = datetime.utcnow()
        db.commit()
        
        return scan

    def recover_interrupted_scans(self, db: Session, stale_after: timedelta = timedelta(minutes=35), now: Optional[datetime] = None) -> int:
        """Mark RUNNING scans whose worker stopped reporting as FAILED.

        A worker killed outside Python (hard time limit, OOM, host loss) never
        runs its failure handler, so its scan would stay RUNNING forever and the
        claim guard would refuse every later delivery. A healthy worker finishes
        or is hard-killed within the configured task time limit, so a RUNNING row
        whose last claim is older than ``stale_after`` (which must exceed that
        limit) cannot still be running. Rows claimed before start-time tracking
        existed have no ``started_at`` and fall back to ``created_at``; dispatch
        happened immediately after creation, so it approximates the claim time.
        Recovery marks the scan FAILED with a completion time, making it visible
        and reclaimable by a later delivery. Scans a live worker may still own
        are never touched, and no finding rows can exist for an interrupted run
        because findings commit in the same transaction as the final status.
        """
        now = now or datetime.utcnow()
        cutoff = now - stale_after
        recovered = db.query(Scan).filter(
            Scan.status == "RUNNING",
            func.coalesce(Scan.started_at, Scan.created_at) < cutoff,
        ).update({"status": "FAILED", "completed_at": now}, synchronize_session=False)
        db.commit()
        return recovered

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

    def get_vulnerability(self, db: Session, vulnerability_id: str, organization_id: str) -> Optional[Vulnerability]:
        return db.query(Vulnerability).join(Scan).filter(
            Vulnerability.id == vulnerability_id, Scan.organization_id == organization_id
        ).first()

    def apply_remediation(self, db: Session, vulnerability_id: str, user_email: str, organization_id: str) -> Remediation:
        vuln = self.get_vulnerability(db, vulnerability_id, organization_id)
        if not vuln:
            raise ValueError('Finding not found.')
            
        if not vuln.terraform_fix or not vuln.terraform_fix.strip():
            raise ValueError('No Terraform template is available for review.')

        # Save a plan for review; this service does not execute Terraform.
        rem_id = str(uuid.uuid4())
        remediation = Remediation(
            id=rem_id,
            vulnerability_id=vulnerability_id,
            remediation_type="TERRAFORM",
            code=vuln.terraform_fix,
            status="PENDING",
            executed_by=None,
            executed_at=None
        )
        db.add(remediation)
        
        # Leave the finding open until a separately verified repair is executed.
        db.commit()
        db.refresh(remediation)
        return remediation

scan_service = ScanService()
