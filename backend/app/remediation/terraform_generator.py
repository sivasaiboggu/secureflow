import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Identifiers that may appear in generated HCL. Anything outside this set
# (quotes, whitespace, semicolons, $ interpolation, ...) is rejected instead
# of being interpolated into a Terraform string, where it could break the
# plan or inject arbitrary HCL.
_SAFE_RESOURCE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]{0,190}$")
_SAFE_TF_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _validate_resource_id(resource_id: str) -> str:
    """Return a resource identifier safe to embed in generated HCL."""
    if not isinstance(resource_id, str) or not _SAFE_RESOURCE_ID.match(resource_id):
        raise ValueError(
            "Refusing to generate Terraform for an unsafe resource identifier: "
            "identifiers must use only letters, digits, '.', '_', '-' and '/'."
        )
    return resource_id


def _hcl_escape(value: str) -> str:
    """Escape a value for a double-quoted HCL string."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("${", "$${")


def _tf_name(resource_id: str) -> str:
    """Derive a valid Terraform resource label from a resource identifier."""
    name = resource_id.split(":")[-1].split("/")[-1].replace(".", "_").replace("-", "_")
    if not _SAFE_TF_NAME.match(name):
        raise ValueError("Cannot derive a safe Terraform resource label from the resource identifier.")
    return name


class TerraformRemediationGenerator:
    """Generates and writes Terraform infrastructure fix templates to harden cloud deployments"""

    def generate_s3_block_fix(self, bucket_name: str) -> str:
        bucket_name = _validate_resource_id(bucket_name)
        safe_name = _tf_name(bucket_name)
        return f'''# Remediation for S3 Bucket public access block setting override
resource "aws_s3_bucket_public_access_block" "{safe_name}_remediated" {{
  bucket = "{_hcl_escape(bucket_name)}"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}
'''

    def generate_s3_encryption_fix(self, bucket_name: str) -> str:
        bucket_name = _validate_resource_id(bucket_name)
        safe_name = _tf_name(bucket_name)
        return f'''# Remediation enabling SSE default bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "{safe_name}_encryption" {{
  bucket = "{_hcl_escape(bucket_name)}"

  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
  }}
}}
'''

    def generate_vpc_flow_logs_fix(self, vpc_id: str, account_id: Optional[str] = None, region: Optional[str] = None) -> str:
        vpc_id = _validate_resource_id(vpc_id)
        safe_name = _tf_name(vpc_id)
        if account_id is not None and not re.fullmatch(r"[0-9]{12}", account_id):
            raise ValueError("account_id must be a 12-digit AWS account ID.")
        if region is not None and not re.fullmatch(r"[a-z]{2}-[a-z]+-[0-9]", region):
            raise ValueError("region must look like an AWS region, e.g. us-east-1.")
        # Placeholders are explicit and must be replaced before apply; the
        # generated plan never pretends to know the operator's account.
        account = account_id or "REPLACE_WITH_ACCOUNT_ID"
        aws_region = region or "REPLACE_WITH_REGION"
        return f'''# Remediation for VPC Flow logging setup
# TODO: replace REPLACE_WITH_ACCOUNT_ID / REPLACE_WITH_REGION with the
# target account and region before applying. This plan is review-only.
resource "aws_flow_log" "{safe_name}_flow_logs" {{
  iam_role_arn    = "arn:aws:iam::{account}:role/vpc-flow-logs-service-role"
  log_destination = "arn:aws:logs:{aws_region}:{account}:log-group/vpc-flow-logs"
  traffic_type    = "ALL"
  vpc_id          = "{_hcl_escape(vpc_id)}"
}}
'''

    def generate_imds_required_fix(self, instance_id: str) -> str:
        instance_id = _validate_resource_id(instance_id)
        safe_name = _tf_name(instance_id)
        return f'''# Remediation enforcing IMDSv2 tokens access inside EC2
resource "aws_instance_metadata_defaults" "{safe_name}_imds_enforce" {{
  http_tokens = "required"
}}
'''

    def get_remediation_code(self, vulnerability_type: str, resource_id: str) -> str:
        """Returns the compiled block depending on finding details"""
        # Resource identifier cleaning
        resource_id = _validate_resource_id(resource_id)
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
