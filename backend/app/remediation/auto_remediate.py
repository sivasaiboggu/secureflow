import boto3
import logging
from typing import Dict, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class AutoRemediator:
    """Executes programmatic patches directly on cloud endpoints for validated threats"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.access_key = credentials.get("aws_access_key_id")
        self.secret_key = credentials.get("aws_secret_access_key")
        self.region = credentials.get("aws_default_region", "us-east-1")
        
        self.enabled = bool(self.access_key and self.secret_key)
        if self.enabled:
            self.session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )

    def remediate_s3_public_access(self, bucket_name: str) -> bool:
        """Invokes S3 put_public_access_block API to encrypt/lockdown open buckets"""
        if not self.enabled:
            logger.warning(f"Simulating S3 block public access remediation for bucket: {bucket_name}")
            return True
            
        try:
            s3 = self.session.client("s3")
            s3.put_public_access_block(
                Bucket=bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            logger.info(f"Remediated public access on bucket {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed S3 public access remediation for {bucket_name}: {e}")
            return False

    def remediate_s3_encryption(self, bucket_name: str) -> bool:
        """Enables SSE-S3 AES-256 encryption configurations on target S3 bucket"""
        if not self.enabled:
            logger.warning(f"Simulating S3 encryption remediation for bucket: {bucket_name}")
            return True
            
        try:
            s3 = self.session.client("s3")
            s3.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'AES256'
                            }
                        }
                    ]
                }
            )
            logger.info(f"Remediated storage encryption on bucket {bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed S3 encryption remediation for {bucket_name}: {e}")
            return False

    def execute(self, vulnerability_type: str, resource_id: str) -> bool:
        """Router executing auto-remediation depending on classification"""
        res_name = resource_id.split(":")[-1].split("/")[-1]
        vtype = vulnerability_type.upper()
        
        if "PUBLIC_ACCESS" in vtype or "PUBLIC_ACL" in vtype:
            return self.remediate_s3_public_access(res_name)
        elif "NO_ENCRYPTION" in vtype:
            return self.remediate_s3_encryption(res_name)
            
        logger.warning(f"Auto-remediation not supported for category: {vulnerability_type}")
        return False
