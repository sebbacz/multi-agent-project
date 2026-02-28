import re
from datetime import date, timedelta
from typing import Optional

# Patterns for relative date extraction
DAYS_OF_WEEK = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

RELATIVE_PATTERNS = [
    (re.compile(r"\b(today|now)\b", re.I), 0),
    (re.compile(r"\btomorrow\b", re.I), 1),
    (re.compile(r"\bnext (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I), None),
    (re.compile(r"\bby (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I), None),
    (re.compile(r"\bin (\d+) days?\b", re.I), None),
    (re.compile(r"\bnext week\b", re.I), 7),
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), None),  # ISO format
]


def resolve_due_date(text: str, reference_date: date) -> Optional[str]:
    """
    Extract due date from text using reference_date as anchor.
    Returns ISO format string or None.
    """
    text_lower = text.lower()

    # check iso
    iso_match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if iso_match:
        try:
            year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return date(year, month, day).isoformat()
        except ValueError:
            pass

    # Today/tomorrow
    if re.search(r"\b(today|now)\b", text_lower):
        return reference_date.isoformat()
    if re.search(r"\btomorrow\b", text_lower):
        return (reference_date + timedelta(days=1)).isoformat()

    # Next week
    if re.search(r"\bnext week\b", text_lower):
        return (reference_date + timedelta(days=7)).isoformat()

    # In N days
    days_match = re.search(r"\bin (\d+) days?\b", text_lower)
    if days_match:
        days = int(days_match.group(1))
        return (reference_date + timedelta(days=days)).isoformat()

    # Day of week (next/by)
    dow_match = re.search(r"\b(next|by) (monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", text_lower)
    if dow_match:
        target_dow = DAYS_OF_WEEK[dow_match.group(2)]
        current_dow = reference_date.weekday()
        days_ahead = (target_dow - current_dow) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (reference_date + timedelta(days=days_ahead)).isoformat()

    return None
