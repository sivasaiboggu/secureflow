import re
from typing import Dict, Any

# Simple regex formats checking cloud identifier signatures
AWS_ACCESS_KEY_REGEX = re.compile(r'^AKIA[0-9A-Z]{16}$')
AWS_SECRET_KEY_REGEX = re.compile(r'^[0-9a-zA-Z+/]{40}$')

def validate_aws_credentials(credentials: Dict[str, Any]) -> bool:
    """Verifies access keys match syntax parameters to secure API payloads"""
    access_key = credentials.get("aws_access_key_id", "")
    secret_key = credentials.get("aws_secret_access_key", "")
    
    # Allow empty configurations for local simulated loops
    if not access_key and not secret_key:
        return True
        
    if not AWS_ACCESS_KEY_REGEX.match(access_key):
        return False
    if not AWS_SECRET_KEY_REGEX.match(secret_key):
        return False
        
    return True

def validate_cidr_block(cidr: str) -> bool:
    """Confirms string layout matches standard IPv4 CIDR range formats (e.g. 10.0.0.0/16)"""
    cidr_regex = re.compile(
        r'^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[1-2][0-9]|3[0-2])$'
    )
    if not cidr_regex.match(cidr):
        return False
    # Validate each byte range does not exceed 255
    parts = cidr.split('/')[0].split('.')
    return all(0 <= int(part) <= 255 for part in parts)
