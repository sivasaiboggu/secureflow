from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ScanCreate(BaseModel):
    cloud_account_id: str

class ScanResponse(BaseModel):
    id: str
    organization_id: str
    cloud_account_id: str
    status: str
    progress: float
    vulnerabilities_found: int
    failed_checks: int
    passed_checks: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CloudAccountCreate(BaseModel):
    name: str
    provider: str  # aws, gcp, azure
    credentials: dict

class CloudAccountResponse(BaseModel):
    id: str
    name: str
    provider: str
    is_active: bool
    last_scanned_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
