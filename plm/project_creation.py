from __future__ import annotations

import os
import sys
from typing import Any

from dateutil.parser import parse
from dateutil.rrule import FR, MO, SA, TH, TU, WE, WEEKLY, rrule
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import FuzzyWordCompleter

from plm.periods import (
    infer_period_from_year_month,
    infer_period_from_year_quarter,
    render_title_template,
    suggest_quarter_project_name,
    weekday_tag_suffix,
)
from plm.project_io import list_project_files, load_project, yaml
from plm.relative_dates import format_ymd, parse_template_reply_by
from plm.templates import (
    has_template,
    list_template_names,
    template_defaults,
    template_description,
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
    player_tags = list(players.keys())
    tag_completer = FuzzyWordCompleter(player_tags)

    project_state = _initialize_project_state(
        session=session,
        plm_projects=plm_projects,
        template_selected=False,
    )

    if project_state["existing"]:
        defaults = _load_existing_project_defaults(
            session=session,
            project_file=project_state["project_file"],
        )
        if defaults is None:
            return project_state["project_file"]
    else:
        defaults = _new_project_defaults()
        project_state = _ensure_manual_project_name(
            session=session,
            plm_projects=plm_projects,
            project_state=project_state,
        )

    title = _prompt_for_title(session, defaults["TITLE"])
    tag = _prompt_for_player_tag(
        session=session,
        plm_roster=plm_roster,
        players=players,
        player_tags=player_tags,
        tag_completer=tag_completer,
        default_tag=defaults["TAG"],
    )
    _show_selected_players(players, tag)

    reply, rep_dt = _prompt_for_reply_by_date(
        get_date=get_date,
        default_reply_by=defaults["REPLY_BY"],
    )
    if reply is None:
        return None

    can_play = _prompt_for_can_play(session, defaults["CAN"])

    repeat_result = _prompt_for_repeat_schedule(
        session=session,
        get_date=get_date,
        get_dates=get_dates,
        repeat_default=defaults["REPEAT"],
        day_default=defaults["DAY"],
        begin_default=defaults["BEGIN"],
        end_default=defaults["END"],
        dates_default=defaults["DATES"],
        reply_dt=rep_dt,
    )
    if repeat_result.get("cancelled"):
        return None

    repeat = repeat_result["repeat"]
    day = repeat_result["day"]
    days = repeat_result["days"]

    schedule_meta = _build_schedule_metadata(days)
    _warn_about_unusual_schedule(schedule_meta["num_dates"])

    numcourts, numplayers, assign_tbd, allow_lastresort = (
        _prompt_for_court_and_player_settings(
            session=session,
            default_num_courts=defaults["NUM_COURTS"],
            default_num_players=defaults["NUM_PLAYERS"],
            default_assign_tbd=defaults["TBD"],
            default_allow_last=defaults["LAST"],
        )
    )

    yaml_text = _render_project_yaml(
        title=title,
        tag=tag,
        reply=reply,
        rep_dt=rep_dt,
        can_play=can_play,
        repeat=repeat,
        day=day,
        days=days,
        numcourts=numcourts,
        numplayers=numplayers,
        assign_tbd=assign_tbd,
        allow_lastresort=allow_lastresort,
        schedule_meta=schedule_meta,
        plm_roster=plm_roster,
        players=players,
        addresses=addresses,
        responses=defaults["RESPONSES"],
    )

    _write_project_file(
        session=session,
        project_file=project_state["project_file"],
        yaml_text=yaml_text,
        tag=tag,
        players=players,
        addresses=addresses,
        responses=defaults["RESPONSES"],
    )

    return project_state["project_file"]


def create_project_from_template(
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
    player_tags = list(players.keys())
    tag_completer = FuzzyWordCompleter(player_tags)

    selected_template = _prompt_for_initial_template_selection(
        session=session,
        template_names=list_template_names(),
    )
    if not selected_template:
        print("cancelled")
        return None

    defaults = _apply_selected_template_defaults(
        defaults=_new_project_defaults(),
        template_name=selected_template,
    )

    if str(defaults["REPEAT"]).lower() == "y" and defaults["DAY"] not in ["", None]:
        defaults, derived_period = _apply_optional_period_defaults(
            session=session,
            defaults=defaults,
        )
        project_state = {
            "input_name": "",
            "project_name": "",
            "project_file": "",
            "existing": False,
            "derived_period": derived_period,
        }
        project_state = _resolve_project_name_after_defaults(
            session=session,
            plm_projects=plm_projects,
            project_state=project_state,
            defaults=defaults,
        )
    else:
        project_state = {
            "input_name": "",
            "project_name": "",
            "project_file": "",
            "existing": False,
            "derived_period": None,
        }
        project_state = _prompt_for_template_project_name(
            session=session,
            plm_projects=plm_projects,
            project_state=project_state,
        )

    title = _prompt_for_title(session, defaults["TITLE"])
    tag = _prompt_for_player_tag(
        session=session,
        plm_roster=plm_roster,
        players=players,
        player_tags=player_tags,
        tag_completer=tag_completer,
        default_tag=defaults["TAG"],
    )
    _show_selected_players(players, tag)

    reply, rep_dt = _prompt_for_template_reply_by_date(
        session=session,
        get_date=get_date,
        default_reply_by=defaults["REPLY_BY"],
        derived_period=project_state["derived_period"],
    )
    if reply is None:
        return None

    can_play = _prompt_for_can_play(session, defaults["CAN"])

    repeat_result = _prompt_for_repeat_schedule(
        session=session,
        get_date=get_date,
        get_dates=get_dates,
        repeat_default=defaults["REPEAT"],
        day_default=defaults["DAY"],
        begin_default=defaults["BEGIN"],
        end_default=defaults["END"],
        dates_default=defaults["DATES"],
        reply_dt=rep_dt,
    )
    if repeat_result.get("cancelled"):
        return None

    repeat = repeat_result["repeat"]
    day = repeat_result["day"]
    days = repeat_result["days"]

    schedule_meta = _build_schedule_metadata(days)
    _warn_about_unusual_schedule(schedule_meta["num_dates"])

    numcourts, numplayers, assign_tbd, allow_lastresort = (
        _prompt_for_court_and_player_settings(
            session=session,
            default_num_courts=defaults["NUM_COURTS"],
            default_num_players=defaults["NUM_PLAYERS"],
            default_assign_tbd=defaults["TBD"],
            default_allow_last=defaults["LAST"],
        )
    )

    yaml_text = _render_project_yaml(
        title=title,
        tag=tag,
        reply=reply,
        rep_dt=rep_dt,
        can_play=can_play,
        repeat=repeat,
        day=day,
        days=days,
        numcourts=numcourts,
        numplayers=numplayers,
        assign_tbd=assign_tbd,
        allow_lastresort=allow_lastresort,
        schedule_meta=schedule_meta,
        plm_roster=plm_roster,
        players=players,
        addresses=addresses,
        responses=defaults["RESPONSES"],
    )

    _write_project_file(
        session=session,
        project_file=project_state["project_file"],
        yaml_text=yaml_text,
        tag=tag,
        players=players,
        addresses=addresses,
        responses=defaults["RESPONSES"],
    )

    return project_state["project_file"]


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


def _initialize_project_state(
    *,
    session: PromptSession,
    plm_projects: str,
    template_selected: bool = False,
) -> dict[str, Any]:
    print(
        wrap_text(
            f"""\
A name is required for the project. It will be used to create a file in the projects directory,
        {rel_path(plm_projects)}
combining the project name with the extension 'yaml'. A short name that will sort in a useful way is suggested, e.g., `2022-4Q-TU` for scheduling Tuesdays in the 4th quarter of 2022.\
"""
        )
    )

    if template_selected:
        print(
            wrap_text(
                """\
You selected a template. If you enter the name of an existing project, that project will be opened for modification and the template selection will be ignored. Otherwise, the new project will use the selected template defaults.\
"""
            )
        )

    possible = list_project_files(plm_projects)
    completer = FuzzyWordCompleter(possible)
    proj = session.prompt("project: ", completer=completer, default="").strip()
    if not proj:
        sys.exit("canceled")

    project_name = os.path.join(plm_projects, proj)
    project_file = os.path.join(
        plm_projects, os.path.splitext(project_name)[0] + ".yaml"
    )

    return {
        "input_name": proj,
        "project_name": project_name,
        "project_file": project_file,
        "existing": os.path.exists(project_file),
    }


def _prompt_for_template_project_name(
    *,
    session: PromptSession,
    plm_projects: str,
    project_state: dict[str, Any],
) -> dict[str, Any]:
    print(
        wrap_text(
            f"""\
A name is needed for the new project file in
        {rel_path(plm_projects)}
If you already know the project name, enter it here. Otherwise you can accept the suggested name when one is available.\
"""
        )
    )

    proj = session.prompt("project name: ", default="").strip()
    if not proj:
        sys.exit("canceled")

    project_name = os.path.join(plm_projects, proj)
    project_file = os.path.join(
        plm_projects, os.path.splitext(project_name)[0] + ".yaml"
    )

    updated = dict(project_state)
    updated["input_name"] = proj
    updated["project_name"] = project_name
    updated["project_file"] = project_file
    return updated


def _load_existing_project_defaults(
    *,
    session: PromptSession,
    project_file: str,
) -> dict[str, Any] | None:
    print(f"\nUsing defaults from the existing:\n        {rel_path(project_file)}\n")
    ok = session.prompt(f"modify {rel_path(project_file)}: [Yn] ").strip()
    if ok.lower() == "n":
        return None

    yaml_data = load_project(project_file)
    return {
        "TITLE": yaml_data["TITLE"],
        "TAG": yaml_data["PLAYER_TAG"],
        "REPLY_BY": yaml_data["REPLY_BY"],
        "CAN": yaml_data.get("CAN", "y"),
        "REPEAT": yaml_data["REPEAT"],
        "DAY": yaml_data["DAY"],
        "BEGIN": yaml_data["BEGIN"],
        "END": yaml_data["END"],
        "RESPONSES": yaml_data["RESPONSES"],
        "DATES": yaml_data["DATES"],
        "NUM_COURTS": yaml_data.get("NUM_COURTS", "0"),
        "NUM_PLAYERS": yaml_data["NUM_PLAYERS"],
        "TBD": yaml_data.get("ASSIGN_TBD", "y"),
        "LAST": yaml_data.get("ALLOW_LAST", "n"),
    }


def _new_project_defaults() -> dict[str, Any]:
    return {
        "TITLE": "",
        "TAG": "",
        "REPLY_BY": "",
        "CAN": "y",
        "REPEAT": "y",
        "DAY": "",
        "BEGIN": "",
        "END": "",
        "RESPONSES": {},
        "DATES": [],
        "NUM_COURTS": "0",
        "NUM_PLAYERS": "",
        "TBD": "y",
        "LAST": "n",
    }


def _prompt_for_initial_template_selection(
    *,
    session: PromptSession,
    template_names: list[str],
) -> str:
    if not template_names:
        return ""

    print(
        wrap_text(
            """\
You can optionally start from a bundled project template to prefill common values such as player tag, repeat settings, weekday, number of players and court rules. Press <return> to skip templates and create the project manually. Completion is available for template names.\
"""
        )
    )
    template_completer = FuzzyWordCompleter(template_names)
    template_name = session.prompt(
        "template: ",
        completer=template_completer,
        complete_while_typing=True,
    ).strip()

    while template_name and template_name not in template_names:
        print(f"'{template_name}' is not an available template.")
        for name in template_names:
            description = template_description(name)
            if description:
                print(f"  {name}: {description}")
            else:
                print(f"  {name}")
        template_name = session.prompt(
            "template: ",
            completer=template_completer,
            complete_while_typing=True,
        ).strip()

    return template_name


def _apply_selected_template_defaults(
    *,
    defaults: dict[str, Any],
    template_name: str,
) -> dict[str, Any]:
    if not template_name:
        return defaults

    template_data = template_defaults(template_name) or {}
    description = template_description(template_name)
    if description:
        print(f"Using template '{template_name}': {description}")
    else:
        print(f"Using template '{template_name}'")

    merged = dict(defaults)
    merged["TITLE"] = template_data.get("TITLE_TEMPLATE", merged["TITLE"])
    merged["TAG"] = template_data.get("PLAYER_TAG", merged["TAG"])
    merged["CAN"] = str(template_data.get("CAN", merged["CAN"]))
    merged["REPEAT"] = str(template_data.get("REPEAT", merged["REPEAT"]))
    merged["DAY"] = template_data.get("DAY", merged["DAY"])
    merged["NUM_COURTS"] = str(template_data.get("NUM_COURTS", merged["NUM_COURTS"]))
    merged["NUM_PLAYERS"] = str(template_data.get("NUM_PLAYERS", merged["NUM_PLAYERS"]))
    merged["TBD"] = str(template_data.get("ASSIGN_TBD", merged["TBD"]))
    merged["LAST"] = str(template_data.get("ALLOW_LAST", merged["LAST"]))
    return merged


def _apply_optional_period_defaults(
    *,
    session: PromptSession,
    defaults: dict[str, Any],
) -> tuple[dict[str, Any], Any]:
    print(
        wrap_text(
            """\
For repeating template-based projects, you can optionally derive quarter defaults from either a year and two-digit month (`yyyy/mm`, e.g. `2026/07`) or a year and quarter (`yyyy/q`, where q is 1, 2, 3 or 4, e.g. `2026/3`). This can suggest the project name, title and beginning/ending dates. Press <return> to skip and enter dates manually.\
"""
        )
    )

    derived_seed = session.prompt(
        "derive from year/two-digit-month or year/quarter: ",
        default="",
    ).strip()

    derived_period = None
    merged = dict(defaults)

    while derived_seed:
        try:
            second_part = derived_seed.split("/", 1)[1].strip()
            if len(second_part) == 1:
                derived_period = infer_period_from_year_quarter(derived_seed)
            elif len(second_part) == 2:
                seed_year, seed_month = [
                    int(x.strip()) for x in derived_seed.split("/", 1)
                ]
                derived_period = infer_period_from_year_month(seed_year, seed_month)
            else:
                raise ValueError(
                    "use 'yyyy/q' for quarter input or 'yyyy/mm' for month input"
                )

            title_template = str(merged["TITLE"])
            merged["TITLE"] = render_title_template(
                title_template,
                year=derived_period.year,
                quarter=derived_period.quarter,
                period=derived_period.period_label,
                start_month=derived_period.start_month,
                end_month=derived_period.end_month,
            )
            merged["BEGIN"] = derived_period.begin_ymd
            merged["END"] = derived_period.end_ymd
            break
        except Exception as exc:
            print(f"Could not derive quarter defaults from '{derived_seed}': {exc}")
            derived_seed = session.prompt(
                "derive from year/two-digit-month or year/quarter: ",
                default="",
            ).strip()

    return merged, derived_period


def _resolve_project_name_after_defaults(
    *,
    session: PromptSession,
    plm_projects: str,
    project_state: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    derived_period = project_state.get("derived_period")
    if derived_period is None:
        return project_state

    suffix = weekday_tag_suffix(int(defaults["DAY"]))
    suggested_name = suggest_quarter_project_name(
        derived_period.year,
        derived_period.quarter,
        suffix,
    )
    print(
        f"Derived defaults: title='{defaults['TITLE']}', begin={defaults['BEGIN']}, end={defaults['END']}, suggested project name='{suggested_name}'"
    )

    current_name = os.path.splitext(project_state["input_name"])[0]
    proj = session.prompt(
        "project name: ",
        default=suggested_name or current_name,
    ).strip()
    if not proj:
        proj = suggested_name or current_name

    project_name = os.path.join(plm_projects, proj)
    project_file = os.path.join(
        plm_projects, os.path.splitext(project_name)[0] + ".yaml"
    )

    updated = dict(project_state)
    updated["project_name"] = project_name
    updated["project_file"] = project_file
    return updated


def _ensure_manual_project_name(
    *,
    session: PromptSession,
    plm_projects: str,
    project_state: dict[str, Any],
) -> dict[str, Any]:
    current_name = os.path.splitext(project_state["input_name"])[0]
    proj = session.prompt("project name: ", default=current_name).strip()
    if not proj:
        sys.exit("canceled")

    project_name = os.path.join(plm_projects, proj)
    project_file = os.path.join(
        plm_projects, os.path.splitext(project_name)[0] + ".yaml"
    )

    updated = dict(project_state)
    updated["project_name"] = project_name
    updated["project_file"] = project_file
    return updated


def _prompt_for_title(session: PromptSession, default_title: Any) -> str:
    print(
        wrap_text(
            """
A user friendly title is needed to use as the subject of emails sent to players initially requesting their availability dates and subsequently containing the schedules, e.g., `Tuesday Tennis 4th Quarter 2022`."""
        )
    )
    title = session.prompt("project title: ", default=str(default_title)).strip()
    if not title:
        sys.exit("canceled")
    return title


def _prompt_for_player_tag(
    *,
    session: PromptSession,
    plm_roster: str,
    players: dict[str, list[str]],
    player_tags: list[str],
    tag_completer: FuzzyWordCompleter,
    default_tag: Any,
) -> str:
    print(
        wrap_text(
            f"""
The players for this project will be those that have the tag you specify from {rel_path(plm_roster)}. These tags are currently available: [{", ".join(player_tags)}].\
"""
        )
    )
    tag = session.prompt(
        "player tag: ",
        completer=tag_completer,
        complete_while_typing=True,
        default=str(default_tag),
    )
    while tag not in player_tags:
        print(f"'{tag}' is not in {', '.join(player_tags)}")
        print(f"Available player tags: {', '.join(player_tags)}")
        tag = session.prompt(
            "player tag: ",
            completer=tag_completer,
            complete_while_typing=True,
            default=str(default_tag),
        )
    return tag


def _show_selected_players(players: dict[str, list[str]], tag: str) -> None:
    print(f"Selected players with the tag '{tag}':")
    for player in players[tag]:
        print(f"   {player}")


def _prompt_for_reply_by_date(*, get_date, default_reply_by: Any) -> tuple[str, Any]:
    print(
        wrap_text(
            """
The letter sent to players asking for their availability dates will request a reply by 6pm on the "reply by date" that you specify next.
"""
        )
    )
    reply = get_date("reply by date", default=str(default_reply_by))
    if reply is None:
        print("cancelled")
        return None, None
    rep_dt = parse(f"{reply} 6pm")
    print(f"reply by: {rep_dt.strftime('%Y/%-m/%-d %-I%p')}")
    return reply, rep_dt


def _prompt_for_template_reply_by_date(
    *,
    session: PromptSession,
    get_date,
    default_reply_by: Any,
    derived_period,
) -> tuple[str, Any]:
    if derived_period is None:
        return _prompt_for_reply_by_date(
            get_date=get_date,
            default_reply_by=default_reply_by,
        )

    start_month = derived_period.begin.strftime("%Y/%m")
    if derived_period.begin.month == 1:
        anchor_year = derived_period.begin.year - 1
        anchor_month = 12
    else:
        anchor_year = derived_period.begin.year
        anchor_month = derived_period.begin.month - 1
    anchor_month_text = f"{anchor_year:04d}/{anchor_month:02d}"

    print(
        wrap_text(
            f"""
The letter sent to players asking for their availability dates will request a reply by 6pm on the "reply by date" that you specify next.

Derived start month: {start_month}
Relative rule anchor month: {anchor_month_text}

For template-based projects with derived quarter defaults, you can enter either:
- an absolute date using yyyy/mm/dd with two-digit month and day, e.g. {anchor_month_text}/19
- a relative weekday rule such as 3FR, interpreted in {anchor_month_text}
"""
        )
    )

    default_value = str(default_reply_by).strip()
    while True:
        reply = session.prompt("reply by date or rule: ", default=default_value).strip()
        if not reply:
            print("cancelled")
            return None, None

        try:
            reply_date = parse_template_reply_by(
                reply,
                anchor_year=derived_period.begin.year,
                anchor_month=derived_period.begin.month,
            )
            normalized_reply = format_ymd(reply_date)
            rep_dt = parse(f"{normalized_reply} 6pm")
            print(
                f"reply by: {normalized_reply} ({rep_dt.strftime('%-I%p on %a, %b %-d')})"
            )
            return normalized_reply, rep_dt
        except ValueError as exc:
            print(f"error: {exc}")
            default_value = reply


def _prompt_for_can_play(session: PromptSession, default_can: Any) -> str:
    print(
        wrap_text(
            """
The letter sent to players asking for their availability dates will request a list either of dates they CAN play or dates they CANNOT play depending upon whether the answer to "interpret responses as can play dates" is Y or n.\
"""
        )
    )
    can_play = session.prompt(
        "interpret responses as CAN play dates: [Yn] ",
        completer=None,
        default=str(default_can),
    )
    can_play = can_play.lower()
    if can_play == "n":
        print("interpreting responses as CANNOT play dates")
    else:
        print("interpreting responses as CAN PLAY dates")
    return can_play


def _prompt_for_repeat_schedule(
    *,
    session: PromptSession,
    get_date,
    get_dates,
    repeat_default: Any,
    day_default: Any,
    begin_default: Any,
    end_default: Any,
    dates_default: list[str],
    reply_dt,
) -> dict[str, Any]:
    print(
        wrap_text(
            """
If play repeats weekly on the same weekday, playing dates can given by specifying the weekday and the beginning and ending dates. Otherwise, dates can be specified individually.
"""
        )
    )
    repeat = (
        session.prompt("Repeat weekly: [Yn] ", default=str(repeat_default))
        .lower()
        .strip()
    )

    if repeat == "y":
        day = int(
            session.prompt(
                "The integer weekday:\n    (0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat): ",
                default=str(day_default),
            )
        )
        weekday = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA}
        weekdays = {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
        }
        print(
            wrap_text(
                f"""
Play will be scheduled for {weekdays[day]}s falling on or after the "beginning date" you specify next."""
            )
        )
        beginning = get_date("beginning date", str(begin_default))
        if beginning is None:
            print("cancelled")
            return {"cancelled": True}
        beg_dt = parse(f"{beginning} 12am")
        print(f"beginning: {beg_dt}")

        print(
            wrap_text(
                f"""
Play will also be limited to {weekdays[day]}s falling on or before the "ending date" you specify next."""
            )
        )
        ending = get_date("ending date", str(end_default))
        if ending is None:
            print("cancelled")
            return {"cancelled": True}
        end_dt = parse(f"{ending} 11:59pm")
        print(f"ending: {end_dt}")

        days = list(rrule(WEEKLY, byweekday=weekday[day], dtstart=beg_dt, until=end_dt))
        return {
            "repeat": repeat,
            "day": day,
            "days": days,
        }

    day = None
    dates, days = get_dates(
        label="Dates",
        year=reply_dt.year,
        month=reply_dt.month,
        default=", ".join(dates_default),
    )
    print(f"using these dates:\n  {', '.join(dates)}")
    return {
        "repeat": repeat,
        "day": day,
        "days": days,
    }


def _build_schedule_metadata(days: list[Any]) -> dict[str, Any]:
    reply_formatted = None
    beginning_datetime = days[0]
    beginning_formatted = beginning_datetime.strftime("%Y/%-m/%-d")
    ending_datetime = days[-1]
    ending_formatted = ending_datetime.strftime("%Y/%-m/%-d")
    byear = beginning_datetime.year
    eyear = ending_datetime.year

    if byear == eyear:
        years = f"{byear}"
    else:
        years = f"{byear} - {eyear}"

    dates = ", ".join([f"{x.month}/{x.day}" for x in days])
    date_list = [x.strip() for x in dates.split(",")]

    return {
        "reply_formatted": reply_formatted,
        "beginning_datetime": beginning_datetime,
        "beginning_formatted": beginning_formatted,
        "ending_datetime": ending_datetime,
        "ending_formatted": ending_formatted,
        "years": years,
        "dates": dates,
        "date_list": date_list,
        "num_dates": len(days),
    }


def _warn_about_unusual_schedule(num_dates: int) -> None:
    if num_dates < 4:
        print("ERROR. At least 4 dates must be scheduled")
    elif num_dates >= 30:
        print(
            f"WARNING. An unusually large number of dates, {num_dates}, were scheduled. \nIs this what was intended?"
        )


def _prompt_for_court_and_player_settings(
    *,
    session: PromptSession,
    default_num_courts: Any,
    default_num_players: Any,
    default_assign_tbd: Any,
    default_allow_last: Any,
) -> tuple[str, str, str, str]:
    numcourts = session.prompt(
        "number of courts (0 for unlimited, else allowed number): ",
        default=str(default_num_courts),
    )
    numplayers = session.prompt(
        "number of players (2 for singles, 4 for doubles): ",
        default=str(default_num_players) if default_num_players else "4",
    )

    if numplayers == "4":
        assign_tbd = session.prompt(
            wrap_text(
                'Automatically assign "TBD" to a court when the addition of a single player would make it possible to schedule the court.'
            )
            + "[Yn] ",
            default=str(default_assign_tbd),
        )
        allow_lastresort = session.prompt(
            wrap_text(
                'Allow players to use the response "last" or to append "~" to their response dates to indicate their willingness to be scheduled as a player of last resort.'
            )
            + "[yN] ",
            default=str(default_allow_last),
        )
    else:
        assign_tbd = "n"
        allow_lastresort = "n"

    return numcourts, numplayers, assign_tbd, allow_lastresort


def _render_project_yaml(
    *,
    title: str,
    tag: str,
    reply: str,
    rep_dt,
    can_play: str,
    repeat: str,
    day,
    days: list[Any],
    numcourts: str,
    numplayers: str,
    assign_tbd: str,
    allow_lastresort: str,
    schedule_meta: dict[str, Any],
    plm_roster: str,
    players: dict[str, list[str]],
    addresses: dict[str, str],
    responses: dict[str, Any],
) -> str:
    reply_formatted = rep_dt.strftime("%Y/%-m/%-d")
    rep_date = rep_dt.strftime("%-I%p on %a, %b %-d")
    dates = schedule_meta["dates"]
    date_list = schedule_meta["date_list"]
    years = schedule_meta["years"]
    beginning_formatted = schedule_meta["beginning_formatted"]
    ending_formatted = schedule_meta["ending_formatted"]

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

    eg_day = days[1]
    eg_yes = eg_day.strftime("%-m/%-d")
    eg_no = eg_day.strftime("%b %-d")

    CAN = "CAN" if can_play == "y" else "CANNOT"
    ALL = "all" if can_play == "y" else "any"
    AND = "and also" if can_play == "y" else "but"

    tmpl = f"""# created by plm - Player Lineup Manager
TITLE: {title}
PLAYER_TAG: {tag}
REPLY_BY: {reply_formatted}
CAN: {can_play}
REPEAT: {repeat}
DAY: {day}
BEGIN: {beginning_formatted}
END: {ending_formatted}
DATES: [{dates}]
NUM_COURTS: {numcourts}
NUM_PLAYERS: {numplayers}
ASSIGN_TBD: {assign_tbd}
ALLOW_LAST: {allow_lastresort}

REQUEST: |
    It's time to set the schedule for these dates in {years}:

        {wrap_text(dates, 0, 8)}

    Please make a note on your calendars to email me the DATES YOU
    {CAN} PLAY from this list no later than {rep_date}.
    Timely replies are greatly appreciated.

    It would help me to copy and paste from your email if you would
    list your dates on one line, separated by commas in the same format
    as the list above. E.g., using {eg_yes}, not {eg_no}.

    If you want to be listed as a possible substitute for any of these
    dates, then append an "*" to the relevant dates. If, for example,
    you {CAN.lower()} play on {date_list[0]} and {date_list[3]} {AND} want to be listed as a possible
    substitute on {date_list[2]}, then your response should be

        {date_list[0]}, {date_list[2]}*, {date_list[3]}
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

        {wrap_text(dates, 0, 8)}

    Please remember that your list is due no later than {rep_date}.

    ___
    From my original request ...

    It would help me to copy and paste from your email if you would
    list your dates on one line, separated by commas in the same format
    as the list above. E.g., using {eg_yes}, not {eg_no}.

    If you want to be listed as a possible substitute for any of these
    dates, then append asterisks to the relevant dates. If, for example,
    you {CAN.lower()} play on {date_list[0]} and {date_list[3]} {AND} want to be listed as a possible
    substitute on {date_list[2]}, then your response should be

        {date_list[0]}, {date_list[2]}*, {date_list[3]}
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
    yaml_text: str,
    tag: str,
    players: dict[str, list[str]],
    addresses: dict[str, str],
    responses: dict[str, Any],
) -> None:
    response_rows = []
    email_rows = []

    for player in players[tag]:
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
