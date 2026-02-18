from datetime import datetime, timedelta, date, timezone

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # type: ignore


def _get_tz(tz_name: str):
    """
    Windows/Python 3.13 da tzdata bo‘lmasa ZoneInfo topilmaydi.
    Shunda UTC+5 fallback (Toshkent vaqti).
    """
    if ZoneInfo is None:
        return timezone(timedelta(hours=5))
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone(timedelta(hours=5))


def today(tz: str) -> date:
    return datetime.now(_get_tz(tz)).date()


def tomorrow(tz: str) -> date:
    return today(tz) + timedelta(days=1)


def ymd(d: date) -> str:
    return d.isoformat()


def ym(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"
