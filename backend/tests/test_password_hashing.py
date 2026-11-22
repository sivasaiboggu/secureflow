"""Pin password hashing behaviour for the full length range the API accepts.

UserCreate allows passwords up to 128 characters. bcrypt silently ignores
everything past 72 bytes, so switching the hash scheme would quietly make
two different long passwords equivalent. These tests keep the current
pbkdf2_sha256 behaviour honest: every character counts, hashes are salted,
and unicode passwords round-trip.
"""
import unittest

from app.core.security import get_password_hash, verify_password


class PasswordHashingTests(unittest.TestCase):
    def test_max_length_password_round_trips(self):
        password = "p" * 128
        self.assertTrue(verify_password(password, get_password_hash(password)))

    def test_characters_past_72_bytes_still_matter(self):
        hashed = get_password_hash("x" * 80 + "A")
        self.assertTrue(verify_password("x" * 80 + "A", hashed))
        self.assertFalse(verify_password("x" * 80 + "B", hashed))

    def test_hashes_are_salted(self):
        self.assertNotEqual(get_password_hash("same-password-1"), get_password_hash("same-password-1"))

    def test_unicode_password_round_trips(self):
        password = "pässwörd-日本語-123456"
        hashed = get_password_hash(password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password(password + "x", hashed))

    def test_hash_is_not_the_plaintext(self):
        self.assertNotIn("secret-password-12", get_password_hash("secret-password-12"))


if __name__ == "__main__":
    unittest.main()
