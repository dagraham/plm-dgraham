import shutil
import requests
from dateutil.rrule import *
from dateutil.parser import parse, ParserError
from datetime import datetime, date
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession

# from prompt_toolkit.completion import WordCompleter
# from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.completion import FuzzyWordCompleter
from collections import OrderedDict
import pyperclip
from pprint import pprint
import calendar
from termcolor import colored

# import ruamel.yaml
from ruamel.yaml import YAML

import os
import sys
import re
import random

# TODO: add wrap text
import textwrap

# for check_output
import subprocess

# for openWithDefault
import platform

# yaml = YAML(typ='safe') # no round trip
yaml = YAML()   # round trip
yaml.indent(mapping=2, sequence=4, offset=2)
yaml.default_flow_style = None
leadingzero = re.compile(r'(?<!(:|\d|-))0+(?=\d)')

# for wrap_print
COLUMNS, ROWS = shutil.get_terminal_size()
COLUMNS -= 4

cwd = os.getcwd()


def zero_fill_sort(dd: [str]) -> [str]:
    l = []
    for d in dd:
        x = d.split('/')
        x[0] = f'{int(x[0]):02}'
        if x[1].endswith('*'):
            x[1] = f"{int(x[1].rstrip('*')):02}*"
        else:
            x[1] = f'{int(x[1]):02}'
        l.append(x)
    l.sort()
    return [f"{x[0].lstrip('0')}/{x[1].lstrip('0')}" for x in l]


def rel_path(path: str) -> str:
    userhome = os.path.expanduser('~')
    rpath = (
        os.path.join('~', os.path.relpath(path, userhome))
        if path.startswith(userhome)
        else path
    )
    return rpath


def wrap_text(text: str, init_indent: int = 0, subs_indent: int = 0):
    # Split the text into paragraphs (separated by newline characters)
    width = shutil.get_terminal_size()[0] - 2
    paragraphs = text.split('\n')

    # Wrap each paragraph separately
    wrapped_text = [
        textwrap.fill(
            paragraph,
            width,
            initial_indent=init_indent * ' ',
            subsequent_indent=subs_indent * ' ',
        )
        for paragraph in paragraphs
    ]

    # Join the wrapped paragraphs with newline characters
    return '\n'.join(wrapped_text)


def clear_screen(default_project=''):
    # Clearing the Screen
    # posix is os name for Linux or mac
    if os.name == 'posix':
        os.system('clear')
    # else screen will be cleared for windows
    else:
        os.system('cls')
    return default_project


def copy_to_clipboard(text):
    pyperclip.copy(text)
    print('copied to system clipboard')


