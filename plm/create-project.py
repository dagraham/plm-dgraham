#!/usr/bin/env python3

from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from ruamel.yaml import YAML
yaml = YAML(typ='safe', pure=True)
import os
import sys
import pendulum

# Create prompt object.
session = PromptSession()
cwd = os.getcwd()
problems = []
roster = os.path.join(cwd, 'roster.yaml')
if not os.path.exists(roster):
    problems.append(f"Could not find {roster}")
projects = os.path.join(cwd, 'projects')
if not os.path.exists(projects) or not os.path.isdir(projects):
    problems.append(f"Either {projects} does not exist or it is not a directory")
if problems:
    print(problems)
    sys.exit()


with open(roster, 'r') as fo:
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
of the projects directory: {projects}.
A short name that will sort in a useful way is suggested, e.g., `2022-4Q-TU`
for scheduling Tuesdays in the 4th quarter of 2022.\
""")
project_name = session.prompt("project name: ")
project = os.path.join(projects, project_name)
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
from {roster}.
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
# obtained from the file '{roster}'.
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
