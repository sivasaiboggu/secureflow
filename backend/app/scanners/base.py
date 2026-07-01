from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScanner(ABC):
    """Abstract base class for cloud posture scanners"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        self.organization_id = organization_id
        self.cloud_account_id = cloud_account_id
        self.credentials = credentials
        
    @abstractmethod
    def scan(self) -> List[Dict[str, Any]]:
        """Run scanning operation and return list of findings/vulnerabilities"""
        pass
        
    @abstractmethod
    def get_compliance_checks(self) -> List[Dict[str, Any]]:
        """Map scanning findings to structured compliance checks (CIS, NIST, etc.)"""
        pass
