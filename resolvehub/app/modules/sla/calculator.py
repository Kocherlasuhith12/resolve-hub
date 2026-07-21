from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_timezone(value: str) -> None:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError:
        raise ValueError("Unknown IANA timezone") from None


def _parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError:
        raise ValueError("Business hour times must use HH:MM format") from None


def validate_weekly_hours(hours: dict[str, list[list[str]]]) -> None:
    if not hours:
        raise ValueError("At least one working interval is required")
    for weekday, intervals in hours.items():
        if weekday not in {str(day) for day in range(7)}:
            raise ValueError("Weekday keys must be 0 (Monday) through 6 (Sunday)")
        previous_end: time | None = None
        for interval in intervals:
            if len(interval) != 2:
                raise ValueError("Each working interval must contain a start and end")
            start, end = (_parse_time(item) for item in interval)
            if start >= end or (previous_end is not None and start < previous_end):
                raise ValueError("Working intervals must be ordered, non-overlapping ranges")
            previous_end = end


def add_business_minutes(
    start: datetime,
    minutes: int,
    *,
    timezone: str,
    weekly_hours: dict[str, list[list[str]]],
    holidays: set[date] | None = None,
) -> datetime:
    """Add working minutes and return an aware UTC deadline."""
    if start.tzinfo is None:
        raise ValueError("Start must be timezone-aware")
    if minutes <= 0:
        raise ValueError("Minutes must be positive")
    validate_timezone(timezone)
    validate_weekly_hours(weekly_hours)
    zone = ZoneInfo(timezone)
    current = start.astimezone(zone)
    remaining = timedelta(minutes=minutes)
    holiday_dates = holidays or set()
    for _ in range(3660):
        day = current.date()
        if day not in holiday_dates:
            for raw_start, raw_end in weekly_hours.get(str(current.weekday()), []):
                interval_start = datetime.combine(day, _parse_time(raw_start), zone)
                interval_end = datetime.combine(day, _parse_time(raw_end), zone)
                effective_start = max(current, interval_start)
                if effective_start >= interval_end:
                    continue
                available = interval_end - effective_start
                if remaining <= available:
                    return (effective_start + remaining).astimezone(UTC)
                remaining -= available
        current = datetime.combine(day + timedelta(days=1), time.min, zone)
    raise ValueError("No business deadline found within ten years")
