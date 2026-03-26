from __future__ import annotations

import calendar
import re
from datetime import date
from typing import Final

_ABSOLUTE_DATE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(\d{4})/((?:0[1-9])|(?:1[0-2]))/((?:0[1-9])|(?:[12]\d)|(?:3[01]))\s*$"
)

_RELATIVE_WEEKDAY_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(-?[1-5])\s*(MO|TU|WE|TH|FR|SA|SU)\s*$",
    re.IGNORECASE,
)

_WEEKDAY_INDEX: Final[dict[str, int]] = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}


def format_ymd(value: date) -> str:
    return value.strftime("%Y/%m/%d")


def parse_absolute_template_date(value: str) -> date:
    """
    Parse an absolute template reply-by date in yyyy/mm/dd format.

    The month and day must both be zero-padded to two digits.

    Examples:
        2026/06/19
        2027/01/05
    """
    match = _ABSOLUTE_DATE_RE.match(str(value))
    if not match:
        raise ValueError(
            "absolute date must have the form 'yyyy/mm/dd' with two-digit month and day"
        )

    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"invalid absolute date '{value}': {exc}") from exc


def parse_relative_weekday_rule(value: str) -> tuple[int, int]:
    """
    Parse a relative weekday rule such as '3FR' or '-1MO'.

    Returns:
        A tuple of (ordinal, weekday_index), where weekday_index uses the
        Python weekday convention Monday=0 ... Sunday=6.
    """
    match = _RELATIVE_WEEKDAY_RE.match(str(value))
    if not match:
        raise ValueError(
            "relative rule must have the form 'nXX' or '-nXX', e.g. '3FR' or '-1MO'"
        )

    ordinal_text, weekday_text = match.groups()
    ordinal = int(ordinal_text)
    weekday = _WEEKDAY_INDEX[weekday_text.upper()]
    return ordinal, weekday


def resolve_nth_weekday(year: int, month: int, ordinal: int, weekday: int) -> date:
    """
    Resolve the nth weekday in a given month.

    Positive ordinals count from the start of the month:
        1 = first, 2 = second, ...
    Negative ordinals count from the end of the month:
        -1 = last, -2 = second last, ...

    Args:
        year: Four-digit year.
        month: Month number 1..12.
        ordinal: Weekday occurrence ordinal.
        weekday: Python weekday index, Monday=0 ... Sunday=6.
    """
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12; got {month}")
    if weekday < 0 or weekday > 6:
        raise ValueError(f"weekday must be between 0 and 6; got {weekday}")
    if ordinal == 0 or ordinal < -5 or ordinal > 5:
        raise ValueError(f"ordinal must be in -5..-1 or 1..5; got {ordinal}")

    month_days = calendar.monthcalendar(year, month)

    if ordinal > 0:
        matches = [week[weekday] for week in month_days if week[weekday] != 0]
        if len(matches) < ordinal:
            raise ValueError(
                f"month {year:04d}/{month:02d} does not have a {ordinal} occurrence of weekday {weekday}"
            )
        day = matches[ordinal - 1]
    else:
        matches = [week[weekday] for week in month_days if week[weekday] != 0]
        if len(matches) < abs(ordinal):
            raise ValueError(
                f"month {year:04d}/{month:02d} does not have a {ordinal} occurrence of weekday {weekday}"
            )
        day = matches[ordinal]

    return date(year, month, day)


def previous_month(year: int, month: int) -> tuple[int, int]:
    """
    Return the (year, month) for the month preceding the given year/month.
    """
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12; got {month}")
    if month == 1:
        return year - 1, 12
    return year, month - 1


def resolve_relative_reply_by(
    value: str, *, anchor_year: int, anchor_month: int
) -> date:
    """
    Resolve a relative reply-by rule against the month preceding anchor_year/anchor_month.

    Example:
        anchor_year=2026, anchor_month=7, value='3FR'
        -> third Friday of June 2026
        -> 2026/06/19
    """
    ordinal, weekday = parse_relative_weekday_rule(value)
    year, month = previous_month(anchor_year, anchor_month)
    return resolve_nth_weekday(year, month, ordinal, weekday)


def parse_template_reply_by(
    value: str,
    *,
    anchor_year: int,
    anchor_month: int,
) -> date:
    """
    Parse a template reply-by value as either:
    - absolute yyyy/mm/dd
    - relative nXX / -nXX rule resolved against the month preceding the anchor month

    Relative examples:
        3FR
        1MO
        -1FR
    """
    text = str(value).strip()
    if not text:
        raise ValueError("reply-by value must not be empty")

    try:
        return parse_absolute_template_date(text)
    except ValueError:
        return resolve_relative_reply_by(
            text,
            anchor_year=anchor_year,
            anchor_month=anchor_month,
        )
