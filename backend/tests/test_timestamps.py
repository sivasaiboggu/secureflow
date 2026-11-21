"""Pin the timestamp helper contracts the rest of the backend relies on.

app/utils/timestamps.py documents a deliberate split: ``utcnow`` returns a
*naive* UTC datetime because every SQLAlchemy ``DateTime`` column and the
JWT ``exp`` claim here expect naive UTC (binding an aware value to those
columns fails), while ``utcnow_iso`` returns an *aware* ISO 8601 string for
logs and scanner metadata. These tests fail if either side of that contract
drifts — for example if someone "fixes" utcnow to return an aware datetime
and breaks database writes at runtime instead of at test time.
"""

import unittest
from datetime import datetime, timezone, timedelta

from app.utils.timestamps import utcnow, utcnow_iso


class UtcnowContractTests(unittest.TestCase):
    def test_utcnow_is_naive(self):
        # SQLAlchemy DateTime columns here are timezone-naive; an aware
        # value must never reach them.
        self.assertIsNone(utcnow().tzinfo)

    def test_utcnow_tracks_real_utc(self):
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        value = utcnow()
        after = datetime.now(timezone.utc).replace(tzinfo=None)
        self.assertLessEqual(before, value)
        self.assertLessEqual(value, after)

    def test_utcnow_is_not_local_time(self):
        # Only meaningful off-UTC, but cheap everywhere: a naive local
        # timestamp would drift from real UTC by the local offset.
        value = utcnow()
        real_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        self.assertLess(abs((value - real_utc).total_seconds()), 5)

    def test_utcnow_jwt_exp_arithmetic_stays_naive(self):
        # core/security.py builds exp as utcnow() + timedelta; the result
        # must remain naive for jose to encode it as the intended epoch.
        exp = utcnow() + timedelta(minutes=30)
        self.assertIsNone(exp.tzinfo)
        expected_epoch = (exp - datetime(1970, 1, 1)).total_seconds()
        self.assertGreater(expected_epoch, 0)


class UtcnowIsoContractTests(unittest.TestCase):
    def test_iso_string_carries_utc_offset(self):
        self.assertTrue(utcnow_iso().endswith('+00:00'))

    def test_iso_string_round_trips_to_aware_datetime(self):
        parsed = datetime.fromisoformat(utcnow_iso())
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset(), timedelta(0))

    def test_iso_string_tracks_real_utc(self):
        before = datetime.now(timezone.utc)
        parsed = datetime.fromisoformat(utcnow_iso())
        after = datetime.now(timezone.utc)
        self.assertLessEqual(before, parsed)
        self.assertLessEqual(parsed, after)


if __name__ == '__main__':
    unittest.main()
