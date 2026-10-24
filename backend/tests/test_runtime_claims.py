"""Keep runtime/demo wording separate from optional model-development code."""
from pathlib import Path
import unittest
ROOT=Path(__file__).parents[2]
class RuntimeClaimTests(unittest.TestCase):
    def test_analytics_copy_does_not_claim_training_or_guaranteed_security(self):
        source=(ROOT/'frontend/src/components/analytics/PredictiveAnalytics.tsx').read_text()
        for phrase in ['fine-tuned transformer model','LOG PAYLOAD SECURE','THREAT DETECTED','Error < 0.15','Error ≥ 0.15']:
            self.assertNotIn(phrase,source)
        self.assertIn('Scanner severity uses CVSS rules',source)
        self.assertIn('Uncalibrated score',source)
    def test_readme_distinguishes_runtime_from_training_scripts(self):
        source=(ROOT/'README.md').read_text()
        self.assertIn('not used for scanner scoring',source)
        self.assertNotIn('predict exact CVSS threat scores',source)