def openWithDefault(path):
    parts = [x.strip() for x in path.split(' ')]
    if len(parts) > 1:
        # logger.debug(f"path: {path}")
        res = subprocess.Popen(
            [parts[0], ' '.join(parts[1:])],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ok = True if res else False
    else:
        path = os.path.normpath(os.path.expanduser(path))
        # logger.debug(f"path: {path}")
        sys_platform = platform.system()
        if platform.system() == 'Darwin':       # macOS
            res = subprocess.run(
                ('open', path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif platform.system() == 'Windows':    # Windows
            res = os.startfile(path)
        else:                                   # linux
            res = subprocess.run(
                ('xdg-open', path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # res = subprocess.run([cmd, path], check=True)
        ret_code = res.returncode
        ok = ret_code == 0
        # logger.debug(f"res: {res}; ret_code: {ret_code}")
    if ok:
        logger.debug(f"ok True; res: '{res}'")
    else:
        logger.debug(f"ok False; res: '{res}'")
        show_message('goto', f"failed to open '{path}'")
    # return


def get_project(default_project=''):
    # clear_screen()
    project = os.path.split(default_project)[1] if default_project else ''
    print('Select the active project.')
    possible = [
        x
        for x in os.listdir(os.path.expanduser(plm_projects))
        if os.path.splitext(x)[1] == '.yaml'
    ]
    possible.sort()
    completer = FuzzyWordCompleter(possible)
    proj = prompt('project: ', completer=completer, default=project).strip()
    proj = proj if proj.endswith('.yaml') else proj + '.yaml'
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
    current = ''
    confirm = False
    while again:
        result = prompt(f'{label}: ', completer=None, default=current)
        if not result:
            print('quitting ...')
            return None
        msg = ''
        dates = [x.strip() for x in result.split(',')]
        days = []
        current = ', '.join(dates)
        for i in range(len(dates)):
            md = dates[i]
            try:
                m_d = [int(x) for x in md.split('/') if x]
            except Exception as e:
                print(f'error: bad entry for month/day: {md}')
                continue
            if m_d[0] > 12:
                print(f'error: bad entry for month: {month}')
                continue
            yr = year + 1 if m_d[0] < month else year
            if len(m_d) == 1:   # month only
                print(calendar.month(yr, m_d[0]))
                confirm = False
            else:
                days.append(parse(f'{yr}/{md}', yearfirst=True))
                confirm = True   # enter pressed with mm/dd

        if confirm:
            print(f'dates: {current}')
            ok = prompt('Accept these dates: [Yn]').strip()
            if ok.lower() != 'n':
                return dates, days


def get_date(label='', default=''):
    help = """\
Enter a date using the format 'yyyy/mm/dd' or, to consult a calendar, enter 'yyyy/mm' to see a calendar showing the month or 'yyyy' to see a calendar for the entire year.\
"""
    again = True
    while again:
        print(wrap_text(help))
        result = prompt(f'{label}: ', completer=None, default=str(default))

        if not result:
            return None

        msg = ''
        parts = [x.strip() for x in result.split('/') if x]
        if len(parts) == 3:
            try:
                dt = parse(result, yearfirst=True)
            except ParserError as e:
                msg = f'error: {e}'
            else:
                return dt.strftime('%Y/%-m/%-d')
        elif len(parts) == 2:
            # year and month - show month
            try:
                year = (
                    int(parts[0])
                    if int(parts[0]) > 2000
                    else 2000 + int(parts[0])
                )
                month = int(parts[1])
                print(calendar.month(year, month))
                default = f'{year}/{month}'
            except Exception as e:
                msg = f'error: {e}'

        elif len(parts) == 1:
            # only year - show year
            try:
                year = (
                    int(parts[0])
                    if int(parts[0]) > 2000
                    else 2000 + int(parts[0])
                )
                print(calendar.calendar(year))
                default = f'{year}'
            except Exception as e:
                msg = f'error: {e}'

        else:
            msg = f'bad entry: {result}'

        if msg:
            print(msg)
            print(
                f"bad entry: {result}. Either 'yyyy/mm/dd', 'yyyy/mm' or 'yyyy' is required. Enter nothing to cancel."
            )

    return date


def edit_roster():
    openWithDefault(plm_roster)


def open_project(default_project=''):
    project = get_project(default_project)
    if project:
        openWithDefault(project)


def open_readme():
    help_link = 'https://dagraham.github.io/plm-dgraham/'
    openWithDefault(help_link)


def main():
    default_project = clear_screen(default_project='')
    project = '{default_project}' if default_project else 'not yet selected'

    commands = """
commands:
    h:  show this help message
    H:  show on-line documentation
    e:  edit 'roster.yaml' using the default text editor
    c:  create/update a project                           (1)
    p:  select the active project from existing projects  (1)
    a:  ask players for their "can play" dates            (2)
    r:  record the "can play" responses                   (3)
    n:  nag players to submit can play responses          (4)
    s:  schedule play using the "can play" responses      (5)
    d:  deliver the schedule to the players               (6)
    v:  view the current settings of a project
    u:  check for an update to a later plm version
    q:  quit
"""

    # help = f"""\
    # Player Lineup Manager ({plm_version})
    # home directory: {plm_home}
    # selected project: {project}
    # {commands}"""

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
            answer = input('command: ').strip()
            if answer not in 'clhevpnarsdouq?Ht':
                print(f"invalid command: '{answer}'")
                print(commands)
            elif answer in ['h', '?']:
                clear_screen()
            elif answer == 'H':
                open_readme()
            elif answer == 'u':
                res = check_update()
                print(f'\n{res}\n')
            elif answer == 'q':
                again = False
                print('quitting plm ...')
            elif answer == 't':
                default_project = get_project(default_project)
                toggle_can_play(default_project)
            else:
                if answer == 'e':
                    edit_roster()
                elif answer == 'o':
                    default_project = open_project(default_project)
                elif answer == 'v':
                    default_project = view_project(default_project)
                elif answer == 'c':
                    default_project = create_project(default_project)
                elif answer == 'p':
                    default_project = get_project(default_project)
                elif answer == 'a':
                    default_project = ask_players(default_project)
                elif answer == 'n':
                    default_project = nag_players(default_project)
                elif answer == 'r':
                    default_project = record_responses(default_project)
                elif answer == 's':
                    default_project = create_schedule(default_project)
                elif answer == 'd':
                    default_project = deliver_schedule(default_project)
                elif answer == 'l':
                    default_project = clear_screen(default_project)
                    # print(help)
                # if default_project:
                #     print(f"default project: {default_project}")

    except KeyboardInterrupt:
        play = False
        print('\nquitting plm ...')


def check_update():
    url = 'https://raw.githubusercontent.com/dagraham/plm-dgraham/master/plm/__version__.py'
    try:
        r = requests.get(url)
        t = r.text.strip()
        # t will be something like "version = '4.7.2'"
        url_version = t.split(' ')[-1][1:-1]
        logger.debug(f'url_version: {url_version}')
        # split(' ')[-1] will give "'4.7.2'" and url_version will then be '4.7.2'
    except:
        url_version = None
    if url_version is None:
        res = 'update information is unavailable'
    else:
        if url_version > plm_version:
            res = f'An update is available from {plm_version} (installed) to {url_version}'
        else:
            res = f'The installed version of plm, {plm_version}, is the latest available.'

    return res


def view_project(default_project=''):
    if not default_project:
        print('The first step is to select the project.')
        default_project = get_project(default_project)
        if not default_project:
            print('Cancelled')
            return

    with open(default_project) as fo:
        lines = fo.readlines()
    project_name = os.path.split(default_project)[1]
    border_length = min(18, (COLUMNS - len(project_name)) // 2)
    markers = '∨' * border_length
    clear_screen(default_project)
    print(colored(f'{markers} begin {project_name} {markers}', 'green'))
    # print(f'{markers}= begin {project_name} {markers}')
    print(''.join(lines).rstrip())
    markers = '∧' * border_length
    print(colored(f'{markers} end {project_name} {markers}\n', 'green'))

    return default_project


def create_project(default_project=''):
    clear_screen()
    session = PromptSession()
    problems = []
    if not os.path.exists(plm_roster):
        problems.append(f'Could not find {plm_roster}')
    if not os.path.exists(plm_projects) or not os.path.isdir(plm_projects):
        problems.append(
            f'Either {plm_projects} does not exist or it is not a directory'
        )
    if problems:
        print(f'problems: {problems}')
        sys.exit(problems)

    with open(plm_roster, 'r') as fo:
        roster_data = yaml.load(fo)

    tags = set([])
    players = {}
    addresses = {}
    for player, values in roster_data.items():
        addresses[player] = values[0]
        for tag in values[1:]:
            players.setdefault(tag, []).append(player)
            tags.add(tag)
    player_tags = [tag for tag in players.keys()]
    tag_completer = FuzzyWordCompleter(player_tags)

    ADDRESSES = {k: v for k, v in addresses.items()}

    print(
        wrap_text(
            f"""\
A name is required for the project. It will be used to create a file in the projects directory,
        {rel_path(plm_projects)}
combining the project name with the extension 'yaml'. A short name that will sort in a useful way is suggested, e.g., `2022-4Q-TU` for scheduling Tuesdays in the 4th quarter of 2022.\
    """
        )
    )
    # get_project would require an existing project - this allows for
    # creating a new project
    possible = [
        x
        for x in os.listdir(plm_projects)
        if os.path.splitext(x)[1] == '.yaml'
    ]
    possible.sort()
    completer = FuzzyWordCompleter(possible)
    proj = prompt(
        'project: ', completer=completer, default=default_project
    ).strip()
    if not proj:
        sys.exit('canceled')

    # userhome = os.path.expanduser('~')
    # projecthome = (
    #     os.path.join('~', os.path.relpath(etmdir, userhome))
    #     if etmdir.startswith(userhome)
    #     else etmdir
    # )

    project_name = os.path.join(plm_projects, proj)

    project_file = os.path.join(
        plm_projects, os.path.splitext(project_name)[0] + '.yaml'
    )
    default_project = project_file

    if os.path.exists(project_file):
        print(
            f'\nUsing defaults from the existing:\n        {rel_path(project_file)}\n'
        )
        ok = session.prompt(f'modify {rel_path(project_file)}: [Yn] ').strip()
        if ok.lower() == 'n':
            return default_project
        # get defaults from existing project file
        with open(project_file, 'r') as fo:
            yaml_data = yaml.load(fo)

        TITLE = yaml_data['TITLE']
        TAG = yaml_data['PLAYER_TAG']
        REPLY_BY = yaml_data['REPLY_BY']
        CAN = yaml_data.get('CAN', 'y')
        REPEAT = yaml_data['REPEAT']
        DAY = yaml_data['DAY']
        BEGIN = yaml_data['BEGIN']
        END = yaml_data['END']
        RESPONSES = yaml_data['RESPONSES']
        DATES = yaml_data['DATES']
        NUM_PLAYERS = yaml_data['NUM_PLAYERS']
    else:
        # set defaults when there is no existing project file
        TITLE = ''
        TAG = ''
        REPLY_BY = ''
        CAN = 'y'
        REPEAT = 'y'
        DAY = ''
        BEGIN = ''
        END = ''
        RESPONSES = {}
        DATES = []
        NUM_PLAYERS = ''

    print(
        wrap_text(
            f"""
A user friendly title is needed to use as the subject of emails sent to players initially requesing their availability dates and subsequently containing the schedules, e.g., `Tuesday Tennis 4th Quarter 2022`."""
        )
    )

    title = session.prompt('project title: ', default=TITLE).strip()
    if not title:
        sys.exit('canceled')

    print(
        wrap_text(
            f"""
The players for this project will be those that have the tag you specify from {rel_path(plm_roster)}. These tags are currently available: [{', '.join(player_tags)}].\
    """
        )
    )
    tag = session.prompt(
        f'player tag: ',
        completer=tag_completer,
        complete_while_typing=True,
        default=TAG,
    )
    while tag not in player_tags:
        print(f"'{tag}' is not in {', '.join(player_tags)}")
        print(f"Available player tags: {', '.join(player_tags)}")
        tag = session.prompt(
            f'player tag: ',
            completer=tag_completer,
            complete_while_typing=True,
        )

    print(f"Selected players with the tag '{tag}':")
    for player in players[tag]:
        print(f'   {player}')

    emails = [v for k, v in addresses.items()]

    print(
        wrap_text(
            f"""
The letter sent to players asking for their availability dates will request a reply by 6pm on the "reply by date" that you specify next.
"""
        )
    )
    # reply = session.prompt("reply by date: ", completer=None, default=str(REPLY_BY))
    reply = get_date('reply by date', default=str(REPLY_BY))
    if reply is None:
        print('cancelled')
        return None
    rep_dt = parse(f'{reply} 6pm')
    print(f"reply by: {rep_dt.strftime('%Y/%-m/%-d %-I%p')}")

    print(
        wrap_text(
            f"""
The letter sent to players asking for their availability dates will request a list either of dates they CAN play or dates they CANNOT play depending upon whether the answer to "interpret responses as can play dates" is Y or n.\
            """
        )
    )
    can_play = session.prompt(
        'interpret responses as CAN play dates: [Yn] ',
        completer=None,
        default=str(CAN),
    )
    can_play = can_play.lower()
    if can_play == 'n':
        print('interpreting responses as CANNOT play dates')
    else:
        print('interpreting responses as CAN play dates')

    print(
        wrap_text(
            """
If play repeats weekly on the same weekday, playing dates can given by specifying the weekday and the beginning and ending dates. Otherwise, dates can be specified individually.
"""
        )
    )
    repeat = (
        session.prompt('Repeat weekly: [Yn] ', default=REPEAT).lower().strip()
    )
    if repeat == 'y':
        day = int(
            session.prompt(
                'The integer weekday:\n    (0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat): ',
                default=str(DAY),
            )
        )
        # rrule objects for generating days
        weekday = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA}
        # long weekday names for TITLE
        weekdays = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
        }
        WEEK_DAY = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        print(
            wrap_text(
                f"""
Play will be scheduled for {weekdays[day]}s falling on or after the "beginning date" you specify next."""
            )
        )
        # beginning = session.prompt("beginning date: ", default=str(BEGIN))
        beginning = get_date('beginning date', str(BEGIN))
        if beginning is None:
            print('cancelled')
            return None
        beg_dt = parse(f'{beginning} 12am')
        print(f'beginning: {beg_dt}')
        print(
            wrap_text(
                f"""
Play will also be limited to {weekdays[day]}s falling on or before the "ending date" you specify next."""
            )
        )
        # ending = session.prompt("ending date: ", default=str(END))
        ending = get_date('ending date', str(END))
        if ending is None:
            print('cancelled')
            return None
        end_dt = parse(f'{ending} 11:59pm')
        print(f'ending: {end_dt}')
        days = list(
            rrule(WEEKLY, byweekday=weekday[day], dtstart=beg_dt, until=end_dt)
        )
    else:
        day = None
        dates, days = get_dates(
            label='Dates',
            year=rep_dt.year,
            month=rep_dt.month,
            default=', '.join(DATES),
        )

        print(f"using these dates:\n  {', '.join(dates)}")

    reply_formatted = rep_dt.strftime('%Y/%-m/%-d')
    beginning_datetime = days[0]
    beginning_formatted = beginning_datetime.strftime('%Y/%-m/%-d')
    ending_datetime = days[-1]
    ending_formatted = ending_datetime.strftime('%Y/%-m/%-d')
    byear = beginning_datetime.year
    eyear = ending_datetime.year
    if byear == eyear:
        years = f'{byear}'
    else:
        years = f'{byear} - {eyear}'

    dates = ', '.join([f'{x.month}/{x.day}' for x in days])
    num_dates = len(days)
    if num_dates == 0:
        print(f'ERROR. No dates were scheduled')
    elif num_dates >= 30:
        print(
            f'WARNING. An unusually large number of dates, {num_dates}, were scheduled. \nIs this what was intended?'
        )

    DATES = [x.strip() for x in dates.split(',')]
    numcourts = session.prompt(
        'number of courts (0 for unlimited, else allowed number): ',
        default='0',
    )
    numplayers = session.prompt(
        'number of players (2 for singles, 4 for doubles): ', default='4'
    )

    rep_dt = parse(f'{reply} 6pm')
    rep_date = rep_dt.strftime('%-I%p on %a, %b %-d')

    eg_day = days[1]
    eg_yes = eg_day.strftime('%-m/%-d')
    eg_no = eg_day.strftime('%b %-d')

    CAN = 'CAN' if can_play == 'y' else 'CANNOT'
    ALL = 'all' if can_play == 'y' else 'any'
    AND = 'and also' if can_play == 'y' else 'but'

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
    dates, then append asterisks to the relevant dates. If, for example,
    you {CAN.lower()} play on {DATES[0]} and {DATES[3]} {AND} want to be listed as a possible
    substitute on {DATES[2]}, then your response should be

        {DATES[0]}, {DATES[2]}*, {DATES[3]}

    Short responses:

        none: there are no dates on which you {CAN} play - equivalent to a
              list without any dates

        all:  you {CAN} play on {ALL} of the dates - equivalent to a
              list with all of the dates

        sub:  you want to be listed as a possible substitute on all of the
            dates - equivalent to a list of all of the dates with
            asterisks appended to each date

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
    you {CAN.lower()} play on {DATES[0]} and {DATES[3]} {AND} want to be listed as a possible
    substitute on {DATES[2]}, then your response should be

        {DATES[0]}, {DATES[2]}*, {DATES[3]}

    Short responses:

        none: there are no dates on which you {CAN} play - equivalent to a
              list without any dates

        all:  you CAN play on all of the dates - equivalent to a
              list with all of the dates

        sub:  you want to be listed as a possible substitute on all of the
              dates - equivalent to a list of all of the dates with
              asterisks appended to each date

    Thanks,

SCHEDULE: |
    Not yet processed

# The entries in ADDRESSES and the names in RESPONSES below
# correspond to those from the file '{plm_roster}' that
# were tagged '{tag}'.
"""

    response_rows = []
    email_rows = []
    for player in players[tag]:
        response = RESPONSES[player] if player in RESPONSES else 'nr'
        response_rows.append(f'{player}: {response}\n')
        email_rows.append(f'{player}: {ADDRESSES[player]}\n')

    if (
        not os.path.exists(project_file)
        or session.prompt(
            f'{rel_path(project_file)} exists. Overwrite: ',
            default='yes',
        ).lower()
        == 'yes'
    ):
        with open(project_file, 'w') as fo:
            fo.write(tmpl)
            fo.write('\nADDRESSES:\n')
            for row in email_rows:
                fo.write(f'    {row}')
            fo.write('\nRESPONSES:\n')
            for row in response_rows:
                fo.write(f'    {row}')
        print(f'Saved {project_file}')
    else:
        print('Overwrite cancelled')

    return default_project


def format_name(name):
    # used to get 'fname lname' from 'lname, fname' for the schedule
    lname, fname = name.split(', ')
    return f'{fname} {lname}'


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
                tmp += freq[other][name]
            talley.append([tmp, other])
        # talley.sort()
        new = talley[0][1]
        for name in chosen:
            freq[name][new] += 1
            freq[new][name] += 1
        chosen.append(new)
        remaining.remove(new)

    return freq, chosen, remaining


def toggle_can_play(default_project):
    """
    For testing. Toggle can_play between 'y' and 'no' and 'reverse'
    responses for players accordingly.
    """
    with open(default_project) as fo:
        yaml_data = yaml.load(fo)
    CAN = yaml_data.get('CAN', 'y')
    RESPONSES = yaml_data['RESPONSES']
    DATES = yaml_data['DATES']

    can_play = 'n' if CAN == 'y' else 'y'
    new_responses = {}
    for name in RESPONSES:
        if RESPONSES[name] == 'none':
            new_responses[name] = 'all'
            sub = []
        elif RESPONSES[name] == 'all':
            new_responses[name] = 'none'
            sub = []
        elif RESPONSES[name] == 'sub':
            new_responses[name] = 'sub'
            sub = [x for x in DATES]
        else:
            new_responses.setdefault(name, [])
            sub = [x for x in RESPONSES[name] if x.endswith('*')]
            other = [x for x in RESPONSES[name] if not x.endswith('*')]
            notother = [x for x in DATES if x not in other and x not in sub]
            new_responses[name] = zero_fill_sort(sub + notother)

    yaml_data['CAN'] = can_play
    yaml_data['RESPONSES'] = new_responses

    with open(default_project, 'w') as fn:
        # yaml.default_flow_style = None
        # yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(yaml_data, fn)
        print(f'Toggle applied to {default_project}')


def create_schedule(default_project=''):
    if not default_project:
        print('The first step is to select the project.')
        default_project = get_project(default_project)
        if not default_project:
            print('Cancelled')
            return
    with open(default_project) as fo:
        yaml_data = yaml.load(fo)

    possible = {}
    response = {}
    responsedates = {}
    availablebydates = {}
    substitutebydates = {}
    unselected = {}
    opportunities = {}
    captain = {}
    captaindates = {}
    courts = {}
    issues = []
    notcaptain = {}
    playerdates = {}
    substitute = {}
    substitutedates = {}
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

    TITLE = yaml_data['TITLE']
    responses = yaml_data['RESPONSES']
    addresses = yaml_data['ADDRESSES']
    DATES = yaml_data['DATES']
    NUM_PLAYERS = yaml_data['NUM_PLAYERS']
    # TAG = yaml_data['PLAYER_TAG']
    can = yaml_data['CAN'] == 'y'

    RESPONSES = {format_name(k): v for k, v in responses.items()}
    ADDRESSES = {format_name(k): v for k, v in addresses.items()}

    # get the roster
    NAMES = [x for x in RESPONSES.keys()]

    missing = [
        x
        for x in [TITLE, RESPONSES, ADDRESSES, DATES, NUM_PLAYERS, NAMES]
        if not x
    ]

    if missing:
        print(
            f"ERROR. The following required data fields were missing or empty in {proj_path}:\n {', '.join(missing)}"
        )
        return None

    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        unselected[name] = 0
        opportunities[name] = 0
        response[name] = 0
        if RESPONSES[name] in ['nr', 'na']:
            notresponded.append(name)

    if notresponded:
        print('Not yet responded:\n  {0}\n'.format('\n  '.join(notresponded)))

    NUM_COURTS = yaml_data['NUM_COURTS']

    # get response players for each date
    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        responsedates[name] = []
        substitutedates[name] = []
        response[name] = 0
        playerdates[name] = []
        if RESPONSES[name] in ['na', 'nr', 'none']:
            responsedates[name] = []
            substitutedates[name] = []
        elif RESPONSES[name] in ['all'] or len(RESPONSES[name]) == 0:
            responsedates[name] = [x for x in DATES]
            substitutedates[name] = []
        elif RESPONSES[name] in ['sub']:
            responsedates[name] = []
            substitutedates[name] = [x for x in DATES]
        else:
            for x in RESPONSES[name]:
                if x.endswith('*'):
                    substitutedates.setdefault(name, []).append(x[:-1])
                else:
                    responsedates[name].append(x)

            baddates = [
                x
                for x in responsedates[name] + substitutedates[name]
                if x not in DATES
            ]
            if baddates:
                issues.append(
                    f'responsedates[{name}]: {responsedates[name]}; substitutedates[{name}]: {substitutedates[name]}'
                )
                issues.append(f'  Not response dates: {baddates}')

        for dd in DATES:
            if dd in substitutedates[name]:
                substitutebydates.setdefault(dd, []).append(name)
                substitute.setdefault(name, 0)
                substitute[name] += 1
            elif can == (dd in responsedates[name]):
                availablebydates.setdefault(dd, []).append(name)
                response[name] += 1

    num_dates = len(DATES)
    freq = {}
    for name in NAMES:
        freq[name] = {}
    for name1 in NAMES:
        others = [x for x in NAMES if x != name1]
        for name2 in others:
            freq[name1].setdefault(name2, 0)
            freq[name2].setdefault(name1, 0)

    delta = 10

    # choose the players for each date and court
    for dd in DATES:
        courts = []
        substitutes = []
        unsched = []
        selected = availablebydates.get(dd, [])
        possible = availablebydates.get(dd, [])
        if NUM_COURTS:
            num_courts = min(NUM_COURTS, len(selected) // NUM_PLAYERS)
        else:
            num_courts = len(selected) // NUM_PLAYERS
        courts_scheduled[dd] = num_courts

        if num_courts:
            dates_scheduled.append(dd)
        else:
            dates_notscheduled.append(dd)

        num_notselected = (
            len(selected) - num_courts * NUM_PLAYERS
            if num_courts
            else len(selected)
        )

        if num_notselected:
            # at least one court =>
            # randomly choose the excess players and remove them from selected
            grps = {}
            for name in selected:
                # players who can play on this date
                try:
                    grps.setdefault(
                        unselected[name] / response[name], []
                    ).append(name)
                except:
                    print(f'response[{name}]: {response[name]}')
                    print(f'unselected[{name}]: {unselected[name]}')

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
                selected.remove(name)
        else:
            unsched = []

        for name in selected:
            playerdates.setdefault(name, []).append(dd)

        if NUM_COURTS:
            num_courts = min(NUM_COURTS, len(selected) // NUM_PLAYERS)
        else:
            num_courts = len(selected) // NUM_PLAYERS

        if len(selected) >= NUM_PLAYERS:
            for name in unsched:
                unselected[name] += 1
                opportunities[name] += 1
            for name in possible:
                opportunities[name] += 1

        # pick captains for each court
        grps = {}
        for name in selected:
            try:
                grps.setdefault(captain[name] - notcaptain[name], []).append(
                    name
                )
            except:
                print('except', name)

        nums = [x for x in grps]
        nums.sort()
        captains = []
        players = selected
        random.shuffle(players)
        lst = []
        for i in range(num_courts):
            court = []
            freq, court, players = select(freq, court, players, NUM_PLAYERS)
            random.shuffle(court)
            tmp = [
                (
                    captain[court[j]]
                    / (captain[court[j]] + notcaptain[court[j]] + 1),
                    j,
                )
                for j in range(NUM_PLAYERS)
            ]
            # put the least often captain first
            tmp.sort()
            court = [court[j] for (i, j) in tmp]
            courts.append('{0}: {1}'.format(i + 1, ', '.join(court)))
            for j in range(len(court)):
                if j == 0:
                    c = '*'
                    cp = ' (captain)'
                    captain[court[j]] += 1
                    captaindates.setdefault(court[j], []).append(dd)
                else:
                    c = cp = ''
                    notcaptain[court[j]] += 1
            lst = []
            for court in courts:
                num, pstr = court.split(':')
                tmp = [x.strip() for x in pstr.split(',')]
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

    scheduled = [f'{dd} [{courts_scheduled[dd]}]' for dd in dates_scheduled]

    schdatestr = (
        '{0} scheduled dates [courts]: {1}'.format(
            len(scheduled), ', '.join([x for x in scheduled])
        )
        if scheduled
        else 'Scheduled dates: none'
    )

    output = [format_head(TITLE)]

    note = """\
1) The captain is responsible for reserving a court and providing
   balls.
2) A player who is scheduled to play but, for whatever reason,
   cannot play is responsible for finding a substitute and for
   informing the other player(s) in the group.

"""

    output.append(note)

    section = 'By date'
    output.append(format_head(section))

    output.append(
        """\
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
"""
    )
    date_year = cur_year
    date_month = cur_month
    for dd in DATES:
        date_month, _ = [int(x) for x in dd.split('/')]
        if cur_month > date_month:
            date_year += 1
        cur_month = date_month

        d = parse(f'{date_year}/{dd} 12am')
        dtfmt = d.strftime('%a %b %-d')
        if not dd in schedule:
            continue
        avail = schedule[dd].pop()

        subs = [f'{x}' for x in substitutebydates.get(dd, [])]
        substr = ', '.join(subs) if subs else 'none'
        availstr = ', '.join(avail) if avail else 'none'

        courts = schedule[dd]

        output.append(f'{dtfmt}')
        if courts:
            output.append(f'    Scheduled')
            for i in range(len(courts)):
                output.append(
                    wrap_format(
                        '      {0}: {1}'.format(i + 1, ', '.join(courts[i]))
                    )
                )
        else:
            output.append(f'    Scheduled: none')
        output.append(wrap_format('    Unscheduled: {0}'.format(availstr)))
        output.append(wrap_format('    Substitutes: {0}'.format(substr)))
        output.append('')

    output.append('')
    section = 'By player'
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
            response = ', '.join(response) if response else 'none'
        output.append(f"{name}: {ADDRESSES.get(name, 'no email address')}")

        if RESPONSES[name]:
            if RESPONSES[name] == 'all':
                response = 'all'
            elif RESPONSES[name] in ['na', 'nr']:
                response = 'no reply'
            elif RESPONSES[name] == 'sub':
                response = 'sub'
            elif RESPONSES[name] == 'none':
                response = 'none'
            else:
                response = ', '.join(RESPONSES[name])

        playswith = []
        if name in freq:
            for other in NAMES:
                if other not in freq[name] or freq[name][other] == 0:
                    continue
                playswith.append('{0} {1}'.format(other, freq[name][other]))

        if name in playerdates:
            player_dates = [x for x in playerdates[name]]

            available_dates = availablebydates.get(name, [])
            for date in available_dates:
                if date in DATES_SCHED:
                    indx = available_dates.index(date)
                    available_dates[indx] = f'{date}*'

            if name in captaindates:
                cptndates = [x for x in captaindates.get(name, [])]
                for date in cptndates:
                    indx = player_dates.index(date)
                    player_dates[indx] = f'{date}*'

            datestr = ', '.join(player_dates)
            availstr = ', '.join(response)
            output.append(
                wrap_format(f'    scheduled ({len(player_dates)}): {datestr}')
            )
            if playswith:
                output.append(
                    wrap_format(
                        '    playing with: {0}'.format(', '.join(playswith))
                    )
                )
            output.append('    ---')
            output.append(wrap_format(f'    response: {response}'))
            if available_dates:
                output.append(
                    wrap_format(
                        '    response ({0}): {1}'.format(
                            len(response), availstr
                        )
                    )
                )

        if name in substitutedates and substitutedates[name]:
            dates = substitutedates[name]
            datestr = ', '.join(dates) if dates else 'none'
            output.append(
                wrap_format(
                    '    substitute ({0}): {1}'.format(len(dates), datestr)
                )
            )

        output.append('')

    output.append('')

    section = 'Summary'
    output.append(format_head(section))

    output.append(wrap_format(schdatestr))
    output.append('')

    schedule = '\n'.join(output)

    yaml_data['SCHEDULE'] = schedule

    with open(default_project, 'w') as fn:
        # yaml.default_flow_style = None
        # yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(yaml_data, fn)
        print(f'Schedule saved to {proj_path}')

    return default_project


def ask_players(default_project=''):
    if not default_project:
        print('The first step is to select the project.')
        default_project = get_project(default_project)
        if not default_project:
            print('Cancelled')
            return
    clear_screen()
    print(
        """
This will help you prepare an email to request can play dates
from the relevant players."""
    )

    with open(default_project) as fo:
        yaml_data = yaml.load(fo)

    print(
        """The next step is to
1) open your favorite email application,
2) create a new email and
3) be ready to paste
  (a) the addresses
  (b) the subject
  (c) the body
