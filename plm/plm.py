import argparse
import shutil
import requests
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import NestedCompleter


from ruamel.yaml import YAML
yaml = YAML(typ='safe', pure=True)
import os
import sys
import re
import pendulum

# for check_output
import subprocess

# for openWithDefault
import platform

leadingzero = re.compile(r'(?<!(:|\d|-))0+(?=\d)')

# oneday = timedelta(days=1)
# oneminute = timedelta(minutes=1)
# onehour = timedelta(hours=1)

# for wrap_print
COLUMNS, ROWS  = shutil.get_terminal_size()

# WEEK_DAY = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']


def openWithDefault(path):
    parts = [x.strip() for x in path.split(" ")]
    if len(parts) > 1:
        logger.debug(f"path: {path}")
        res =subprocess.Popen([parts[0], ' '.join(parts[1:])], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ok = True if res else False
    else:
        path = os.path.normpath(os.path.expanduser(path))
        logger.debug(f"path: {path}")
        sys_platform = platform.system()
        if platform.system() == 'Darwin':       # macOS
            res = subprocess.run(('open', path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif platform.system() == 'Windows':    # Windows
            res = os.startfile(path)
        else:                                   # linux
            res = subprocess.run(('xdg-open', path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # res = subprocess.run([cmd, path], check=True)
        ret_code = res.returncode
        ok = ret_code == 0
        logger.debug(f"res: {res}; ret_code: {ret_code}")
    if ok:
        logger.debug(f"ok True; res: '{res}'")
    else:
        logger.debug(f"ok False; res: '{res}'")
        show_message('goto', f"failed to open '{path}'")
    return

def edit_roster():
    openWithDefault(plm_roster)

def edit_project():
    project_hsh = {}
    possible = [x for x in os.listdir(plm_projects) if os.path.isdir(os.path.join(plm_projects, x))]

    for proj in possible:
        tmp = {}
        files = os.listdir(os.path.join(plm_projects, proj))
        for file in files:
            if file in ['letter.txt', 'responses.yaml', 'schedule.txt']:
                tmp[file] = None
        project_hsh[proj] = tmp if tmp else None
    completer = NestedCompleter.from_nested_dict(project_hsh)
    print(f"""
Press <space> to show completions for the project name and then again
for the file name.""")
    path_to_edit = prompt("project and file to edit: ", completer=completer)
    comp = [x.strip() for x in path_to_edit.split(' ') if x.strip()]
    rel_path = os.path.join(comp[0], comp[1])
    file_path = os.path.join(plm_projects, rel_path)

    if os.path.isfile(file_path):
        openWithDefault(file_path)
    else:
        print(f"'{file_path}' is not a file")

def main():

    parser = argparse.ArgumentParser(
            description=f"Player Lineup Manager [v {plm_version}]",
            prog='plm')

    parser.add_argument("-p", "--project",
            help="create a new project", action="store_true")

    parser.add_argument("-s", "--schedule",
            help="make the schedule for an existing project", action="store_true")

    parser.add_argument("-r", "--roster",
            help="open 'roster.yaml' using the default text editor", action="store_true")

    parser.add_argument("-o", "--open",
            help="Choose a project and file to open using the default text editor", action="store_true")


    # parser.add_argument("")

    parser.add_argument("-v",  "--version",
            help="check for an update to a later plm version", action="store_true")

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.version:
        res = check_update()
        print(res)
        return

    if args.project:
        create_project()
        return


    if args.schedule:
        make_schedule()
        return

    if args.roster:
        edit_roster()
        return

    if args.open:
        edit_project()
        return

    if args.add:
        tmp, *child = args.add.split(" ")
        idstr = tmp.split('-')[0]
        if child:
            child = '_'.join(child)
        Data.addID(idstr, child)

    if args.edit:
        ok, res = Data.editID(args.edit)
        if not ok:
            print(res)

def check_update():
    url = "https://raw.githubusercontent.com/dagraham/plm-dgraham/master/plm/__version__.py"
    try:
        r = requests.get(url)
        t = r.text.strip()
        # t will be something like "version = '4.7.2'"
        url_version = t.split(' ')[-1][1:-1]
        # split(' ')[-1] will give "'4.7.2'" and url_version will then be '4.7.2'
    except:
        url_version = None
    if url_version is None:
        res = "update information is unavailable"
    else:
        if url_version > plm_version:
            res = f"An update is available from {plm_version} (installed) to {url_version}"
        else:
            res = f"The installed version of plm, {plm_version}, is the latest available."

    return res



def create_project():
    # Create prompt object.
    session = PromptSession()
    problems = []
    if not os.path.exists(plm_roster):
        problems.append(f"Could not find {plm_roster}")
    if not os.path.exists(plm_projects) or not os.path.isdir(plm_projects):
        problems.append(f"Either {plm_projects} does not exist or it is not a directory")
    if problems:
        print(problems)
        sys.exit()

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
    tag_completer = WordCompleter(player_tags)


    print(f"""
    A name is required for the project. It will be used to create a sub-directory
    of the projects directory: {plm_projects}.
    A short name that will sort in a useful way is suggested, e.g., `2022-4Q-TU`
    for scheduling Tuesdays in the 4th quarter of 2022.\
    """)
    project_name = session.prompt("project name: ")
    project = os.path.join(plm_projects, project_name)
    if not os.path.exists(project):
        os.mkdir(project)
        print(f"created directory: {project}")
    else:
        print(f"using existing directory: {project}")


    responses_file = os.path.join(project, 'responses.yaml')
    letter_file = os.path.join(project, 'letter.txt')

    print(f"""
    A user friendly title is needed to use as the subject of emails sent
    to players initially requesing their "cannot play" dates and subsequently
    containing the schedules, e.g., `Tuesday Tennis`.""")

    title = session.prompt("project title: ")

    print(f"""
    The players for this project will be those that have the tag you specify
    from {plm_roster}.
    These tags are currently available: [{', '.join(player_tags)}].\
    """)
    tag = session.prompt(f"player tag: ", completer=tag_completer, complete_while_typing=True)
    while tag not in player_tags:
        print(f"'{tag}' is not in {', '.join(player_tags)}")
        print(f"Available player tags: {', '.join(player_tags)}")
        tag = session.prompt(f"player tag: ", completer=tag_completer, complete_while_typing=True)



    print(f"Selected players with tag '{tag}':")
    for player in players[tag]:
        print(f"   {player}")

    emails = [v for k, v in addresses.items()]

    print(f"""
    The letter sent to players asking for their "cannot play" dates will
    request a reply by 6pm on the "reply by date" that you specify next.\
            """)
    reply = session.prompt("reply by date: ", completer=None)
    rep_dt = parse(f"{reply} 6pm")
    print(f"reply by: {rep_dt}")



    print("""
    If play repeats weekly on the same weekday, playing dates can given by
    specifying the weekday and the beginning and ending dates. Otherwise,
    dates can be specified individually.
            """)
    repeat = session.prompt("Repeat weekly: ", default='yes')
    if repeat == 'yes':
        day = int(session.prompt("The integer weekday (0: Mon, 1: Tue, 2: Wed, 3: Thu, 4: Fri, 5: Sat): "))
        # rrule objects for generating days
        weekday = {0: MO, 1: TU, 2: WE, 3: TH, 4: FR, 5: SA}
        # Long weekday names for TITLE
        weekdays = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday'}
        WEEK_DAY = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        print(f"""
    Play will be scheduled for {weekdays[day]}s falling on or after the
    "beginning date" you specify next.""")
        beginning = session.prompt("beginning date: ")
        beg_dt = parse(f"{beginning} 12am")
        # print(f"beginning: {beg_dt}")
        print(f"""
    Play will also be limited to {weekdays[day]}s falling on or before the
    "ending date" you specify next.""")
        ending = session.prompt("ending date: ")
        end_dt = parse(f"{ending} 11:59pm")
        # print(f"ending: {end_dt}")
        days = list(rrule(WEEKLY, byweekday=weekday[day], dtstart=beg_dt, until=end_dt))
    else:
        print("""
    Playing dates separated by commas using year/month/day format. The current
    year is assumed if omitted.
    """)
        dates = session.prompt("Dates: ")
        days = [parse(f"{x} 12am") for x in dates.split(',')]

    numcourts = session.prompt("number of courts (0 for unlimited, else allowed number): ", default="0")
    numplayers = session.prompt("number of players (2 for singles, 4 for doubles): ", default="4")


    beginning_datetime = pendulum.instance(days[0])
    # print(f"beginning_datetime: {beginning_datetime}")
    beginning_formatted = beginning_datetime.format('YY-MM-DD')
    ending_datetime = pendulum.instance(days[-1])
    # print(f"ending_datetime: {ending_datetime}")
    ending_formatted = ending_datetime.format('YY-MM-DD')

    # title = f"{weekdays[day]} Tennis for {beginning_formatted} through {ending_formatted}"

    # dates will be in m/d format, e.g., 12/20, 12/27, 1/3 so only works for less than a year

    dates = ", ".join([f"{x.month}/{x.day}" for x in days])
    DATES = [x.strip() for x in dates.split(",")]

    rep_dt = pendulum.instance(parse(f"{reply} 6pm"))
    rep_date = rep_dt.format("hA on dddd, MMMM D")
    rep_DATE = rep_dt.format("hA on dddd, MMMM D, YYYY")

    eg_day = pendulum.instance(days[1])
    eg_yes = eg_day.format("M/D")
    eg_no = eg_day.format("MMMM D")

    tmpl = f"""# created by create-project.py
    TITLE: {title}
    NUM_COURTS: {numcourts}
    NUM_PLAYERS: {numplayers}
    BEGIN: {beginning_formatted}
    DAY: {day}
    END: {ending_formatted}
    DATES: [{dates}]

    # The names used as the keys in RESPONSES below were
    # obtained from the file '{plm_roster}'.
    # Responses are due by {rep_DATE}.

    """


    lttr_tmpl = f"""\
    ==== Addresses ====
    {", ".join(emails)}

    ==== Subject ====
    {title}

    ==== Body ====
    It's time to set the schedule for these dates:

        {dates}

    Please make a note on your calendars to let me have your cannot play dates from this list no later than {rep_date}. I will suppose that anyone who does not reply by this date cannot play on any of the scheduled dates.

    It would help me to copy and paste from your email if you would list your cannot play dates on one line, separated by commas in the same format as the list above. E.g., using {eg_yes}, not {eg_no}.

    If you want to be listed as a possible substitute for any of these dates, then append asterisks to the relevant dates. If, for example, you cannot play on {DATES[0]} and {DATES[3]} but might be able to play on {DATES[2]} and thus want to be listed as a substitute for that date, then your response should be:

        {DATES[0]}, {DATES[2]}*, {DATES[3]}

    Short responses:

        none: there are no dates on which you cannot play - equivalent to a
            list without any dates

        all: you cannot play on any of the dates - equivalent to a list with
            all of the dates

        sub: you want to be listed as a possible substitute on all of the
            dates - equivalent to a list of all of the dates with asterisks
            appended to each


    Thanks,
    """


    response_rows = []
    email_rows = []
    for player in players[tag]:
        response_rows.append(f"{player}: nr\n")
        email_rows.append(f"{player}: {addresses[player]}\n")

    if not os.path.exists(letter_file) or session.prompt(f"'./{os.path.relpath(letter_file, cwd)}' exists. Overwrite: ", default="yes").lower() == "yes":
        os.makedirs(os.path.dirname(letter_file), exist_ok=True)
        with open(letter_file, 'w') as fo:
            fo.write(lttr_tmpl)
        print(f"Saved {letter_file}")
    else:
        print("Overwrite cancelled")

    if not os.path.exists(responses_file) or session.prompt(f"'./{os.path.relpath(responses_file, cwd)}' exists. Overwrite: ", default="yes").lower() == "yes":
        os.makedirs(os.path.dirname(responses_file), exist_ok=True)
        with open(responses_file, 'w') as fo:
            fo.write(tmpl)
            fo.write('RESPONSES:\n')
            for row in response_rows:
                fo.write(f"    {row}")
            fo.write('\nADDRESSES:\n')
            for row in email_rows:
                fo.write(f"    {row}")
        print(f"Saved {responses_file}")
    else:
        print("Overwrite cancelled")


def format_name(name):
    lname, fname = name.split(', ')
    return f"{fname} {lname}"

def select(freq = {}, chosen=[], remaining=[]):
    """
    Add players from remaining to chosen which have the lowest combined
    frequency with players in chosen
    """

    while len(chosen) < 4 and len(remaining) > 0:
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


def makeSchedule(project):
    possible = {}
    available = {}
    availabledates = {}
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
    layerdates = {}
    substitute = {}
    substitutedates = {}
    schedule = OrderedDict({})
    onlysubstitute = []
    notresponded = []
    dates_scheduled = []
    dates_notscheduled= []
    unavailable = {}
    responses = os.path.join(project, 'responses.yaml')
    schedule_name = os.path.join(project, 'schedule.txt')

    with open(responses, 'r') as fo:
        yaml_responses = yaml.load(fo)

    TITLE = yaml_responses['TITLE']
    DAY = yaml_responses['DAY']
    responses = yaml_responses['RESPONSES']
    addresses = yaml_responses['ADDRESSES']
    DATES = yaml_responses['DATES']

    RESPONSES = {format_name(k): v for k, v in responses.items()}
    ADDRESSES = {format_name(k): v for k, v in addresses.items()}

    roster = f"./roster.yaml"
    if not os.path.exists(roster):
        print(f"Must be executed in the directory that contains '{roster}'.\nExiting")
        sys.exit()

    # get the roster
    NAMES = [x for x in RESPONSES.keys()]

    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        unselected[name] = 0
        opportunities[name] = 0
        available[name] = 0
        if RESPONSES[name] in ['nr', 'na']:
            notresponded.append(name)

    if notresponded:
        print("Not yet responded:\n  {0}\n".format("\n  ".join(notresponded)))


    NUM_COURTS = yaml_responses['NUM_COURTS']

    # get available players for each date
    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        available[name] = 0
        # print(f"RESPONSES[{name}]: {RESPONSES[name]}")
        if RESPONSES[name] in ['na', 'nr', 'all']:
            availabledates[name] = []
            substitutedates[name] = []
            unavailable[name] = [x for x in DATES]
        elif RESPONSES[name] in ['none'] or len(RESPONSES[name]) == 0:
            availabledates[name] = [x for x in DATES]
            substitutedates[name] = []
            unavailable[name] = []
        elif RESPONSES[name] in ['sub']:
            availabledates[name] = []
            substitutedates[name] = [x for x in DATES]
            unavailable[name] = []
        else:
            availabledates[name] = [x for x in DATES]
            substitutedates[name] = [x[:-1] for x in RESPONSES[name] if x.endswith("*")]
            unavailable[name] = [x for x in RESPONSES[name] if not x.endswith("*")]

            for x in substitutedates[name] + unavailable[name]:
                if x in availabledates[name]:
                    availabledates[name].remove(x)
                else:
                    issues.append(f"availabledates[{name}]: {availabledates[name]}")
                    issues.append("{0} listed for {1} is not an available date".format(x, name))

        for dd in DATES:
            if dd in availabledates[name]:
                availablebydates.setdefault(dd, []).append(name)
                available[name] += 1
            elif dd in substitutedates[name]:
                substitutebydates.setdefault(dd, []).append(name)
                substitute[name] += 1

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
            num_courts = min(NUM_COURTS, len(selected)//4)
        else:
            num_courts = len(selected)//4

        if num_courts:
            dates_scheduled.append(dd)
        else:
            dates_notscheduled.append(dd)

        num_notselected = len(selected) - num_courts * 4 if num_courts else len(selected)

        if num_notselected:
            # randomly choose the excess players and remove them from selected
            grps = {}
            for name in selected:
                try:
                    grps.setdefault(unselected[name] / available[name], []).append(name)
                except:
                    print(f"available: {available}")
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
                selected.remove(name)
        else:
            unsched = []

        for name in selected:
            playerdates.setdefault(name, []).append(dd)

        if NUM_COURTS:
            num_courts = min(NUM_COURTS, len(selected)//4)
        else:
            num_courts = len(selected)//4

        if len(selected) >= 4:
            for name in unsched:
                unselected[name] += 1
                opportunities[name] += 1
            for name in possible:
                opportunities[name] += 1

        # pick captains for each court
        grps = {}
        for name in selected:
            try:
                grps.setdefault(captain[name] - notcaptain[name], []).append(name)
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
            freq, court, players = select(freq, court, players)
            random.shuffle(court)
            tmp = [(captain[court[j]]/(captain[court[j]] + notcaptain[court[j]] + 1), j) for j in range(4)]
            # put the least often captain first
            tmp.sort()
            court = [court[j] for (i, j) in tmp]
            courts.append("{0}: {1}".format(i+1, ", ".join(court)))
            for j in range(len(court)):
                if j == 0:
                    c = "*"
                    cp = " (captain)"
                    captain[court[j]] += 1
                    captaindates.setdefault(court[j], []).append(dd)
                else:
                    c = cp = ""
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
    schdatestr = "Scheduled dates ({0}): {1}".format(len(DATES_SCHED), ", ".join([x for x in DATES_SCHED])) if DATES_SCHED else "Scheduled dates: none"

    output = [format_head(TITLE)]

    note = """\
1) The captain is responsible for reserving a court and providing
   balls.
2) A player who is scheduled to play but, for whatever reason,
   cannot play is responsible for finding a substitute and for
   informing the other three players in his group.

"""

    output.append(note)

    section = 'By date'
    output.append(format_head(section))

    output.append("""\
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
""")

    for dd in DATES:
        # dd = d.strftime("%m/%d")
        # dkey = leadingzero.sub('', d.strftime("%m/%d"))
        d = parse(f"{dd} 12am")
        dtfmt = leadingzero.sub('', d.strftime("%a %b %d"))
        if not dd in schedule:
            continue
        avail = schedule[dd].pop()

        subs = [f"{x}" for x in substitutebydates.get(dd, [])]
        substr = ", ".join(subs) if subs else "none"
        availstr = ", ".join(avail) if avail else "none"

        courts = schedule[dd]

        output.append(f'{dtfmt}')
        if courts:
            output.append(f"    Scheduled")
            for i in range(len(courts)):
                output.append(wrap_format("      {0}: {1}".format(i + 1, ", ".join(courts[i]))))
        else:
            output.append(f"    Scheduled: none")
        output.append(wrap_format("    Unscheduled: {0}".format(availstr)))
        output.append(wrap_format("    Substitutes: {0}".format(substr)))
        output.append('')

    output.append('')
    section = 'By player'
    output.append(format_head(section))

    subs2avail = []
    cap2play = []
    output.append("""\
Scheduled dates on which the player is captain and available
dates on which a court is scheduled have asterisks.
""")
    for name in NAMES:
        if name not in RESPONSES:
            continue
        response = RESPONSES[name]
        if isinstance(response, list):
            response = ', '.join(response) if response else 'none'
        output.append(f"{name}: {ADDRESSES.get(name, 'no email address')}")

        if name in playerdates:
            # playerdates[name].sort()
            player_dates = [x for x in playerdates[name]]

            available_dates = availabledates[name]
            for date in available_dates:
                if date in DATES_SCHED:
                    indx = available_dates.index(date)
                    available_dates[indx] = f"{date}*"

            if name in captaindates:
                # captaindates[name].sort()
                cptndates = [x for x in captaindates[name]]
                for date in cptndates:
                    indx = player_dates.index(date)
                    player_dates[indx] = f"{date}*"

            datestr = ", ".join(player_dates)
            availstr = ", ".join(available_dates)
            output.append(wrap_format("    SCHEDULED ({0}): {1}".format(len(player_dates), datestr)))
            output.append(wrap_format("    available ({0}): {1}".format(len(availabledates[name]), availstr)))


        if RESPONSES[name]:
            if RESPONSES[name] == 'all':
                ua = "all"
                un = num_dates
            elif RESPONSES[name] in ['na', 'nr']:
                ua = "no answer"
                un = num_dates
            elif RESPONSES[name] == 'sub':
                ua = "substitute only"
                un = 0
            else:
                ua = ", ".join(unavailable[name])
                un = len(unavailable[name])
            output.append(wrap_format("    unavailable ({0}): {1}".format(un,  ua)))

        if name in substitutedates:
            dates = substitutedates[name]
            datestr = ", ".join(dates) if dates else "none"
            output.append(wrap_format("    substitute ({0}): {1}".format(len(dates), datestr)))

        if name not in freq:
            continue
        tmp = []
        for other in NAMES:
            if other not in freq[name] or freq[name][other] == 0:
                continue
            tmp.append("{0} {1}".format(other, freq[name][other]))
        if tmp:
            output.append(wrap_format("    with: {0}".format(", ".join(tmp))))
        output.append('')

    output.append('')

    section = 'Summary'
    output.append(format_head(section))


    unsel = [(unselected[name], opportunities[name]) for name in opportunities if opportunities[name]]
    unsel_hsh = {}
    if unsel:
        unsel_lst = []
        for (n, x) in unsel:
            unsel_hsh.setdefault(str(n), []).append(str(x))
        for n in unsel_hsh:
            tmp_hsh = {i: unsel_hsh[n].count(i) for i in unsel_hsh[n]}
            tmp_lst = []
            for i in tmp_hsh:
                if tmp_hsh[i] > 1:
                    tmp_lst.append(f'{i}({tmp_hsh[i]})')
                else:
                    tmp_lst.append(f"{i}")
            unsel_lst.append(f"{n}/[{', '.join(tmp_lst)}]")
        output.append(wrap_format(f'Times unscheduled/times available and others scheduled*: {", ".join(unsel_lst)}'))

    cap = [(captain[name], captain[name] + notcaptain[name]) for name in available if available[name]]
    cap_hsh = {}
    if cap:
        cap_lst = []
        for (n, x) in cap:
            cap_hsh.setdefault(str(n), []).append(str(x))
        for n in cap_hsh:
            tmp_hsh = {i: cap_hsh[n].count(i) for i in cap_hsh[n]}
            tmp_lst = []
            for i in tmp_hsh:
                if tmp_hsh[i] > 1:
                    tmp_lst.append(f'{i}({tmp_hsh[i]})')
                else:
                    tmp_lst.append(f"{i}")
            cap_lst.append(f"{n}/[{', '.join(tmp_lst)}]")

        output.append('')
        output.append(wrap_format(f'Times captain/times scheduled: {", ".join(cap_lst)}'))

    output.append('')
    output.append(wrap_format(schdatestr))
    output.append('')

    output.append("""\
* An entry such as 2/[7(3)] would mean that there were 3 occasions
  in which i) a player was available 7 times when other players were
  scheduled and ii) the player was unscheduled 2 of those 7 times.
""")

    if not os.path.exists(schedule_name) or session.prompt(f"'{os.path.relpath(schedule_name, home)}' exists. Overwrite: ", default="yes").lower() == "yes":
        with open(schedule_name, 'w') as fo:
            fo.write("\n".join(output))
            print(f"updated {schedule_name}")


def print_head(s):
    print("{0}".format(s.upper()))
    print("="*len(s))


def format_head(s):
    return f"""\
{s.upper()}
{"="*len(s)}
"""


def wrap_print(s):
    lines = textwrap.wrap(s, width=COLUMNS, subsequent_indent="        ")
    for line in lines:
        print(line)


def wrap_format(s):
    lines = textwrap.wrap(s, width=COLUMNS, subsequent_indent="        ")
    return "\n".join(lines)


if __name__ == '__main__':
    sys.exit('plm.py should only be imported')

