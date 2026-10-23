"""Configuration-only tests: no database, cloud credentials or model downloads."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

class ProductionSettingsTests(unittest.TestCase):
    def check_settings(self, debug, key=None):
        env = dict(os.environ, DEBUG=str(debug).lower())
        env.pop("SECRET_KEY", None)
        if key is not None:
            env["SECRET_KEY"] = key
        return subprocess.run(
            [sys.executable, "-c", "from app.config.settings import Settings; Settings(_env_file=None)"],
            cwd=BACKEND, env=env, capture_output=True, text=True,
        )

    def test_debug_preserves_local_demo_defaults(self):
        self.assertEqual(self.check_settings(True).returncode, 0)

    def test_production_rejects_default_key(self):
        result = self.check_settings(False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("When DEBUG=False", result.stderr)

    def test_production_rejects_short_and_blank_keys(self):
        for key in ["short", " " * 32]:
            with self.subTest(key_length=len(key)):
                self.assertNotEqual(self.check_settings(False, key).returncode, 0)

    def test_production_accepts_long_custom_key(self):
        self.assertEqual(self.check_settings(False, "local-test-key-not-for-deployment-0123456789").returncode, 0)

if __name__ == "__main__":
    unittest.main()