into the email. You will be prompted for each paste operation in turn.
"""
    )
    ADDRESSES = yaml_data['ADDRESSES']
    CAN = 'CAN' if yaml_data['CAN'] == 'y' else 'CANNOT'
    addresses = ', '.join([v for k, v in ADDRESSES.items()])
    copy_to_clipboard(addresses)

    print(
        """
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
"""
    )
    ok = prompt('Have the ADDRESSES been pasted? ', default='yes')

    if not ok == 'yes':
        print('Cancelled')
        return

    title = yaml_data['TITLE']
    copy_to_clipboard(f'{title} - {CAN} PLAY DATES REQUEST')

    print(
        """
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
"""
    )
    ok = prompt('Has the SUBJECT been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return

    request = yaml_data['REQUEST']
    copy_to_clipboard(request)

    print(
        """
The request has been copied to the system clipboard. When you
have pasted it into the "body" section of your email, your email
should be ready to send.
"""
    )
    ok = prompt('Has the BODY of the request been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return

    return default_project


def nag_players(default_project=''):
    print(
        """
This will help you prepare an email to nag players for their can
play dates from the relevant players."""
    )

    print('The first step is to select the project.')
    project = get_project(default_project)
    if not project:
        print('Cancelled')
        return
    default_project = os.path.split(project)[1]
    with open(project) as fo:
        yaml_data = yaml.load(fo)

    print(
        """The next step is to
