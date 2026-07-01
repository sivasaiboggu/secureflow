import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TerraformRemediationGenerator:
    """Generates and writes Terraform infrastructure fix templates to harden cloud deployments"""
    
    def generate_s3_block_fix(self, bucket_name: str) -> str:
        safe_name = bucket_name.replace(".", "_").replace("-", "_")
        return f'''# Remediation for S3 Bucket public access block setting override
resource "aws_s3_bucket_public_access_block" "{safe_name}_remediated" {{
  bucket = "{bucket_name}"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}
'''

    def generate_s3_encryption_fix(self, bucket_name: str) -> str:
        safe_name = bucket_name.replace(".", "_").replace("-", "_")
        return f'''# Remediation enabling SSE default bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "{safe_name}_encryption" {{
  bucket = "{bucket_name}"

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}
'''

    def generate_vpc_flow_logs_fix(self, vpc_id: str) -> str:
        safe_name = vpc_id.replace("-", "_")
        return f'''# Remediation for VPC Flow logging setup
resource "aws_flow_log" "{safe_name}_flow_logs" {{
  iam_role_arn    = "arn:aws:iam::your-account:role/vpc-flow-logs-service-role"
  log_destination = "arn:aws:logs:us-east-1:your-account:log-group/vpc-flow-logs"
  traffic_type    = "ALL"
  vpc_id          = "{vpc_id}"
}}
'''

    def generate_imds_required_fix(self, instance_id: str) -> str:
        safe_name = instance_id.replace("-", "_")
        return f'''# Remediation enforcing IMDSv2 tokens access inside EC2
resource "aws_instance_metadata_defaults" "{safe_name}_imds_enforce" {{
  http_tokens = "required"
}}
'''

    def get_remediation_code(self, vulnerability_type: str, resource_id: str) -> str:
        """Returns the compiled block depending on finding details"""
        # Resource identifier cleaning
        res_name = resource_id.split(":")[-1].split("/")[-1]
        
        vtype = vulnerability_type.upper()
        if "PUBLIC_ACCESS" in vtype or "PUBLIC_ACL" in vtype:
            return self.generate_s3_block_fix(res_name)
        elif "NO_ENCRYPTION" in vtype:
            return self.generate_s3_encryption_fix(res_name)
        elif "FLOW_LOGS" in vtype:
            return self.generate_vpc_flow_logs_fix(res_name)
        elif "IMDS" in vtype:
            return self.generate_imds_required_fix(res_name)
            
        return f'''# Manual review required for finding category {vulnerability_type}
# Resource: {resource_id}
# Apply security policies following your corporate directory templates.
'''

tf_generator = TerraformRemediationGenerator()
