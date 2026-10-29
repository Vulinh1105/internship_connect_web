from datetime import datetime, timezone


def utcnow() -> datetime:
    """Giờ UTC dạng naive (không kèm múi giờ) để lưu vào DB."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
