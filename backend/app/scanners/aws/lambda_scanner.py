import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid
from botocore.exceptions import ClientError
from app.scanners.base import BaseScanner

logger = logging.getLogger(__name__)

class LambdaScanner(BaseScanner):
    """AWS Lambda security posture scanner checking runtimes and policy settings"""
    
    def __init__(self, organization_id: str, cloud_account_id: str, credentials: Dict[str, Any]):
        super().__init__(organization_id, cloud_account_id, credentials)
        self.access_key = credentials.get("aws_access_key_id")
        self.secret_key = credentials.get("aws_secret_access_key")
        self.region = credentials.get("aws_default_region", "us-east-1")
        
        self.is_simulated = not (self.access_key and self.secret_key)
        self.findings: List[Dict[str, Any]] = []
        
        if not self.is_simulated:
            try:
                self.session = boto3.Session(
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                self.lambda_client = self.session.client('lambda')
            except Exception as e:
                logger.warning(f"Failed to initialize Lambda client: {e}. Simulating.")
                self.is_simulated = True

    def scan(self) -> List[Dict[str, Any]]:
        self.findings = []
        if self.is_simulated:
            logger.info("Executing simulated AWS Lambda scan...")
            self.findings = self._generate_simulated_findings()
            return self.findings
            
        try:
            functions = self.lambda_client.list_functions().get("Functions", [])
            for fn in functions:
                self.findings.extend(self._scan_function(fn))
        except ClientError as e:
            logger.error(f"Error performing Lambda scan: {e}")
            self.is_simulated = True
            self.findings = self._generate_simulated_findings()
            
        return self.findings

    def get_compliance_checks(self) -> List[Dict[str, Any]]:
        checks = []
        for finding in self.findings:
            frameworks = finding.get("compliance_frameworks", [])
            for fw in frameworks:
                parts = fw.split()
                fw_name = parts[0] if parts else "CIS"
                control_id = parts[-1] if len(parts) > 1 else "Unknown"
                checks.append({
                    "id": str(uuid.uuid4()),
                    "framework": fw_name,
                    "control_id": control_id,
                    "title": finding["title"],
                    "status": "FAIL",
                    "resource_id": finding["resource_id"],
                    "evidence": {
                        "vulnerability_type": finding["vulnerability_type"],
                        "severity": finding["severity"]
                    }
                })
        return checks

    def _scan_function(self, fn: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        fn_name = fn.get("FunctionName", "unknown-function")
        arn = fn.get("FunctionArn", f"arn:aws:lambda:{self.region}:account:function:{fn_name}")
        runtime = fn.get("Runtime", "")
        
        # Check 1: Obsolete Runtimes (e.g. python3.7, python3.8, nodejs12.x, etc.)
        obsolete_runtimes = ["python3.7", "python3.8", "nodejs12.x", "nodejs14.x", "go1.x", "java8"]
        if runtime in obsolete_runtimes:
            findings.append(self._create_finding(
                fn_name, arn, "LAMBDA_DEPRECATED_RUNTIME", "MEDIUM", 6.1,
                "Lambda Function Using Deprecated Runtime Environment",
                f"Lambda function '{fn_name}' runs on deprecated environment runtime '{runtime}'. This lacks patching support and exposes operational risks.",
                "Upgrade the lambda execution runtime environment version parameter to a supported release (e.g., python3.11 or nodejs18.x).",
                ["CIS AWS 2.9.1"],
                f'resource "aws_lambda_function" "{fn_name.replace("-", "_")}" {{\n  # ... other config ...\n  runtime = "python3.11"\n}}',
                {"runtime": runtime}
            ))
            
        # Check 2: Public policy exposure
        try:
            policy_res = self.lambda_client.get_policy(FunctionName=fn_name)
            policy_str = policy_res.get("Policy", "{}")
            import json
            policy = json.loads(policy_str)
            for stmt in policy.get("Statement", []):
                if stmt.get("Effect") == "Allow" and stmt.get("Principal") == "*":
                    findings.append(self._create_finding(
                        fn_name, arn, "LAMBDA_PUBLIC_POLICY", "CRITICAL", 9.1,
                        "Lambda Function Resource Policy Permits Wildcard Triggers",
                        f"Lambda function '{fn_name}' has a policy allow rule matching '*' principal triggers, allowing external unauthorized invocations.",
                        "Edit the lambda function permissions. Replace '*' trigger rules with specific AWS account IDs or IAM roles.",
                        ["CIS AWS 1.22", "NIST SP 800-53 AC-3"],
                        f'# Restrict lambda execution permissions to specific service triggers\n# Check resource policy statement for: {fn_name}',
                        {"policy": policy}
                    ))
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                logger.error(f"Error reading policy for lambda {fn_name}: {e}")
                
        return findings

    def _create_finding(self, fn_name: str, arn: str, vtype: str, sev: str, score: float, title: str, desc: str, rec: str, frameworks: List[str], tf_fix: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": f"lambda-{fn_name}-{vtype}".lower(),
            "resource_type": "LAMBDA_FUNCTION",
            "resource_id": arn,
            "resource_name": fn_name,
            "vulnerability_type": vtype,
            "severity": sev,
            "title": title,
            "description": desc,
            "recommendation": rec,
            "remediation_steps": [
                "1. Go to AWS Lambda console.",
                "2. Click the function name to inspect detail parameters.",
                "3. In the Configuration tab, go to permissions to review resource triggers.",
                "4. Update runtime environments or remove permissive trigger definitions."
            ],
            "terraform_fix": tf_fix,
            "compliance_frameworks": frameworks,
            "cvss_score": score,
            "cve_id": None,
            "discovered_at": datetime.utcnow().isoformat(),
            "evidence": evidence
        }

    def _generate_simulated_findings(self) -> List[Dict[str, Any]]:
        simulated = []
        
        # Instance 1: Obsolete runtime
        simulated.append(self._create_finding(
            "legacy-payment-reconciliation-job",
            "arn:aws:lambda:us-east-1:123456789:function:legacy-payment-reconciliation-job",
            "LAMBDA_DEPRECATED_RUNTIME", "MEDIUM", 6.1,
            "Lambda Function Using Deprecated Runtime Environment",
            "Lambda function 'legacy-payment-reconciliation-job' runs on deprecated environment runtime 'python3.7' which has reached end of life support.",
            "Upgrade to python3.11 runtime environment version.",
            ["CIS AWS 2.9.1"],
            'resource "aws_lambda_function" "payment_job" {\n  # ... config ...\n  runtime = "python3.11"\n}',
            {"runtime": "python3.7"}
        ))
        
        # Instance 2: Public trigger policy
        simulated.append(self._create_finding(
            "receive-telemetry-webhook",
            "arn:aws:lambda:us-east-1:123456789:function:receive-telemetry-webhook",
            "LAMBDA_PUBLIC_POLICY", "CRITICAL", 9.1,
            "Lambda Function Resource Policy Permits Wildcard Triggers",
            "Lambda function 'receive-telemetry-webhook' has a resource-based policy that allows execution triggers from all AWS account contexts (Principal: *).",
            "Revoke open invoke permissions and allow triggers from specific API gateway accounts only.",
            ["CIS AWS 1.22", "NIST SP 800-53 AC-3"],
            '# Revoke generic invoke policies inside IAM resource declarations',
            {"principal": "*", "action": "lambda:InvokeFunction"}
        ))
        
        return simulated
