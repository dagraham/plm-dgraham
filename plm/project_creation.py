from __future__ import annotations

import os
import sys
from typing import Any

from dateutil.parser import parse
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyWordCompleter

from plm.project_io import list_project_files, load_project, yaml
from plm.quarterly_creation import (
    QuarterlyProjectDraft,
    build_quarterly_project_draft,
    draft_to_project_data,
    editable_fields_for_review,
    next_quarter_year_and_quarter,
)
from plm.utils import rel_path, wrap_text


def create_project(
    *,
    plm_roster: str,
    plm_projects: str,
    clear_screen,
    get_date,
    get_dates,
) -> str | None:
    return create_project_manual(
        plm_roster=plm_roster,
        plm_projects=plm_projects,
        clear_screen=clear_screen,
        get_date=get_date,
        get_dates=get_dates,
    )


def modify_project(
    *,
    plm_roster: str,
    plm_projects: str,
    clear_screen,
) -> str | None:
    clear_screen()
    session = PromptSession()
    _validate_project_environment(plm_roster, plm_projects)

    roster_data = _load_roster_data(plm_roster)
    players, addresses = _extract_roster_maps(roster_data)

    project_file = _prompt_for_existing_project_file(
        session=session,
        plm_projects=plm_projects,
    )
    if not project_file:
        print("cancelled")
        return None

    project_data = load_project(project_file)
    data = _project_data_for_review(project_data)

    selected_tag = data["PLAYER_TAG"]
    if selected_tag not in players:
        print(
            f"warning: player tag '{selected_tag}' was not found in {rel_path(plm_roster)}"
        )
        available = ", ".join(sorted(players.keys()))
        print(f"available player tags: {available}")
        selected_tag = _prompt_for_existing_player_tag(
            session=session,
            players=players,
            default_tag=selected_tag,
        )
        data["PLAYER_TAG"] = selected_tag

    review_result = _review_generated_project(
        session=session,
        data=data,
        players=players,
    )
    if review_result is None:
        print("cancelled")
        return None

    data = review_result
    _write_project_file(
        session=session,
        project_file=project_file,
        project_data=data,
        plm_roster=plm_roster,
        players=players,
        addresses=addresses,
    )
    return project_file


def create_project_manual(
    *,
    plm_roster: str,
    plm_projects: str,
    clear_screen,
    get_date,
    get_dates,
) -> str | None:
    clear_screen()
    session = PromptSession()
    _validate_project_environment(plm_roster, plm_projects)

    roster_data = _load_roster_data(plm_roster)
    players, addresses = _extract_roster_maps(roster_data)

    print(
        wrap_text(
            f"""\
Create a new quarterly doubles project by entering:
1) the year
2) the quarter
3) the integer weekday

The project name, title, player tag, reply-by date, begin/end dates and
weekly playing dates will be generated automatically. The reply-by date is
set to 14 days before the first generated playing date.

Projects are stored in:
    {rel_path(plm_projects)}
"""
        )
    )

    default_year, default_quarter = next_quarter_year_and_quarter()

    year = _prompt_for_year(session, default_year)
    quarter = _prompt_for_quarter(session, default_quarter)
    day = _prompt_for_day(session)

    draft = build_quarterly_project_draft(year, quarter, day)
    data = draft_to_project_data(draft)

    selected_tag = data["PLAYER_TAG"]
    if selected_tag not in players:
        print(
            f"warning: derived player tag '{selected_tag}' was not found in {rel_path(plm_roster)}"
        )
        available = ", ".join(sorted(players.keys()))
        print(f"available player tags: {available}")
        selected_tag = _prompt_for_existing_player_tag(
            session=session,
            players=players,
            default_tag=selected_tag,
        )
        data["PLAYER_TAG"] = selected_tag

    data["YEAR"] = year
    data["QUARTER"] = quarter

    review_result = _review_generated_project(
        session=session,
        data=data,
        players=players,
    )
    if review_result is None:
        print("cancelled")
        return None

    data = review_result
    project_file = os.path.join(plm_projects, f"{data['NAME']}.yaml")
    _write_project_file(
        session=session,
        project_file=project_file,
        project_data=data,
        plm_roster=plm_roster,
        players=players,
        addresses=addresses,
    )
    return project_file


def create_project_from_template(
    *,
    plm_roster: str,
    plm_projects: str,
    clear_screen,
    get_date,
    get_dates,
) -> str | None:
    print(
        wrap_text(
            """\
Template-based project creation has been retired. Use command 'c' for the streamlined quarterly doubles workflow.\
"""
        )
    )
    return None


