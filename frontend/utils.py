import os
from datetime import datetime, timedelta, timezone

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
IST = timezone(timedelta(hours=5, minutes=30))


def api_get(path: str, params: dict | None = None) -> dict:
    with httpx.Client(timeout=30) as c:
        r = c.get(f"{BACKEND_URL}{path}", params=params)
        r.raise_for_status()
        return r.json()


def api_post(path: str, json: dict) -> dict:
    with httpx.Client(timeout=120) as c:
        r = c.post(f"{BACKEND_URL}{path}", json=json)
        r.raise_for_status()
        return r.json()


def api_delete(path: str) -> dict:
    with httpx.Client(timeout=30) as c:
        r = c.delete(f"{BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()


def fmt_ist_time(iso_str: str) -> str:
    """UTC ISO → IST 12-hour time, e.g. '02:14 PM'."""
    try:
        clean = iso_str.replace("Z", "").split("+")[0]
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).strftime("%I:%M %p").lstrip("0")
    except Exception:
        return iso_str[11:19] if len(iso_str) >= 19 else iso_str


def fmt_ist_datetime(iso_str: str) -> str:
    """UTC ISO → IST date + 12-hour time, e.g. '20 Apr · 2:14 PM'."""
    try:
        clean = iso_str.replace("Z", "").split("+")[0]
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).strftime("%d %b · %I:%M %p").replace(" 0", " ")
    except Exception:
        return iso_str