1) open your favorite email application,
2) create a new email and
3) be ready to paste
  (a) the addresses
  (b) the subject
  (c) the body
into the email. You will be prompted for each paste operation in turn.
"""
    )
    ADDRESSES = yaml_data['ADDRESSES']
    RESPONSES = yaml_data['RESPONSES']
    addresses = ', '.join(
        [v for k, v in ADDRESSES.items() if RESPONSES[k] == 'nr']
    )
    copy_to_clipboard(addresses)

    print(
        """
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
"""
    )
    ok = prompt('Have the ADDRESSES been pasted? ', default='yes')

    if not ok == 'yes':
        print('Cancelled')
        return

    title = yaml_data['TITLE']
    copy_to_clipboard(f'{title} - CAN PLAY DATES REMINDER')

    print(
        """
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
"""
    )
    ok = prompt('Has the SUBJECT been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return

    request = yaml_data['NAG']
    copy_to_clipboard(request)

    print(
        """
The reminder has been copied to the system clipboard. When you
have pasted it into the "body" section of your email, your email
should be ready to send.
"""
    )
    ok = prompt('Has the BODY of the request been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return

    return default_project


def deliver_schedule(default_project=''):
    print(
        """
This will help you prepare an email to send the completed schedule
for a project to the relevant players."""
    )

    print('The first step is to select the project.')
    project = get_project(default_project)
    if not project:
        print('Cancelled')
        return default_project
    default_project = os.path.split(project)[1]
    with open(project) as fo:
        yaml_data = yaml.load(fo)

    print(
        """