def _validate_project_environment(plm_roster: str, plm_projects: str) -> None:
    problems = []
    if not os.path.exists(plm_roster):
        problems.append(f"Could not find {plm_roster}")
    if not os.path.exists(plm_projects) or not os.path.isdir(plm_projects):
        problems.append(
            f"Either {plm_projects} does not exist or it is not a directory"
        )
    if problems:
        print(f"problems: {problems}")
        sys.exit(problems)


def _load_roster_data(plm_roster: str) -> dict[str, Any]:
    with open(plm_roster, "r", encoding="utf-8") as stream:
        return yaml.load(stream) or {}


def _extract_roster_maps(
    roster_data: dict[str, Any],
) -> tuple[dict[str, list[str]], dict[str, str]]:
    players: dict[str, list[str]] = {}
    addresses: dict[str, str] = {}

    for player, values in roster_data.items():
        addresses[player] = values[0]
        for tag in values[1:]:
            players.setdefault(tag, []).append(player)

    return players, addresses


def _prompt_for_existing_project_file(
    *,
    session: PromptSession,
    plm_projects: str,
) -> str | None:
    print("Select the project to modify.")
    possible = list_project_files(plm_projects)
    completer = FuzzyWordCompleter(possible)
    proj = session.prompt("project: ", completer=completer, default="").strip()
    if not proj:
        return None
    proj = proj if proj.endswith(".yaml") else proj + ".yaml"
    project_file = os.path.join(plm_projects, proj)
    if not os.path.isfile(project_file):
        print(f"project '{project_file}' not found")
        return None
    return project_file


def _project_data_for_review(project_data: dict[str, Any]) -> dict[str, Any]:
    data = dict(project_data)
    data.setdefault(
        "YEAR", _year_from_dates(data.get("DATES", []), data.get("REPLY_BY", ""))
    )
    data.setdefault(
        "QUARTER", _quarter_from_dates(data.get("DATES", []), data.get("NAME", ""))
    )
    data.setdefault("CAN", "y")
    data.setdefault("NUM_COURTS", "0")
    data.setdefault("NUM_PLAYERS", "4")
    data.setdefault("ASSIGN_TBD", "n")
    data.setdefault("ALLOW_LAST", "n")
    return data


def _year_from_dates(dates: list[str], reply_by: str) -> int:
    if dates:
        try:
            reply_dt = parse(reply_by, yearfirst=True)
            first_month = int(str(dates[0]).split("/")[0])
            year = reply_dt.year + 1 if first_month < reply_dt.month else reply_dt.year
            return year
        except Exception:
            pass
    try:
        return parse(reply_by, yearfirst=True).year
    except Exception:
        return datetime.now().year


