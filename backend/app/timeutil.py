from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC timestamp.

    datetime.utcnow() is deprecated and scheduled for removal, but storing
    tz-aware values behaves differently between SQLite and Postgres and invites
    naive/aware comparison errors. Every timestamp here is UTC by construction,
    so the tzinfo is dropped deliberately and consistently.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
