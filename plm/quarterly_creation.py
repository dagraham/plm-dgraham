from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from dateutil.parser import parse
from dateutil.rrule import FR, MO, SA, TH, TU, WE, WEEKLY, rrule

from plm.periods import derive_quarter_period, quarter_label

_WEEKDAY_RRULE = {
    0: MO,
    1: TU,
    2: WE,
    3: TH,
    4: FR,
    5: SA,
}

_WEEKDAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
}

DEFAULT_NUM_COURTS = "0"
DEFAULT_NUM_PLAYERS = "4"
DEFAULT_ASSIGN_TBD = "n"
DEFAULT_ALLOW_LAST = "n"
DEFAULT_CAN = "y"


@dataclass(frozen=True)
class QuarterlyProjectDraft:
    year: int
    quarter: int
    day: int
    name: str
    title: str
    player_tag: str
    reply_by: str
    begin: str
    end: str
    dates: list[str]
    num_courts: str = DEFAULT_NUM_COURTS
    num_players: str = DEFAULT_NUM_PLAYERS
    assign_tbd: str = DEFAULT_ASSIGN_TBD
    allow_last: str = DEFAULT_ALLOW_LAST
    can: str = DEFAULT_CAN

    @property
    def weekday_name(self) -> str:
        return weekday_name(self.day)

    @property
    def weekday_suffix(self) -> str:
        return weekday_suffix(self.day)

    @property
    def years_label(self) -> str:
        return str(self.year)


def weekday_name(day: int) -> str:
    day = int(day)
    if day not in _WEEKDAY_NAMES:
        raise ValueError(f"day must be an integer from 0 to 5; got {day}")
    return _WEEKDAY_NAMES[day]


def weekday_suffix(day: int) -> str:
    return weekday_name(day)[:2].upper()


def player_tag_from_day(day: int) -> str:
    return weekday_name(day)[:3].lower()


def project_name(year: int, quarter: int, day: int) -> str:
    return f"{int(year)}-{int(quarter)}Q-{weekday_suffix(day)}"


def project_title(year: int, quarter: int, day: int) -> str:
    return f"{weekday_name(day)} Tennis {quarter_label(int(quarter))} {int(year)}"


def zero_padded_ymd(value: date) -> str:
    return value.strftime("%Y/%m/%d")


def slash_date(value: date | datetime) -> str:
    return f"{value.month}/{value.day}"


def quarter_weekday_dates(year: int, quarter: int, day: int) -> list[date]:
    period = derive_quarter_period(int(year), int(quarter))
    weekday = int(day)

    if weekday not in _WEEKDAY_RRULE:
        raise ValueError(f"day must be an integer from 0 to 5; got {weekday}")

    begin_dt = parse(f"{period.begin_ymd} 12am")
    end_dt = parse(f"{period.end_ymd} 11:59pm")

    return [
        dt.date()
        for dt in rrule(
            WEEKLY,
            byweekday=_WEEKDAY_RRULE[weekday],
            dtstart=begin_dt,
            until=end_dt,
        )
    ]


def reply_by_from_first_date(first_date: date, days_before: int = 14) -> date:
    return first_date - timedelta(days=int(days_before))


def next_quarter_year_and_quarter(today: date | None = None) -> tuple[int, int]:
    if today is None:
        today = date.today()

    current_quarter = ((today.month - 1) // 3) + 1
    if current_quarter == 4:
        return today.year + 1, 1
    return today.year, current_quarter + 1


def build_quarterly_project_draft(
    year: int, quarter: int, day: int
) -> QuarterlyProjectDraft:
    year = int(year)
    quarter = int(quarter)
    day = int(day)

    dates = quarter_weekday_dates(year, quarter, day)
    if not dates:
        raise ValueError(
            f"no dates were generated for year={year}, quarter={quarter}, day={day}"
        )

    begin = dates[0]
    end = dates[-1]
    reply_by = reply_by_from_first_date(begin)

    return QuarterlyProjectDraft(
        year=year,
        quarter=quarter,
        day=day,
        name=project_name(year, quarter, day),
        title=project_title(year, quarter, day),
        player_tag=player_tag_from_day(day),
        reply_by=zero_padded_ymd(reply_by),
        begin=zero_padded_ymd(begin),
        end=zero_padded_ymd(end),
        dates=[slash_date(d) for d in dates],
    )


def editable_fields_for_review(draft: QuarterlyProjectDraft) -> list[tuple[str, Any]]:
    return [
        ("YEAR", draft.year),
        ("QUARTER", draft.quarter),
        ("NAME", draft.name),
        ("TITLE", draft.title),
        ("PLAYER_TAG", draft.player_tag),
        ("REPLY_BY", draft.reply_by),
        ("CAN", draft.can),
        ("DAY", draft.day),
        ("DATES", draft.dates),
        ("NUM_COURTS", draft.num_courts),
        ("NUM_PLAYERS", draft.num_players),
        ("ASSIGN_TBD", draft.assign_tbd),
        ("ALLOW_LAST", draft.allow_last),
    ]


def draft_to_project_data(draft: QuarterlyProjectDraft) -> dict[str, Any]:
    return {
        "YEAR": draft.year,
        "QUARTER": draft.quarter,
        "NAME": draft.name,
        "TITLE": draft.title,
        "PLAYER_TAG": draft.player_tag,
        "REPLY_BY": draft.reply_by,
        "CAN": draft.can,
        "DAY": draft.day,
        "DATES": list(draft.dates),
        "NUM_COURTS": draft.num_courts,
        "NUM_PLAYERS": draft.num_players,
        "ASSIGN_TBD": draft.assign_tbd,
        "ALLOW_LAST": draft.allow_last,
    }
