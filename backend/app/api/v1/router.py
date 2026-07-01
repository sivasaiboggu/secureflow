from fastapi import APIRouter
from app.api.v1.endpoints import auth, scans, vulnerabilities, compliance, analytics, remediation

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["vulnerabilities"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(remediation.router, prefix="/remediation", tags=["remediation"])
