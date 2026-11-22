"""Control-level compliance: the score must be a pass rate over evaluated
controls, not over failure rows.

Before 1.0.7 the scan pipeline only wrote finding-derived compliance
rows, and every one of those is a FAIL (a row only exists when something
failed). The dashboard score and the compliance summary therefore read
0% after every scan — demo or real — by construction, and no code path
produced the "76% = 16/21" figure quoted in the 1.0.6 notes. The scan
worker now writes one row per CIS control (PASS when no finding violates
it), the scan counters count those rows, and the summary scores from
them when they exist.
"""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.compliance.frameworks.cis_benchmark import cis_evaluator
from app.config.database import Base
from app.database.models import (
    CloudAccount,
    ComplianceCheck,
    Organization,
    Scan,
    User,
)


def _demo_findings():
    from app.scanners.aws.cloudtrail_scanner import CloudTrailScanner
    from app.scanners.aws.ec2 import EC2Scanner
    from app.scanners.aws.iam import IAMScanner
    from app.scanners.aws.lambda_scanner import LambdaScanner
    from app.scanners.aws.rds_scanner import RDSScanner
    from app.scanners.aws.s3 import S3Scanner
    from app.scanners.aws.vpc_scanner import VPCScanner

    creds = {"scan_mode": "demo", "aws_default_region": "us-east-1"}
    findings = []
    for cls in (S3Scanner, EC2Scanner, IAMScanner, RDSScanner,
                LambdaScanner, VPCScanner, CloudTrailScanner):
        findings.extend(cls("org", "acct", creds).scan())
    return findings


class EvaluatorTests(unittest.TestCase):
    def test_demo_scan_cis_score_is_one_of_eight(self):
        result = cis_evaluator.evaluate_compliance(_demo_findings())
        self.assertEqual(result["score"], 12.5)
        self.assertEqual([c["control_id"] for c in result["passed_controls"]], ["1.8"])
        self.assertEqual(len(result["failed_controls"]), 7)

    def test_control_matching_is_by_token_not_substring(self):
        # "CIS AWS 2.1.2" contains "1.2" as a substring, and "PCI-DSS
        # 1.2" is another framework's control with the same number.
        # Neither may fail CIS control 1.2.
        result = cis_evaluator.evaluate_compliance([
            {"resource_id": "arn:aws:s3:::ssl-bucket",
             "compliance_frameworks": ["CIS AWS 2.1.2"]},
            {"resource_id": "arn:aws:rds:us-east-1:1:db:pci-db",
             "compliance_frameworks": ["PCI-DSS 1.2"]},
        ])
        failed = {c["control_id"]: c for c in result["failed_controls"]}
        self.assertNotIn("1.2", failed)
        self.assertEqual(sorted(failed), ["2.1.2"])
        self.assertEqual(result["score"], 87.5)

    def test_seed_findings_score_four_of_eight(self):
        frameworks = [
            ["CIS AWS 2.1.5", "NIST 800-53"], ["CIS AWS 1.16"],
            ["CIS AWS 1.2"], ["CIS AWS 4.3", "PCI-DSS 1.2"],
            ["CIS AWS 2.9.1"], ["CIS AWS 4.3", "NIST SP 800-53"],
            ["CIS AWS 3.2", "NIST SP 800-53"],
        ]
        findings = [{"resource_id": f"res-{i}", "compliance_frameworks": fw}
                    for i, fw in enumerate(frameworks)]
        result = cis_evaluator.evaluate_compliance(findings)
        self.assertEqual(result["score"], 50.0)
        self.assertEqual(sorted(c["control_id"] for c in result["passed_controls"]),
                         ["1.14", "1.8", "2.1.1", "2.1.2"])


def _load_worker():
    taskmod = types.ModuleType("app.tasks.celery_app")
    taskmod.celery_app = Mock()
    taskmod.celery_app.task = lambda **kw: lambda fn: fn
    mlmod = types.ModuleType("app.services.ml_service")
    mlmod.ml_service = Mock()
    mlmod.ml_service.predict_severity.return_value = {"predicted_severity": "HIGH"}
    patcher = patch.dict(sys.modules, {"app.tasks.celery_app": taskmod,
                                       "app.services.ml_service": mlmod})
    patcher.start()
    path = Path(__file__).parents[1] / "app/tasks/scan_tasks.py"
    spec = importlib.util.spec_from_file_location("test_control_level_worker", path)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    return worker, patcher


class ScanWorkerControlLevelTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
        db = self.session()
        db.add(Organization(id="org", name="Synthetic"))
        db.add(CloudAccount(id="account", name="Demo", provider="aws",
                            organization_id="org",
                            credentials={"scan_mode": "demo"}, is_active=True))
        db.add(Scan(id="one", organization_id="org", cloud_account_id="account"))
        db.commit()
        db.close()
        self.worker, self.patcher = _load_worker()
        self.worker.SessionLocal = self.session
        for name in ["S3Scanner", "EC2Scanner", "IAMScanner", "RDSScanner",
                     "LambdaScanner", "VPCScanner", "CloudTrailScanner"]:
            cls = Mock()
            cls.return_value.scan.return_value = []
            cls.return_value.get_compliance_checks.return_value = []
            setattr(self.worker, name, cls)

    def tearDown(self):
        self.patcher.stop()
        self.engine.dispose()

    def test_scan_counters_count_control_rows(self):
        finding = dict(id="x", resource_type="S3_BUCKET", resource_id="arn:aws:s3:::b",
                       resource_name="b", vulnerability_type="PUBLIC_ACCESS_NOT_BLOCKED",
                       cvss_score=9.1, title="t", description="d", recommendation="r",
                       remediation_steps=[], terraform_fix="",
                       compliance_frameworks=["CIS AWS 2.1.5"], cve_id=None,
                       evidence={})
        self.worker.S3Scanner.return_value.scan.return_value = [finding]
        self.worker.S3Scanner.return_value.get_compliance_checks.return_value = [
            dict(framework="CIS", control_id="2.1.5", title="t", status="FAIL",
                 resource_id="arn:aws:s3:::b", evidence={})]
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(), "one", "account", "org"))
        db = self.session()
        scan = db.get(Scan, "one")
        # One finding violates one of the eight controls; the other seven pass.
        self.assertEqual((scan.passed_checks, scan.failed_checks), (7, 1))
        rows = db.query(ComplianceCheck).filter_by(scan_id="one").all()
        control_rows = [r for r in rows if (r.evidence or {}).get("control_level")]
        self.assertEqual(len(control_rows), 8)
        self.assertEqual(len(rows), 9)  # 8 control rows + 1 finding-derived row
        self.assertEqual(
            sorted(r.control_id for r in control_rows if r.status == "PASS"),
            ["1.14", "1.16", "1.2", "1.8", "2.1.1", "2.1.2", "4.3"])
        failed = [r for r in control_rows if r.status == "FAIL"]
        self.assertEqual([r.control_id for r in failed], ["2.1.5"])
        self.assertEqual(failed[0].resource_id, "arn:aws:s3:::b")
        db.close()

    def test_empty_scan_passes_all_eight_controls(self):
        self.assertTrue(self.worker.run_cloud_scan_task(Mock(), "one", "account", "org"))
        db = self.session()
        scan = db.get(Scan, "one")
        self.assertEqual((scan.passed_checks, scan.failed_checks), (8, 0))
        db.close()


class ComplianceSummaryControlLevelTests(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timedelta

        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
        db = self.session()
        db.add(Organization(id="org", name="Synthetic"))
        db.add(User(id="u1", email="a@example.com", hashed_password="x",
                    organization_id="org"))
        db.add(CloudAccount(id="account", name="Demo", provider="aws",
                            organization_id="org",
                            credentials={"scan_mode": "demo"}, is_active=True))
        now = datetime(2026, 11, 22, 10, 0, 0)
        db.add(Scan(id="new", organization_id="org", cloud_account_id="account",
                    status="DEMO_COMPLETED", passed_checks=7, failed_checks=1,
                    completed_at=now))
        db.add(Scan(id="old", organization_id="org", cloud_account_id="account",
                    status="COMPLETED", passed_checks=0, failed_checks=7,
                    completed_at=now - timedelta(days=1)))
        self.now = now
        db.commit()
        db.close()

    def tearDown(self):
        self.engine.dispose()

    def _add_rows(self, scan_id, rows):
        db = self.session()
        for i, (framework, control_id, status, control_level) in enumerate(rows):
            db.add(ComplianceCheck(
                id=f"{scan_id}-{i}", scan_id=scan_id, framework=framework,
                control_id=control_id, title="t", status=status,
                resource_id="r",
                evidence={"control_level": True} if control_level else {}))
        db.commit()
        db.close()

    def _summary(self):
        from app.api.v1.endpoints.compliance import get_compliance_summary

        db = self.session()
        user = db.get(User, "u1")
        result = get_compliance_summary(db=db, current_user=user)
        db.close()
        return result

    def test_summary_scores_control_level_rows_only(self):
        # Latest scan: 7 finding-derived FAIL rows plus the 8 control
        # rows (7 PASS, 1 FAIL). The score must come from the controls.
        finding_rows = [("CIS", "2.1.5", "FAIL", False)] * 7
        control_rows = [("CIS", cid, "PASS", True)
                        for cid in ("1.2", "1.8", "1.14", "1.16", "2.1.1", "2.1.2", "4.3")]
        control_rows.append(("CIS", "2.1.5", "FAIL", True))
        self._add_rows("new", finding_rows + control_rows)
        self.assertEqual(self._summary(), {"CIS": 87.5})

    def test_summary_falls_back_when_no_control_rows_exist(self):
        # Pre-1.0.7 data: only finding-derived rows. Scores from them
        # rather than showing nothing.
        self._add_rows("new", [("CIS", "2.1.5", "FAIL", False)] * 7)
        self.assertEqual(self._summary(), {"CIS": 0.0})


if __name__ == "__main__":
    unittest.main()
