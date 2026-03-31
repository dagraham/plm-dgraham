import calendar
import shutil
from collections import OrderedDict
from datetime import date, datetime
from pprint import pprint

import pyperclip
import requests
from dateutil.parser import ParserError, parse
from dateutil.rrule import *
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit import print_formatted_text as print_formatted
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.styles.named_colors import NAMED_COLORS

from plm.__main__ import logger
from plm.email_flow import (
    ask_email_payload,
    nag_email_payload,
    run_email_clipboard_flow,
    schedule_email_payload,
)
from plm.project_creation import (
    create_project_manual as orchestrate_project_creation,
)
from plm.project_creation import (
    modify_project,
)
from plm.project_io import list_project_files, load_project, save_project, yaml
from plm.responses import normalize_response_value, parse_response_input
from plm.utils import (
    format_head,
    print_head,
    rel_path,
    wrap_format,
    wrap_print,
    wrap_text,
)

# Determine the best color depth supported by the terminal
output = create_output()
best_color_depth = output.get_default_color_depth()


def colored(text: str, color: str) -> None:
    """
    Prints `text` in the specified `color`.

    Args:
        text (str): The text to be printed.
        color (str): The name of the color to be used.

    Returns:
        None

    Raises:
        ValueError: If `color` is not a valid named color.
    """
    if color not in NAMED_COLORS:
        raise ValueError(f"Invalid color: {color}")

    try:
        tokens = FormattedText([(f"fg:{color}", text)])
        print_formatted(tokens, color_depth=best_color_depth)
    except Exception as e:
        print(e)
        print(f"{tokens = }")


import os

# for openWithDefault
import platform
import random
import re

# for check_output
import subprocess
import sys

leadingzero = re.compile(r"(?<!(:|\d|-))0+(?=\d)")

# for wrap_print
COLUMNS, ROWS = shutil.get_terminal_size()
divider = COLUMNS * "_"
COLUMNS -= 4
plm_projects = {}
plm_roster = {}
plm_version = None
plm_home = ""

cwd = os.getcwd()


def zero_fill_sort(dd: list[str]) -> list[str]:
    l = []
    for d in dd:
        x = d.split("/")
        x[0] = f"{int(x[0]):02}"
        if x[1].endswith("*"):
            x[1] = f"{int(x[1].rstrip('*')):02}*"
        elif x[1].endswith("~"):
            x[1] = f"{int(x[1].rstrip('~')):02}~"
        else:
            x[1] = f"{int(x[1]):02}"
        l.append(x)
    l.sort()
    return [f"{x[0].lstrip('0')}/{x[1].lstrip('0')}" for x in l]


def clear_screen(default_project=""):
    # Clearing the Screen
    # posix is os name for Linux or mac
    if os.name == "posix":
        os.system("clear")
    # else screen will be cleared for windows
    else:
        os.system("cls")
    return default_project


def copy_to_clipboard(text):
    pyperclip.copy(text)
    print("copied to system clipboard")


