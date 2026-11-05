from datetime import datetime, timezone

import pytest

from app.services import schedules
from app.services.rule_engine import cap_severity


def utc(s):
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def test_overnight_window_sydney():
    w = schedules.validate_windows([{"days": [0, 1, 2, 3, 4], "start": "18:00", "end": "06:00"}])
    tz = "Australia/Sydney"
    assert schedules.matches(w, utc("2026-11-03T19:30:00+11:00"), tz)  # Tue evening
    assert schedules.matches(w, utc("2026-11-04T05:59:00+11:00"), tz)  # Wed early (started Tue)
    assert not schedules.matches(w, utc("2026-11-04T09:00:00+11:00"), tz)
    assert schedules.matches(w, utc("2026-11-08T02:00:00+11:00"), tz) is False  # Sun 2am: Sat not in days
    assert schedules.matches(w, utc("2026-11-07T02:00:00+11:00"), tz)  # Sat 2am belongs to Fri window


def test_empty_schedule_means_always():
    assert schedules.matches([], datetime.now(timezone.utc), "UTC")


@pytest.mark.parametrize("bad", [[{"days": [7], "start": "01:00", "end": "02:00"}],
                                 [{"days": [1], "start": "25:00", "end": "02:00"}],
                                 [{"days": [1], "start": "02:00", "end": "02:00"}]])
def test_invalid_windows(bad):
    with pytest.raises(ValueError):
        schedules.validate_windows(bad)


def test_face_covering_severity_capped():
    assert cap_severity("face_covering_observed", "critical_review") == "informational"
    assert cap_severity("weapon_possible", "critical_review") == "critical_review"