The next step is to
(1) open your favorite email application
(2) create a new email and
(3) be ready to paste
    (a) the addresses
    (b) the subject
    (c) the body
into the email. You will be prompted for each paste operation in turn.
"""
    )

    ADDRESSES = yaml_data['ADDRESSES']
    addresses = ', '.join([v for k, v in ADDRESSES.items()])
    copy_to_clipboard(addresses)

    print(
        """
The email addresses for the relevant players have been copied
to the system clipboard. When you have pasted them into the "to"
section of your email, press <return> to continue to the next step.
"""
    )
    ok = prompt('Have the ADDRESSES been pasted? ', default='yes')

    if not ok == 'yes':
        print('Cancelled')
        return

    title = yaml_data['TITLE']
    copy_to_clipboard(f'{title} - Schedule')

    print(
        """
The email subject has been copied to the system clipboard. When you
have pasted it into the "subject" section of your email, press
<return> to continue to the next step.
"""
    )
    ok = prompt('Has the SUBJECT been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return

    schedule = yaml_data['SCHEDULE']
    copy_to_clipboard(schedule)

    print(
        """
The schedule has been copied to the system clipboard. When you
have pasted it into the "body" section of your email your email
should be ready to send.
"""
    )
    ok = prompt('Has the SCHEDULE been pasted? ', default='yes')
    if not ok == 'yes':
        print('Cancelled')
        return


def record_responses(default_project=''):
    if not default_project:
        print('The first step is to select the project.')
        default_project = get_project(default_project)
        if not default_project:
            print('Cancelled')
            return
    with open(default_project) as fo:
        yaml_data = yaml.load(fo)

    RESPONSES = yaml_data['RESPONSES']
    CAN = 'CAN' if yaml_data.get('CAN', 'y') == 'y' else 'CANNOT'
    DATES = yaml_data['DATES']
    PLAYER_TAG = yaml_data['PLAYER_TAG']

    players = FuzzyWordCompleter([x for x in RESPONSES] + ['.', '?'])

    again = True
    player_default = ''
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

    changes = ''
    while again:

        if changes:
            clear_screen(default_project)
            with open(default_project, 'w') as fn:
                yaml.dump(yaml_data, fn)
            print(f'saved changes: {changes}')
            changes = ''
            # show responses recorded thus far
            count = 0
            print(colored(f'Responses are for {CAN} PLAY dates', 'yellow'))
            for key, value in RESPONSES.items():
                if value == 'nr':
                    count += 1
                    print(colored(f'{key}: {value}', 'yellow'))
                else:
                    print(colored(f'{key}: {value}', 'green'))
                    # print(f'{key}: {value}')
            if count:
                print(colored(f'not yet responded: {count}', 'red'))
            continue

        print(
            "Enter player's name, '?' to review current responses\nor '.' to stop recording responses."
        )
        player = prompt('player: ', completer=players).strip()
        if player == '.':
            again = False
            continue
        if player == '?':
            # show responses recorded thus far
            clear_screen(default_project)
            print(colored(f'Responses are for {CAN} PLAY dates', 'yellow'))
            count = 0
            for key, value in RESPONSES.items():
                if value == 'nr':
                    count += 1
                    print(colored(f'{key}: {value}', 'yellow'))
                else:
                    print(colored(f'{key}: {value}', 'green'))
                    # print(f'{key}: {value}')
            if count:
                print(colored(f'not yet responded: {count}', 'red'))
            continue

        if player not in RESPONSES:
            print(f'{player} not found, continuing ...')
            continue
        else:
            default = RESPONSES[player]
            if isinstance(default, list):
                default = ', '.join(default)
            response = prompt(f'{player}: ', default=default)
            tmp = []
            if isinstance(response, str):
                response = response.strip().lower()
                if response in ['na', 'nr']:
                    RESPONSES[player] = 'nr'
                elif response == 'none':
                    RESPONSES[player] = 'none'
                elif response == 'all':
                    RESPONSES[player] = 'all'
                elif response == 'sub':
                    RESPONSES[player] = 'sub'
                else:   # comma separated list of dates
                    tmp = [x.strip() for x in response.split(',')]
            else:   # list of dates
                tmp = response
            if tmp:
                issues = []
                dates = []
                for x in tmp:
                    if x.endswith('*') and x[:-1] in DATES:
                        dates.append(x)
                    elif x in DATES:
                        dates.append(x)
                    else:
                        issues.append(x)
                if issues:
                    print(f"bad dates: {', '.join(issues)}")
                else:
                    RESPONSES[player] = dates

            new = RESPONSES[player]
            if isinstance(new, list):
                new = ', '.join(new)
            if new != default:
                changes += f'  {player}: {new}\n'
        player = '?'

    return default_project


def print_head(s):
    print('{0}'.format(s.upper()))
    print('=' * len(s))


def format_head(s):
    s = s.strip()
    return f"""\
{s.upper()}
{"="*len(s)}
"""


def wrap_print(s):
    lines = textwrap.wrap(s, width=COLUMNS, subsequent_indent='        ')
    for line in lines:
        print(line)


def wrap_format(s):
    lines = textwrap.wrap(s, width=COLUMNS, subsequent_indent='        ')
    return '\n'.join(lines)


if __name__ == '__main__':
    sys.exit('plm.py should only be imported')
