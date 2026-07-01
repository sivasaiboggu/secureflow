from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class ComplianceCheckResponse(BaseModel):
    id: str
    scan_id: str
    framework: str
    control_id: str
    title: str
    status: str
    resource_id: str
    evidence: Optional[Dict[str, Any]] = None
    checked_at: datetime

    class Config:
        from_attributes = True
