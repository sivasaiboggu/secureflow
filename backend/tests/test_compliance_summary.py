"""Compliance summary honesty: unchecked frameworks earn no score."""
from pathlib import Path
import unittest
from app.compliance.checker import compliance_engine

class ComplianceScoreTests(unittest.TestCase):
    def test_unchecked_frameworks_earn_no_score(self):
        scores = compliance_engine.calculate_scores([
            {"framework": "CIS", "status": "PASS"},
            {"framework": "CIS", "status": "FAIL"},
        ])
        self.assertEqual(scores, {"CIS": 50.0})

    def test_empty_checks_yield_empty_scores(self):
        self.assertEqual(compliance_engine.calculate_scores([]), {})

    def test_no_default_hundred_remains(self):
        source = (Path(__file__).parents[1] / 'app/compliance/checker.py').read_text()
        self.assertNotIn('Default baseline score', source)
        self.assertNotIn('= 100.0', source)
        endpoint = (Path(__file__).parents[1] / 'app/api/v1/endpoints/compliance.py').read_text()
        self.assertNotIn('"CIS": 100.0', endpoint)

if __name__ == '__main__':
    unittest.main()
