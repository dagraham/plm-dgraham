from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

_QUARTER_START_MONTHS = {
    1: 1,
    2: 4,
    3: 7,
    4: 10,
}

_QUARTER_LABELS = {
    1: "1st Quarter",
    2: "2nd Quarter",
    3: "3rd Quarter",
    4: "4th Quarter",
}

_YEAR_QUARTER_RE = re.compile(r"^\s*(\d{4})\s*/\s*([1-4])\s*$")
_YEAR_MONTH_RE = re.compile(r"^\s*(\d{4})\s*/\s*(0[1-9]|1[0-2])\s*$")


@dataclass(frozen=True)
class QuarterPeriod:
    year: int
    quarter: int
    begin: date
    end: date
    start_month: int
    end_month: int
    period_label: str

    @property
    def begin_ymd(self) -> str:
        return format_ymd(self.begin)

    @property
    def end_ymd(self) -> str:
        return format_ymd(self.end)


def format_ymd(value: date) -> str:
    return f"{value.year}/{value.month}/{value.day}"


def quarter_label(quarter: int) -> str:
    quarter = int(quarter)
    if quarter not in _QUARTER_LABELS:
        raise ValueError(f"quarter must be 1, 2, 3 or 4; got {quarter}")
    return _QUARTER_LABELS[quarter]


def quarter_month_range(quarter: int) -> tuple[int, int]:
    quarter = int(quarter)
    if quarter not in _QUARTER_START_MONTHS:
        raise ValueError(f"quarter must be 1, 2, 3 or 4; got {quarter}")
    start_month = _QUARTER_START_MONTHS[quarter]
    return start_month, start_month + 2


def derive_quarter_period(year: int, quarter: int) -> QuarterPeriod:
    year = int(year)
    quarter = int(quarter)

    start_month, end_month = quarter_month_range(quarter)
    last_day = calendar.monthrange(year, end_month)[1]

    begin = date(year, start_month, 1)
    end = date(year, end_month, last_day)

    return QuarterPeriod(
        year=year,
        quarter=quarter,
        begin=begin,
        end=end,
        start_month=start_month,
        end_month=end_month,
        period_label=quarter_label(quarter),
    )


def infer_quarter_from_month(month: int) -> int:
    month = int(month)
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12; got {month}")
    return ((month - 1) // 3) + 1


def infer_period_from_year_month(year: int, month: int) -> QuarterPeriod:
    return derive_quarter_period(int(year), infer_quarter_from_month(int(month)))


def parse_year_month(value: str) -> tuple[int, int]:
    match = _YEAR_MONTH_RE.match(str(value))
    if not match:
        raise ValueError(
            "month input must have the form 'yyyy/mm' with a two-digit month in 01..12"
        )
    year, month = match.groups()
    return int(year), int(month)


def parse_year_quarter(value: str) -> tuple[int, int]:
    match = _YEAR_QUARTER_RE.match(str(value))
    if not match:
        raise ValueError("quarter input must have the form 'yyyy/q' with q in 1..4")
    year, quarter = match.groups()
    return int(year), int(quarter)


def infer_period_from_year_quarter(value: str) -> QuarterPeriod:
    year, quarter = parse_year_quarter(value)
    return derive_quarter_period(year, quarter)


def infer_period_from_year_month_text(value: str) -> QuarterPeriod:
    year, month = parse_year_month(value)
    return infer_period_from_year_month(year, month)


def render_title_template(
    template: str,
    *,
    year: int,
    quarter: Optional[int] = None,
    period: Optional[str] = None,
    start_month: Optional[int] = None,
    end_month: Optional[int] = None,
) -> str:
    values = {
        "year": int(year),
        "quarter": quarter,
        "period": period
        if period is not None
        else (quarter_label(quarter) if quarter is not None else ""),
        "start_month": start_month if start_month is not None else "",
        "end_month": end_month if end_month is not None else "",
    }
    return template.format(**values)


def suggest_quarter_project_name(
    year: int,
    quarter: int,
    suffix: str,
) -> str:
    suffix = str(suffix).strip().upper()
    if suffix:
        return f"{int(year)}-{int(quarter)}Q-{suffix}"
    return f"{int(year)}-{int(quarter)}Q"


def weekday_tag_suffix(day: int) -> str:
    day = int(day)
    mapping = {
        0: "MO",
        1: "TU",
        2: "WE",
        3: "TH",
        4: "FR",
        5: "SA",
        6: "SU",
    }
    if day not in mapping:
        raise ValueError(f"day must be between 0 and 6; got {day}")
    return mapping[day]
