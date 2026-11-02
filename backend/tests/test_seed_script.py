"""Seed script guards: no default password, no silent destructive reset."""
import importlib.util
from pathlib import Path
import unittest


def load_seed_module():
    path = Path(__file__).parents[2] / 'scripts' / 'seed_database.py'
    spec = importlib.util.spec_from_file_location('seed_database_script', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SeedPasswordGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_seed_module()

    def test_missing_password_refused(self):
        with self.assertRaises(self.mod.SeedConfigError):
            self.mod.resolve_admin_password({})

    def test_old_published_default_refused(self):
        with self.assertRaises(self.mod.SeedConfigError):
            self.mod.resolve_admin_password({'SEED_ADMIN_PASSWORD': 'password123'})

    def test_short_password_refused(self):
        with self.assertRaises(self.mod.SeedConfigError):
            self.mod.resolve_admin_password({'SEED_ADMIN_PASSWORD': 'x1y2z3'})

    def test_operator_password_accepted(self):
        pw = self.mod.resolve_admin_password({'SEED_ADMIN_PASSWORD': 'a-strong-operator-choice'})
        self.assertEqual(pw, 'a-strong-operator-choice')


class SeedResetGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_seed_module()

    def test_no_flag_is_non_destructive(self):
        args = self.mod.parse_args([])
        self.assertFalse(self.mod.confirm_reset(args, {}))

    def test_reset_flag_alone_refused(self):
        args = self.mod.parse_args(['--reset'])
        with self.assertRaises(self.mod.SeedConfigError):
            self.mod.confirm_reset(args, {})

    def test_reset_env_alone_is_non_destructive(self):
        args = self.mod.parse_args([])
        self.assertFalse(self.mod.confirm_reset(args, {'SEED_RESET_CONFIRM': 'DELETE_ALL_DATA'}))

    def test_reset_requires_flag_and_env(self):
        args = self.mod.parse_args(['--reset'])
        self.assertTrue(self.mod.confirm_reset(args, {'SEED_RESET_CONFIRM': 'DELETE_ALL_DATA'}))


if __name__ == '__main__':
    unittest.main()
