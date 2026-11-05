"""Weekly time windows, evaluated in the site's local timezone.

Window format: {"days": [0..6] (Mon=0), "start": "HH:MM", "end": "HH:MM"}.
If end <= start the window runs overnight and the part after midnight belongs to the window
that started on the previous day (e.g. Fri 18:00 -> Sat 06:00 is matched by days=[4]).
An empty window list means "always".
"""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def validate_windows(windows: list) -> list[dict]:
    out = []
    if not isinstance(windows, list) or len(windows) > 28:
        raise ValueError("schedule must be a list of at most 28 windows")
    for w in windows:
        if not isinstance(w, dict):
            raise ValueError("each window must be an object")
        days = w.get("days", list(range(7)))
        if not isinstance(days, list) or not days or any((not isinstance(d, int)) or d < 0 or d > 6 for d in days):
            raise ValueError("days must be a non-empty list of integers 0 (Mon) .. 6 (Sun)")
        start, end = str(w.get("start", "")), str(w.get("end", ""))
        if not _HHMM.match(start) or not _HHMM.match(end):
            raise ValueError("start/end must be HH:MM (24h)")
        if start == end:
            raise ValueError("start and end must differ (use an empty schedule for 'always')")
        out.append({"days": sorted(set(days)), "start": start, "end": end})
    return out


def validate_timezone(tz: str) -> str:
    try:
        ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"unknown timezone: {tz}") from exc
    return tz


def _t(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def in_window(local: datetime, w: dict) -> bool:
    start, end = _t(w["start"]), _t(w["end"])
    now_t = local.time()
    days = w["days"]
    if start < end:
        return local.weekday() in days and start <= now_t < end
    # overnight
    if now_t >= start and local.weekday() in days:
        return True
    prev_day = (local - timedelta(days=1)).weekday()
    return now_t < end and prev_day in days


def matches(windows: list[dict] | None, when_utc: datetime, tz: str) -> bool:
    if not windows:
        return True
    local = when_utc.astimezone(ZoneInfo(tz))
    return any(in_window(local, w) for w in windows)