def _quarter_from_dates(dates: list[str], name: str) -> int:
    if dates:
        try:
            first_month = int(str(dates[0]).split("/")[0])
            return ((first_month - 1) // 3) + 1
        except Exception:
            pass
    try:
        middle = str(name).split("-")[1]
        return int(middle[0])
    except Exception:
        return 1


def _prompt_for_year(session: PromptSession, default_year: int) -> int:
    while True:
        value = session.prompt("year: ", default=str(default_year)).strip()
        if not value:
            value = str(default_year)
        if len(value) == 4 and value.isdigit():
            return int(value)
        print("enter a four-digit year, e.g. 2026")


def _prompt_for_quarter(session: PromptSession, default_quarter: int) -> int:
    while True:
        value = session.prompt("quarter: ", default=str(default_quarter)).strip()
        if not value:
            value = str(default_quarter)
        if value in {"1", "2", "3", "4"}:
            return int(value)
        print("enter a quarter using 1, 2, 3 or 4")


def _prompt_for_day(session: PromptSession, default_day: int = 1) -> int:
    while True:
        value = session.prompt(
            "weekday integer (0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat): ",
            default=str(default_day),
        ).strip()
        if not value:
            value = str(default_day)
        if value in {"0", "1", "2", "3", "4", "5"}:
            return int(value)
        print("enter a weekday integer from 0 to 5")


def _prompt_for_existing_player_tag(
    *,
    session: PromptSession,
    players: dict[str, list[str]],
    default_tag: str,
) -> str:
    tags = sorted(players.keys())
    completer = FuzzyWordCompleter(tags)
    while True:
        tag = session.prompt(
            "player tag: ",
            completer=completer,
            complete_while_typing=True,
            default=str(default_tag),
        ).strip()
        if tag in players:
            return tag
        print(f"'{tag}' is not one of: {', '.join(tags)}")


def _review_generated_project(
    *,
    session: PromptSession,
    data: dict[str, Any],
    players: dict[str, list[str]],
) -> dict[str, Any] | None:
    while True:
        _print_project_review(data, players)

        action = (
            session.prompt(
                "Enter a line number to modify, 's' to save, or 'q' to cancel: ",
                default="s",
            )
            .strip()
            .lower()
        )

        if action == "s":
            return data
        if action == "q":
            return None
        if not action.isdigit():
            print("enter a line number, 's' or 'q'")
            continue

        line_number = int(action)
        if line_number not in _reviewable_field_map():
            print(f"{line_number} is not an editable line number")
            continue

        key = _reviewable_field_map()[line_number]
        updated = _edit_review_field(
            session=session,
            key=key,
            current=data[key],
            data=data,
            players=players,
        )
        if updated is not None:
            data[key] = updated


def _print_project_review(data: dict[str, Any], players: dict[str, list[str]]) -> None:
    fields = [
        (1, "YEAR", data["YEAR"]),
        (2, "QUARTER", data["QUARTER"]),
        (3, "DAY", data["DAY"]),
        (4, "NAME", data["NAME"]),
        (5, "TITLE", data["TITLE"]),
        (6, "PLAYER_TAG", data["PLAYER_TAG"]),
        (7, "REPLY_BY", data["REPLY_BY"]),
        (8, "CAN", data["CAN"]),
        (9, "NUM_COURTS", data["NUM_COURTS"]),
        (10, "NUM_PLAYERS", data["NUM_PLAYERS"]),
        (11, "ASSIGN_TBD", data["ASSIGN_TBD"]),
        (12, "ALLOW_LAST", data["ALLOW_LAST"]),
    ]

    print("")
    print("Generated project settings")
    print("==========================")
    for line_no, key, value in fields:
        print(f"{line_no:>2}  {key}: {value}")

    print("")
    print(f"DATES: {', '.join(data['DATES'])}")

    tag = data["PLAYER_TAG"]
    if tag in players:
        print("")
        print(f"Players with tag '{tag}':")
        for player in players[tag]:
            print(f"    {player}")
    else:
        print("")
        print(f"Players with tag '{tag}': none found")


def _reviewable_field_map() -> dict[int, str]:
    return {
        1: "YEAR",
        2: "QUARTER",
        3: "DAY",
        4: "NAME",
        5: "TITLE",
        6: "PLAYER_TAG",
        7: "REPLY_BY",
        8: "CAN",
        9: "NUM_COURTS",
        10: "NUM_PLAYERS",
        11: "ASSIGN_TBD",
        12: "ALLOW_LAST",
    }


def _edit_review_field(
    *,
    session: PromptSession,
    key: str,
    current: Any,
    data: dict[str, Any],
    players: dict[str, list[str]],
) -> Any | None:
    if key == "YEAR":
        new_year = _prompt_for_year(session, int(current))
        _regenerate_derived_fields(data, year=new_year)
        return new_year
    if key == "QUARTER":
        new_quarter = _prompt_for_quarter(session, int(current))
        _regenerate_derived_fields(data, quarter=new_quarter)
        return new_quarter
    if key == "DAY":
        new_day = _prompt_for_day(session, int(current))
        _regenerate_derived_fields(data, day=new_day)
        return new_day
    if key == "NAME":
        return _prompt_name(session, str(current))
    if key == "TITLE":
        return _prompt_nonempty_text(session, "TITLE", str(current))
    if key == "PLAYER_TAG":
        return _prompt_for_existing_player_tag(
            session=session,
            players=players,
            default_tag=str(current),
        )
    if key == "REPLY_BY":
        return _prompt_reply_by(session, str(current))
    if key == "CAN":
        return _prompt_yes_no(session, "CAN", str(current))
    if key == "NUM_COURTS":
        return _prompt_nonnegative_int_text(session, "NUM_COURTS", str(current))
    if key == "NUM_PLAYERS":
        return _prompt_num_players(session, str(current))
    if key == "ASSIGN_TBD":
        return _prompt_yes_no(session, "ASSIGN_TBD", str(current))
    if key == "ALLOW_LAST":
        return _prompt_yes_no(session, "ALLOW_LAST", str(current))
    return None


def _prompt_name(session: PromptSession, default_value: str) -> str:
    while True:
        value = session.prompt("NAME: ", default=default_value).strip()
        if value:
            return value
        print("NAME must not be empty")


def _prompt_nonempty_text(
    session: PromptSession, label: str, default_value: str
) -> str:
    while True:
        value = session.prompt(f"{label}: ", default=default_value).strip()
        if value:
            return value
        print(f"{label} must not be empty")


def _prompt_reply_by(session: PromptSession, default_value: str) -> str:
    while True:
        value = session.prompt("REPLY_BY (yyyy/mm/dd): ", default=default_value).strip()
        try:
            dt = parse(value, yearfirst=True)
            return dt.strftime("%Y/%m/%d")
        except Exception as exc:
            print(f"invalid reply-by date '{value}': {exc}")


def _prompt_yes_no(session: PromptSession, label: str, default_value: str) -> str:
    while True:
        value = (
            session.prompt(f"{label} [y/n]: ", default=default_value).strip().lower()
        )
        if value in {"y", "n"}:
            return value
        print(f"{label} must be 'y' or 'n'")


def _prompt_nonnegative_int_text(
    session: PromptSession, label: str, default_value: str
) -> str:
    while True:
        value = session.prompt(f"{label}: ", default=default_value).strip()
        if value.isdigit():
            return value
        print(f"{label} must be a non-negative integer")


def _prompt_num_players(session: PromptSession, default_value: str) -> str:
    while True:
        value = session.prompt("NUM_PLAYERS (4): ", default=default_value).strip()
        if value == "4":
            return value
        print("NUM_PLAYERS is fixed at 4 for quarterly doubles projects")


def _regenerate_derived_fields(
    data: dict[str, Any],
    *,
    year: int | None = None,
    quarter: int | None = None,
    day: int | None = None,
) -> None:
    regenerated = build_quarterly_project_draft(
        year if year is not None else int(data["YEAR"]),
        quarter if quarter is not None else int(data["QUARTER"]),
        day if day is not None else int(data["DAY"]),
    )
    data["YEAR"] = regenerated.year
    data["QUARTER"] = regenerated.quarter
    data["DAY"] = regenerated.day
    data["NAME"] = regenerated.name
    data["TITLE"] = regenerated.title
    data["PLAYER_TAG"] = regenerated.player_tag
    data["REPLY_BY"] = regenerated.reply_by
    data["DATES"] = regenerated.dates


def _render_project_yaml(
    *,
    project_data: dict[str, Any],
    plm_roster: str,
    players: dict[str, list[str]],
    addresses: dict[str, str],
) -> str:
    title = project_data["TITLE"]
    tag = project_data["PLAYER_TAG"]
    reply = project_data["REPLY_BY"]
    can_play = project_data["CAN"]
    year = project_data["YEAR"]
    quarter = project_data["QUARTER"]
    day = project_data["DAY"]
    dates_list = project_data["DATES"]
    dates = ", ".join(dates_list)
    numcourts = project_data["NUM_COURTS"]
    numplayers = project_data["NUM_PLAYERS"]
    assign_tbd = project_data["ASSIGN_TBD"]
    allow_lastresort = project_data["ALLOW_LAST"]

    rep_dt = parse(f"{reply} 6pm")
    rep_date = rep_dt.strftime("%-I%p on %a, %b %-d")

    begin = parse(f"{year}/{dates_list[0]} 12am", yearfirst=True).strftime("%Y/%m/%d")
    end = parse(f"{year}/{dates_list[-1]} 12am", yearfirst=True).strftime("%Y/%m/%d")
    begin_dt = parse(f"{begin} 12am")
    end_dt = parse(f"{end} 12am")
    years = (
        str(begin_dt.year)
        if begin_dt.year == end_dt.year
        else f"{begin_dt.year} - {end_dt.year}"
    )

    eg_day = parse(f"{begin} 12am")
    eg_yes = eg_day.strftime("%-m/%-d")
    eg_no = eg_day.strftime("%b %-d")

    CAN = "CAN" if can_play == "y" else "CANNOT"
    ALL = "all" if can_play == "y" else "any"
    AND = "and also" if can_play == "y" else "but"

    lastresort_text = (
        """
    Alternatively, if you want to be listed as a player of last resort
    for any of these dates, then append an "~" to the relevant dates. As
    a player of last resort, you would only be selected if only one
    player is needed to schedule a court on the given date and, by
    playing, you make it possible for the court to be scheduled. A
    player of last resort will not be selected as captain.
    """
        if allow_lastresort == "y"
        else ""
    )

    lastresort_short = (
        """
        last: you want to be listed as a 'last resort' on all of the dates -
              equivalent to a list of all of the dates and an '~' appended to
              each date
"""
        if allow_lastresort == "y"
        else ""
    )

    tmpl = f"""# created by plm - Player Lineup Manager
TITLE: {title}
PLAYER_TAG: {tag}
REPLY_BY: {reply}
CAN: {can_play}
YEAR: {year}
QUARTER: {quarter}
REPEAT: y
DAY: {day}
DATES: [{dates}]
NUM_COURTS: {numcourts}
NUM_PLAYERS: {numplayers}
ASSIGN_TBD: {assign_tbd}
ALLOW_LAST: {allow_lastresort}

REQUEST: |
    It's time to set the schedule for these dates in {years}:

        {dates}

    Please make a note on your calendars to email me the DATES YOU
    {CAN} PLAY from this list no later than {rep_date}.
    Timely replies are greatly appreciated.

    It would help me to copy and paste from your email if you would
    list your dates on one line, separated by commas in the same format
    as the list above. E.g., using {eg_yes}, not {eg_no}.

    If you want to be listed as a possible substitute for any of these
    dates, then append an "*" to the relevant dates. If, for example,
    you {CAN.lower()} play on {dates_list[0]} and {dates_list[3]} {AND} want to be listed as a possible
    substitute on {dates_list[2]}, then your response should be

        {dates_list[0]}, {dates_list[2]}*, {dates_list[3]}
    {lastresort_text}
    Short responses:

        none: there are no dates on which you {CAN} play - equivalent to a
              list without any dates

        all:  you {CAN} play on {ALL} of the dates - equivalent to a
              list with all of the dates

        sub:  you want to be listed as a possible substitute on all of the
              dates - equivalent to a list of all of the dates with an '*'
              appended to each date
        {lastresort_short}
    Thanks,

NAG: |
    You are receiving this letter because I have not yet received a list of
    the dates you {CAN} play from:

        {dates}

    Please remember that your list is due no later than {rep_date}.

    ___
    From my original request ...

    It would help me to copy and paste from your email if you would
    list your dates on one line, separated by commas in the same format
    as the list above. E.g., using {eg_yes}, not {eg_no}.

    If you want to be listed as a possible substitute for any of these
    dates, then append asterisks to the relevant dates. If, for example,
    you {CAN.lower()} play on {dates_list[0]} and {dates_list[3]} {AND} want to be listed as a possible
    substitute on {dates_list[2]}, then your response should be

        {dates_list[0]}, {dates_list[2]}*, {dates_list[3]}
    {lastresort_text}
    Short responses:

        none: there are no dates on which you {CAN} play - equivalent to a
              list without any dates

        all:  you CAN play on all of the dates - equivalent to a
              list with all of the dates

        sub:  you want to be listed as a possible substitute on all of the
              dates - equivalent to a list of all of the dates with
              asterisks appended to each date
        {lastresort_short}
    Thanks,

SCHEDULE: |
    Not yet processed

# The entries in ADDRESSES and the names in RESPONSES below
# correspond to those from the file '{plm_roster}' that
# were tagged '{tag}'.
"""
    return tmpl


def _write_project_file(
    *,
    session: PromptSession,
    project_file: str,
    project_data: dict[str, Any],
    plm_roster: str,
    players: dict[str, list[str]],
    addresses: dict[str, str],
) -> None:
    tag = project_data["PLAYER_TAG"]
    responses = {}
    yaml_text = _render_project_yaml(
        project_data=project_data,
        plm_roster=plm_roster,
        players=players,
        addresses=addresses,
    )

    response_rows = []
    email_rows = []

    for player in players.get(tag, []):
        response = responses[player] if player in responses else "nr"
        response_rows.append(f"{player}: {response}\n")
        email_rows.append(f"{player}: {addresses[player]}\n")

    if (
        not os.path.exists(project_file)
        or session.prompt(
            f"{rel_path(project_file)} exists. Overwrite: ",
            default="yes",
        ).lower()
        == "yes"
    ):
        with open(project_file, "w", encoding="utf-8") as fo:
            fo.write(yaml_text)
            fo.write("\nADDRESSES:\n")
            for row in email_rows:
                fo.write(f"    {row}")
            fo.write("\nRESPONSES:\n")
            for row in response_rows:
                fo.write(f"    {row}")
        print(f"Saved {project_file}")
    else:
        print("Overwrite cancelled")
