"""Timezone helpers.

All ``DateTime`` columns in this codebase are timezone-naive, and stored
timestamps are UTC by convention. ``datetime.utcnow()`` is deprecated (and
removed in a future Python version), so every call site goes through these
helpers instead:

* :func:`utcnow` — naive UTC ``datetime``, for database columns, JWT
  ``exp`` claims and anything compared against a stored timestamp.
  Deliberately naive: SQLAlchemy ``DateTime`` columns here are
  timezone-naive, and binding a timezone-aware value to them fails.
* :func:`utcnow_iso` — timezone-aware ISO 8601 string (``+00:00``
  suffix), for log lines, API payloads and scanner finding metadata.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (database-column safe)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utcnow_iso() -> str:
    """Current UTC time as an aware ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