def openWithDefault(path):
    parts = [x.strip() for x in path.split(" ")]
    if len(parts) > 1:
        res = subprocess.Popen(
            [parts[0], " ".join(parts[1:])],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ok = True if res else False
    else:
        path = os.path.normpath(os.path.expanduser(path))
        sys_platform = platform.system()
        if platform.system() == "Darwin":  # macOS
            res = subprocess.run(
                ("open", path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif platform.system() == "Windows":  # Windows
            res = os.startfile(path)
        else:  # linux
            res = subprocess.run(
                ("xdg-open", path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        ret_code = res.returncode
        ok = ret_code == 0
    if not ok:
        print(f"failed to open '{path}'")


def get_project(default_project=""):
    project = os.path.split(default_project)[1] if default_project else ""
    print("Select the active project.")
    possible = list_project_files(plm_projects)
    completer = FuzzyWordCompleter(possible)
    proj = prompt("project: ", completer=completer, default=project).strip()
    proj = proj if proj.endswith(".yaml") else proj + ".yaml"
    project = os.path.join(plm_projects, proj)
    if os.path.isfile(project):
        clear_screen()
        return project
    else:
        print(f"project '{project}' not found")
        return None


def get_dates(label, year, month, default):

    help = f"""
Specify playing dates in calendar order separated by commas on one line using the 'mm/dd' format for each date. The year from your "reply by date", {year}, will be assumed unless the month is less than month from your "reply by date", {month}, in which case the following year will be assumed. E.g. with "reply by" year 2022 and month 10, '11/4' and '1/5' would be interpreted, respectively, as '2022/11/04' and '2023/01/05'.

If the last part of your entry has the format 'mm', i.e., omits the '/dd', then a calendar for that month will be displayed to assist in your entries.
"""

    print(help)

    again = True
    year = int(year)
    month = int(month)
    current = ""
    confirm = False
    while again:
        result = prompt(f"{label}: ", completer=None, default=current)
        if not result:
            print("quitting ...")
            return None
        msg = ""
        dates = [x.strip() for x in result.split(",")]
        days = []
        current = ", ".join(dates)
        for i in range(len(dates)):
            md = dates[i]
            try:
                m_d = [int(x) for x in md.split("/") if x]
            except Exception as e:
                print(f"error: bad entry for month/day: {md}")
                continue
            if m_d[0] > 12:
                print(f"error: bad entry for month: {month}")
                continue
            yr = year + 1 if m_d[0] < month else year
            if len(m_d) == 1:  # month only
                print(calendar.month(yr, m_d[0]))
                confirm = False
            else:
                days.append(parse(f"{yr}/{md}", yearfirst=True))
                confirm = True  # enter pressed with mm/dd

        if confirm:
            print(f"dates: {current}")
            ok = prompt("Accept these dates: [Yn]").strip()
            if ok.lower() != "n":
                return dates, days


def get_date(label="", default=""):
    help = """\
Enter a date using the format 'yyyy/mm/dd' or, to consult a calendar, enter 'yyyy/mm' to see a calendar showing the month or 'yyyy' to see a calendar for the entire year.\
"""
    again = True
    while again:
        print(wrap_text(help))
        result = prompt(f"{label}: ", completer=None, default=str(default))

        if not result:
            return None

        msg = ""
        parts = [x.strip() for x in result.split("/") if x]
        if len(parts) == 3:
            try:
                dt = parse(result, yearfirst=True)
            except ParserError as e:
                msg = f"error: {e}"
            else:
                return dt.strftime("%Y/%-m/%-d")
        elif len(parts) == 2:
            # year and month - show month
            try:
                year = int(parts[0]) if int(parts[0]) > 2000 else 2000 + int(parts[0])
                month = int(parts[1])
                print(calendar.month(year, month))
                default = f"{year}/{month}"
            except Exception as e:
                msg = f"error: {e}"

        elif len(parts) == 1:
            # only year - show year
            try:
                year = int(parts[0]) if int(parts[0]) > 2000 else 2000 + int(parts[0])
                print(calendar.calendar(year))
                default = f"{year}"
            except Exception as e:
                msg = f"error: {e}"

        else:
            msg = f"bad entry: {result}"

        if msg:
            print(msg)
            print(
                f"bad entry: {result}. Either 'yyyy/mm/dd', 'yyyy/mm' or 'yyyy' is required. Enter nothing to cancel."
            )

    return date


def edit_roster():
    openWithDefault(plm_roster)


def open_project(default_project=""):
    project = get_project(default_project)
    if project:
        openWithDefault(project)


def open_readme():
    help_link = "https://dagraham.github.io/plm-dgraham/"
    openWithDefault(help_link)


def main():
    default_project = clear_screen(default_project="")
    project = "{default_project}" if default_project else "not yet selected"

    commands = """
commands:
    h:  show this help message
    H:  show on-line documentation
    e:  edit 'roster.yaml' using the default editor
    c:  create a new quarterly doubles project        (1)
    m:  modify an existing project                    (1)
    p:  select the active project from existing       (1)
    a:  ask players for their "can play" dates        (2)
    r:  record the "can play" responses               (3)
    n:  nag players to submit can play responses      (4)
    s:  schedule play using the "can play" responses  (5)
    d:  deliver the schedule to the players           (6)
    v:  view the current settings of a project
    u:  check for an update to a later plm version
    q:  quit
"""

    try:
        again = True
        while again:
            if default_project:
                project = os.path.split(default_project)[1]
            else:
                project = wrap_text(
                    """\
The active project has not been chosen.
         Use command 'c' to create one or 'p' to select one.
""",
                    0,
                    8,
                )
            help = f"""\
Player Lineup Manager ({plm_version})
home directory: {plm_home}
project: {project}
{commands}"""
            print(help)
            answer = input("command: ").strip()
            if answer not in "clmhevpnarsdouq?H":
                print(f"invalid command: '{answer}'")
                print(commands)
            elif answer in ["h", "?"]:
                clear_screen()
            elif answer == "H":
                open_readme()
            elif answer == "u":
                res = check_update()
                print(f"\n{res}\n")
            elif answer == "q":
                again = False
                print("quitting plm ...")
            else:
                if answer == "e":
                    edit_roster()
                elif answer == "o":
                    default_project = open_project(default_project)
                elif answer == "v":
                    default_project = view_project(default_project)
                elif answer == "c":
                    default_project = create_project(default_project)
                elif answer == "m":
                    default_project = modify_project(
                        plm_roster=plm_roster,
                        plm_projects=plm_projects,
                        clear_screen=clear_screen,
                    )
                elif answer == "p":
                    default_project = get_project(default_project)
                elif answer == "a":
                    default_project = ask_players(default_project)
                elif answer == "n":
                    default_project = nag_players(default_project)
                elif answer == "r":
                    default_project = record_responses(default_project)
                elif answer == "s":
                    default_project = create_schedule(default_project)
                elif answer == "d":
                    default_project = deliver_schedule(default_project)
                elif answer == "l":
                    default_project = clear_screen(default_project)

    except KeyboardInterrupt:
        play = False
        print("\nquitting plm ...")


def check_update():
    url = "https://raw.githubusercontent.com/dagraham/plm-dgraham/master/plm/__version__.py"
    try:
        r = requests.get(url)
        t = r.text.strip()
        # t will be something like "version = '4.7.2'"
        url_version = t.split(" ")[-1][
            1:-1
        ]  # split(' ')[-1] will give "'4.7.2'" and url_version will then be '4.7.2'
    except:
        url_version = None
    if url_version is None:
        res = "update information is unavailable"
    else:
        if url_version > plm_version:
            res = f"An update is available from {plm_version} (installed) to {url_version}"
        else:
            res = (
                f"The installed version of plm, {plm_version}, is the latest available."
            )

    return res


def view_project(default_project=""):
    if not default_project:
        print("The first step is to select the project.")
        default_project = get_project(default_project)
        if not default_project:
            print("Cancelled")
            return

    yaml_data = load_project(default_project)
    project_name = os.path.split(default_project)[1]
    border_length = min(18, (COLUMNS - len(project_name)) // 2)
    markers = "∨" * border_length
    clear_screen(default_project)

    dates = yaml_data.get("DATES", [])
    fallback_year = ""
    fallback_quarter = ""

    if dates:
        try:
            first_month = int(str(dates[0]).split("/")[0])
            fallback_quarter = ((first_month - 1) // 3) + 1

            reply_by = yaml_data.get("REPLY_BY", "")
            if reply_by:
                reply_dt = parse(str(reply_by), yearfirst=True)
                fallback_year = (
                    reply_dt.year + 1 if first_month < reply_dt.month else reply_dt.year
                )
            else:
                fallback_year = datetime.now().year
        except Exception:
            fallback_year = ""
            fallback_quarter = ""

    display_fields = [
        ("YEAR", yaml_data.get("YEAR", fallback_year)),
        ("QUARTER", yaml_data.get("QUARTER", fallback_quarter)),
        ("DAY", yaml_data.get("DAY", "")),
        ("NAME", yaml_data.get("NAME", os.path.splitext(project_name)[0])),
        ("TITLE", yaml_data.get("TITLE", "")),
        ("PLAYER_TAG", yaml_data.get("PLAYER_TAG", "")),
        ("REPLY_BY", yaml_data.get("REPLY_BY", "")),
        ("CAN", yaml_data.get("CAN", "")),
        ("NUM_COURTS", yaml_data.get("NUM_COURTS", "")),
        ("NUM_PLAYERS", yaml_data.get("NUM_PLAYERS", "")),
        ("ASSIGN_TBD", yaml_data.get("ASSIGN_TBD", "")),
        ("ALLOW_LAST", yaml_data.get("ALLOW_LAST", "")),
    ]

    colored(f"{markers} begin {project_name} {markers}", "LightSkyBlue")
    for key, value in display_fields:
        colored(f"{key}: {value}", "LightSkyBlue")

    if dates:
        colored("", "LightSkyBlue")
        colored(f"DATES: {', '.join(dates)}", "LightSkyBlue")

    markers = "∧" * border_length
    colored(f"{markers} end {project_name} {markers}\n", "LightSkyBlue")

    return default_project


def create_project(default_project=""):
    return orchestrate_project_creation(
        plm_roster=plm_roster,
        plm_projects=plm_projects,
        clear_screen=clear_screen,
        get_date=get_date,
        get_dates=get_dates,
    )


def format_name(name):
    # used to get 'fname lname' from 'lname, fname' for the schedule
    if "," in name:
        lname, fname = name.split(", ")
        return f"{fname} {lname}"
    else:
        return name


def select(freq={}, chosen=[], remaining=[], numplayers=4):
    """
    Add players from remaining to chosen which have the lowest combined
    frequency with players in chosen
    """

    while len(chosen) < numplayers and len(remaining) > 0:
        talley = []

        for other in remaining:
            tmp = 0
            for name in chosen:
                if other in freq and name in freq[other]:
                    tmp += freq[other][name]
            talley.append([tmp, other])
        new = talley[0][1]
        for name in chosen:
            freq = bump_freq(freq, name, new)
        chosen.append(new)
        remaining.remove(new)

    return freq, chosen, remaining


def toggle_can_play(default_project):
    """
    For testing. Toggle can_play between 'y' and 'no' and 'reverse'
    responses for players accordingly.
    """
    yaml_data = load_project(default_project)
    CAN = yaml_data.get("CAN", "y")
    RESPONSES = yaml_data["RESPONSES"]
    DATES = yaml_data["DATES"]

    can_play = "n" if CAN == "y" else "y"
    new_responses = {}
    for name in RESPONSES:
        if RESPONSES[name] == "none":
            new_responses[name] = "all"
            sub = []
        elif RESPONSES[name] == "all":
            new_responses[name] = "none"
            sub = []
        elif RESPONSES[name] == "sub":
            new_responses[name] = "sub"
            sub = [x for x in DATES]
        else:
            new_responses.setdefault(name, [])
            sub = [x for x in RESPONSES[name] if x.endswith("*")]
            other = [x for x in RESPONSES[name] if not x.endswith("*")]
            notother = [x for x in DATES if x not in other and x not in sub]
            new_responses[name] = zero_fill_sort(sub + notother)

    yaml_data["CAN"] = can_play
    yaml_data["RESPONSES"] = new_responses

    save_project(default_project, yaml_data)
    print(f"Toggle applied to {default_project}")


def create_schedule(default_project=""):
    if not default_project:
        print("The first step is to select the project.")
        default_project = get_project(default_project)
        if not default_project:
            print("Cancelled")
            return
    yaml_data = load_project(default_project)

    possible = {}
    response = {}
    responsedates = {}
    availablebydates = {}
    substitutebydates = {}
    lastresortbydates = {}
    unselected = {}
    opportunities = {}
    captain = {}
    captaindates = {}
    courts = {}
    issues = []
    notcaptain = {}
    playerdates = {}
    substitute = {}
    lastresort = {}
    substitutedates = {}
    lastresortdates = {}
    schedule = OrderedDict({})
    onlysubstitute = []
    notresponded = []
    dates_scheduled = []
    dates_notscheduled = []
    unresponse = {}
    project_hsh = {}
    courts_scheduled = {}
    session = PromptSession()
    proj_path = default_project
    now = datetime.now()
    cur_year = now.year
    cur_month = now.month

    TITLE = yaml_data["TITLE"]
    responses = yaml_data["RESPONSES"]
    addresses = yaml_data["ADDRESSES"]
    DATES = yaml_data["DATES"]
    NUM_PLAYERS = yaml_data["NUM_PLAYERS"]
    ASSIGN_TBD = yaml_data["ASSIGN_TBD"] == "y"
    ALLOW_LAST = yaml_data.get("ALLOW_LAST", "n") == "y"
    can = yaml_data["CAN"] == "y"

    RESPONSES = {format_name(k): v for k, v in responses.items()}
    ADDRESSES = {format_name(k): v for k, v in addresses.items()}

    # get the roster
    NAMES = [x for x in RESPONSES.keys()]

    missing = [
        x for x in [TITLE, RESPONSES, ADDRESSES, DATES, NUM_PLAYERS, NAMES] if not x
    ]

    if missing:
        print(
            f"ERROR. The following required data fields were missing or empty in {proj_path}:\n {', '.join(missing)}"
        )
        return None

    for name in NAMES:
        # initialize all the name counters
        if name == "TBD":
            continue
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        lastresort[name] = 0
        unselected[name] = 0
        opportunities[name] = 0
        response[name] = 0
        if RESPONSES[name] in ["nr", "na"]:
            notresponded.append(name)

    if notresponded:
        print("Not yet responded:\n  {0}\n".format("\n  ".join(notresponded)))

    NUM_COURTS = yaml_data["NUM_COURTS"]

    # get response players for each date
    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        responsedates[name] = []
        substitutedates[name] = []
        lastresortdates[name] = []
        response[name] = 0
        playerdates[name] = []
        if RESPONSES[name] in ["na", "nr", "none"]:
            responsedates[name] = []
            substitutedates[name] = []
            lastresortdates[name] = []
        elif RESPONSES[name] in ["all"] or len(RESPONSES[name]) == 0:
            responsedates[name] = [x for x in DATES]
            substitutedates[name] = []
            lastresortdates[name] = []
        elif ALLOW_LAST and RESPONSES[name] in ["last"]:
            responsedates[name] = []
            substitutedates[name] = []
            lastresortdates[name] = [x for x in DATES]
        elif RESPONSES[name] in ["sub"]:
            responsedates[name] = []
            substitutedates[name] = [x for x in DATES]
        else:
            for x in RESPONSES[name]:
                if x.endswith("*"):
                    substitutedates.setdefault(name, []).append(x[:-1])
                elif ALLOW_LAST and x.endswith("~"):
                    lastresortdates.setdefault(name, []).append(x[:-1])
                else:
                    responsedates[name].append(x)

            baddates = [
                x for x in responsedates[name] + substitutedates[name] if x not in DATES
            ]
            if baddates:
                issues.append(
                    f"responsedates[{name}]: {responsedates[name]}; substitutedates[{name}]: {substitutedates[name]}"
                )
                issues.append(f"  Not response dates: {baddates}")

        for dd in DATES:
            if dd in substitutedates[name]:
                substitutebydates.setdefault(dd, []).append(name)
                substitute.setdefault(name, 0)
                substitute[name] += 1
            elif dd in lastresortdates[name]:
                lastresortbydates.setdefault(dd, []).append(name)
                lastresort.setdefault(name, 0)
                lastresort[name] += 1
            elif can == (dd in responsedates[name]):
                availablebydates.setdefault(dd, []).append(name)
                response[name] += 1

    num_dates = len(DATES)
    freq = {}
    for name in NAMES:
        for other in NAMES:
            if other == name:
                continue
            freq = bump_freq(freq, name, other, bump=False)

    delta = 10

    # choose the players for each date and court
    for dd in DATES:
        num_selected = 0
        lastresort_used = []
        courts = []
        substitutes = []
        unsched = []
        available = availablebydates.get(dd, [])
        possible = availablebydates.get(dd, [])
        lastresort = lastresortbydates.get(dd, [])
        if NUM_COURTS:
            num_courts = min(NUM_COURTS, len(available) // NUM_PLAYERS)
            # only if another court can be added without violating the NUM_COURTS constraint
            partial_court = (
                len(available) % NUM_PLAYERS if num_courts < NUM_COURTS else 0
            )
        else:
            num_courts = len(available) // NUM_PLAYERS
            partial_court = len(available) % NUM_PLAYERS

        num_selected = num_courts * NUM_PLAYERS

        needed = NUM_PLAYERS - partial_court if partial_court else 0
        add = ""
        if needed:
            if len(lastresort) >= needed and num_courts + 1 >= needed:
                # we need players to fill a partial court and we have enough lastresort players and enough courts to use
                # at most one last resort player per court
                lastresort_used = random.sample(lastresort, needed)
                num_selected += partial_court
                num_courts += 1
            elif needed == 1 and ASSIGN_TBD:
                num_selected += partial_court
                num_courts += 1
                add = "TBD"

        courts_scheduled[dd] = num_courts

        if num_courts:
            dates_scheduled.append(dd)
        else:
            dates_notscheduled.append(dd)

        num_notselected = len(available) - num_selected
        if add:
            available.append(add)

        selected = available
        logger.debug(
            f"{dd}: {available = } {needed = } {ASSIGN_TBD = } {partial_court = } {selected = } {num_selected = } {num_notselected = } {num_courts = }"
        )

        if num_notselected:
            # at least one court =>
            # randomly choose the excess players and remove them from selected
            grps = {}
            for name in available:
                # players who can play on this date
                try:
                    grps.setdefault(unselected[name] / response[name], []).append(name)
                except:
                    print(f"response[{name}]: {response[name]}")
                    print(f"unselected[{name}]: {unselected[name]}")

            nums = [x for x in grps]
            nums.sort()
            while len(unsched) < num_notselected:
                for num in nums:
                    needed = num_notselected - len(unsched)
                    if len(grps[num]) <= needed:
                        unsched.extend(grps[num])
                    else:
                        unsched.extend(random.sample(grps[num], needed))
            for name in unsched:
                available.remove(name)
        else:
            unsched = []

        for name in available:
            # if name == 'TBD':
            #     continue
            playerdates.setdefault(name, []).append(dd)

        if len(available) >= NUM_PLAYERS:
            for name in unsched:
                if name == "TBD":
                    continue
                unselected[name] += 1
                opportunities[name] += 1
            for name in possible:
                if name == "TBD":
                    continue
                opportunities[name] += 1

        grps = {}
        for name in selected:  # available - lastresort
            try:
                if name == "TBD":
                    continue
                grps.setdefault(captain[name] - notcaptain[name], []).append(name)
            except:
                print("except", name)

        nums = [x for x in grps]
        nums.sort()
        captains = []
        players = available
        random.shuffle(players)
        lst = []
        for i in range(num_courts):
            court = []
            num_to_select = NUM_PLAYERS - 1 if lastresort_used else NUM_PLAYERS
            freq, court, players = select(freq, court, players, num_to_select)
            logger.debug(f"{court = } {players = } {num_to_select = } {captain = }")
            random.shuffle(court)
            has_tbd = "TBD" in court
            tmp = [
                (
                    captain[court[j]] / (captain[court[j]] + notcaptain[court[j]] + 1),
                    j,
                )
                for j in range(num_to_select)
                if court[j] != "TBD"
            ]
            # put the least often captain first
            tmp.sort()
            court = [court[j] for (i, j) in tmp]
            lastresort_player = None
            if lastresort_used:
                lastresort_player = lastresort_used.pop(0)
                playerdates.setdefault(lastresort_player, []).append(dd)
                for x in court:
                    bump_freq(freq, x, lastresort_player)
                court.append(lastresort_player)
            if has_tbd:
                court.append("TBD")
            courts.append("{0}: {1}".format(i + 1, ", ".join(court)))
            for j in range(len(court)):
                if j == 0:
                    c = "*"
                    cp = " (captain)"
                    captain[court[j]] += 1
                    captaindates.setdefault(court[j], []).append(dd)
                elif court[j] != "TBD":
                    c = cp = ""
                    notcaptain[court[j]] += 1
            lst = []
            for court in courts:
                num, pstr = court.split(":")
                tmp = [x.strip() for x in pstr.split(",")]
                lst.append(tmp)
        random.shuffle(lst)
        lst.append(unsched)
        schedule[dd] = lst

    if issues:
        # print any error messages that were generated and quit
        for line in issues:
            print(line)
        return

    DATES_SCHED = [dd for dd in dates_scheduled]

    scheduled = [f"{dd} [{courts_scheduled[dd]}]" for dd in dates_scheduled]

    schdatestr = (
        "{0} scheduled dates [courts]: {1}".format(
            len(scheduled), ", ".join([x for x in scheduled])
        )
        if scheduled
        else "Scheduled dates: none"
    )

    output = [format_head(TITLE)]

    tbd_instruction = (
        """\
If 'TBD' is listed for a date, the captain is also responsible for
   finding a substitute, if possible, and for informing the other
   players whether or not it will be possible to play.
"""
        if ASSIGN_TBD
        else ""
    )

    note = f"""\
1) The captain is responsible for reserving a court and providing balls.
   {tbd_instruction}
2) A player who is scheduled to play but, for whatever reason,
   cannot play is responsible for finding a substitute and for
   informing the other player(s) in the group.
"""

    output.append(note)

    section = "By date"
    output.append(format_head(section))

    lastresort_bydate = (
        f"""\
4) 'Last Resort' players for a date agreed to play if doing so made
   it possible to schedule a court for {NUM_PLAYERS - 1} other available players.
"""
        if ALLOW_LAST
        else ""
    )

    output.append(
        f"""\
1) The player listed first in each 'Scheduled' group is the
   captain for that group.
2) 'Unscheduled' players for a date were available to play but were
   not assigned. If you are among these available but unassigned
   players, would you please reach out to other players, even
   players from outside the group, before other plans are made to
   see if a foursome could be scheduled? Email addresses are in
   the 'BY PLAYER' section below for those in the group.
3) 'Substitutes' for a date asked not to be scheduled but instead
   to be listed as possible substitutes.
{lastresort_bydate}
"""
    )
    date_year = cur_year
    date_month = cur_month
    for dd in DATES:
        date_month, _ = [int(x) for x in dd.split("/")]
        if cur_month > date_month:
            date_year += 1
        cur_month = date_month

        d = parse(f"{date_year}/{dd} 12am")
        dtfmt = d.strftime("%a %b %-d")
        if not dd in schedule:
            continue
        avail = schedule[dd].pop()

        subs = [f"{x}" for x in substitutebydates.get(dd, [])]
        substr = ", ".join(subs) if subs else "none"
        last = [f"{x}" for x in lastresortbydates.get(dd, [])]
        laststr = ", ".join(last) if last else "none"
        availstr = ", ".join(avail) if avail else "none"

        courts = schedule[dd]

        output.append(f"{dtfmt}")
        if courts:
            output.append(f"    Scheduled")
            for i in range(len(courts)):
                output.append(
                    wrap_format("      {0}: {1}".format(i + 1, ", ".join(courts[i])))
                )
        else:
            output.append(f"    Scheduled: none")
        output.append(wrap_format("    Unscheduled: {0}".format(availstr)))
        output.append(wrap_format("    Substitutes: {0}".format(substr)))
        if ALLOW_LAST:
            output.append(wrap_format("    Last Resort: {0}".format(laststr)))
        output.append("")

    output.append("")
    section = "By player"
    output.append(format_head(section))

    subs2avail = []
    cap2play = []
    output.append(
        """\
Scheduled dates on which the player is captain and available
dates on which a court is scheduled have asterisks.
"""
    )
    for name in NAMES:
        if name not in RESPONSES:
            continue
        response = RESPONSES[name]
        if isinstance(response, list):
            response = zero_fill_sort(response)
            response = ", ".join(response) if response else "none"
        output.append(f"{name}: {ADDRESSES.get(name, 'no email address')}")

        if RESPONSES[name]:
            if RESPONSES[name] == "all":
                response = "all"
            elif RESPONSES[name] in ["na", "nr"]:
                response = "no reply"
            elif RESPONSES[name] == "sub":
                response = "sub"
            elif RESPONSES[name] == "last":
                response = "last resort"
            elif RESPONSES[name] == "none":
                response = "none"
            else:
                response = ", ".join(RESPONSES[name])

        playswith = []
        if name in freq:
            for other in NAMES:
                if other not in freq[name] or freq[name][other] == 0:
                    continue
                playswith.append("{0} {1}".format(other, freq[name][other]))

        if name in playerdates:
            player_dates = [x for x in playerdates[name]]

            available_dates = availablebydates.get(name, [])
            for date in available_dates:
                if date in DATES_SCHED:
                    indx = available_dates.index(date)
                    available_dates[indx] = f"{date}*"

            if name in captaindates:
                cptndates = [x for x in captaindates.get(name, [])]
                for date in cptndates:
                    indx = player_dates.index(date)
                    player_dates[indx] = f"{date}*"

            datestr = ", ".join(player_dates)
            availstr = ", ".join(response)
            output.append(
                wrap_format(f"    scheduled ({len(player_dates)}): {datestr}")
            )
            if playswith:
                output.append(
                    wrap_format("    playing with: {0}".format(", ".join(playswith)))
                )
            output.append("    ---")
            output.append(wrap_format(f"    response: {response}"))
            if available_dates:
                output.append(
                    wrap_format(
                        "    response ({0}): {1}".format(len(response), availstr)
                    )
                )

        if name in substitutedates and substitutedates[name]:
            dates = substitutedates[name]
            datestr = ", ".join(dates) if dates else "none"
            output.append(
                wrap_format("    substitute ({0}): {1}".format(len(dates), datestr))
            )

        output.append("")

    output.append("")

    section = "Summary"
    output.append(format_head(section))

    output.append(wrap_format(schdatestr))
    output.append("")

    schedule = "\n".join(output)

    yaml_data["SCHEDULE"] = schedule

    save_project(default_project, yaml_data)
    print(f"Schedule saved to {proj_path}")

    return default_project


def bump_freq(freq, a, b, bump: bool = True):
    freq.setdefault(a, {})
    freq.setdefault(b, {})
    freq[a].setdefault(b, 0)
    freq[b].setdefault(a, 0)
    if bump:
        freq[a][b] += 1
        freq[b][a] += 1
    return freq


def ask_players(default_project=""):
    if not default_project:
        print("The first step is to select the project.")
        default_project = get_project(default_project)
        if not default_project:
            print("Cancelled")
            return
    clear_screen()
    print(
        """
This will help you prepare an email to request can play dates
from the relevant players."""
    )

    yaml_data = load_project(default_project)
    addresses, subject, body = ask_email_payload(yaml_data)

    ok = run_email_clipboard_flow(
        addresses,
        subject,
        body,
        copy_to_clipboard=copy_to_clipboard,
        prompt=prompt,
        intro_text="""The next step is to
1) open your favorite email application,
2) create a new email and
3) be ready to paste
  (a) the addresses
  (b) the subject
  (c) the body
into the email. You will be prompted for each paste operation in turn.
""",
        body_label="BODY of the request",
        addresses_step_text="""
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
""",
        subject_step_text="""
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
""",
        body_step_text="""
The request has been copied to the system clipboard. When you
have pasted it into the "body" section of your email, your email
should be ready to send.
""",
    )
    if ok:
        return default_project


def nag_players(default_project=""):
    print(
        """
This will help you prepare an email to nag players for their can
play dates from the relevant players."""
    )

    print("The first step is to select the project.")
    project = get_project(default_project)
    if not project:
        print("Cancelled")
        return
    default_project = os.path.split(project)[1]
    yaml_data = load_project(project)
    addresses, subject, body = nag_email_payload(yaml_data)

    ok = run_email_clipboard_flow(
        addresses,
        subject,
        body,
        copy_to_clipboard=copy_to_clipboard,
        prompt=prompt,
        intro_text="""The next step is to
1) open your favorite email application,
2) create a new email and
3) be ready to paste
  (a) the addresses
  (b) the subject
  (c) the body
into the email. You will be prompted for each paste operation in turn.
""",
        body_label="BODY of the request",
        addresses_step_text="""
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
""",
        subject_step_text="""
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
""",
        body_step_text="""
The reminder has been copied to the system clipboard. When you
have pasted it into the "body" section of your email, your email
should be ready to send.
""",
    )
    if ok:
        return default_project


def deliver_schedule(default_project=""):
    print(
        """
This will help you prepare an email to send the completed schedule
for a project to the relevant players."""
    )

    print("The first step is to select the project.")
    project = get_project(default_project)
    if not project:
        print("Cancelled")
        return default_project
    default_project = os.path.split(project)[1]
    yaml_data = load_project(project)
    addresses, subject, body = schedule_email_payload(yaml_data)

    ok = run_email_clipboard_flow(
        addresses,
        subject,
        body,
        copy_to_clipboard=copy_to_clipboard,
        prompt=prompt,
        intro_text="""
The next step is to
(1) open your favorite email application
(2) create a new email and
(3) be ready to paste
    (a) the addresses
    (b) the subject
    (c) the body
into the email. You will be prompted for each paste operation in turn.
""",
        body_label="SCHEDULE",
        addresses_step_text="""
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
""",
        subject_step_text="""
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
""",
        body_step_text="""
The schedule has been copied to the system clipboard. When you
have pasted it into the "body" section of your email your email
should be ready to send.
""",
    )
    if ok:
        return default_project


def record_responses(default_project=""):
    if not default_project:
        print("The first step is to select the project.")
        default_project = get_project(default_project)
        if not default_project:
            print("Cancelled")
            return
    yaml_data = load_project(default_project)

    RESPONSES = yaml_data["RESPONSES"]
    CAN = "CAN" if yaml_data.get("CAN", "y") == "y" else "CANNOT"
    DATES = yaml_data["DATES"]
    PLAYER_TAG = yaml_data["PLAYER_TAG"]
    ALLOW_LAST = True if yaml_data.get("ALLOW_LAST", "n") == "y" else False

    players = FuzzyWordCompleter([x for x in RESPONSES] + [".", "?"])

    again = True
    player_default = ""
    print(
        f"""\
Entering responses for project {os.path.split(default_project)[1]}

The response for a player should be 'all', 'none', 'nr' (no reply)
or a comma separated list of {CAN} PLAY DATES using the month/day
format. Asterisks can be appended to dates in which the player
wants to be listed as a sub, e.g., '{DATES[0]}, {DATES[2]}*, {DATES[3]}'.

dates: {wrap_format(", ".join(DATES))}
player tag: {PLAYER_TAG}
"""
    )

    changes = ""
    while again:
        if changes:
            clear_screen(default_project)
            save_project(default_project, yaml_data)
            print(f"saved changes: {changes}")
            changes = ""
            # show responses recorded thus far
            count = 0
            colored(f"Responses are for {CAN} PLAY dates", "DarkOrange")
            for key, value in RESPONSES.items():
                if value == "nr":
                    count += 1
                    colored(f"{key}: {value}", "Gold")
                else:
                    colored(f"{key}: {value}", "LightSkyBlue")
                    # print(f'{key}: {value}')
            if count:
                colored(f"not yet responded: {count}", "DarkOrange")
            continue

        print(f"""{divider}
- to record a response             enter the player's name (TAB accepts completion)
- to review current responses      enter ?
- to stop recording responses      enter .\
""")
        player = prompt("player: ", completer=players).strip()
        if player == ".":
            again = False
            continue
        if player == "?":
            # show responses recorded thus far
            clear_screen(default_project)
            colored(f"Responses are for {CAN} PLAY dates", "DarkOrange")
            count = 0
            for key, value in RESPONSES.items():
                if value == "nr":
                    count += 1
                    colored(f"{key}: {value}", "Gold")
                else:
                    colored(f"{key}: {value}", "LightSkyBlue")
            if count:
                colored(f"not yet responded: {count}", "DarkOrange")
            continue

        if player not in RESPONSES:
            print(f"{player} not found, continuing ...")
            continue
        else:
            original_value = RESPONSES[player]
            default = normalize_response_value(original_value)
            response = prompt(f"{player}: ", default=default)

            parsed_value, issues = parse_response_input(
                response,
                DATES,
                allow_last=ALLOW_LAST,
            )

            if issues:
                print(f"bad dates: {', '.join(issues)}")
            elif parsed_value is not None:
                RESPONSES[player] = parsed_value

            new = normalize_response_value(RESPONSES[player])
            if new != default:
                changes += f"  {player}: {new}\n"
        player = "?"

    return default_project


if __name__ == "__main__":
    sys.exit("plm.py should only be imported")
