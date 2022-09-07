#!/usr/bin/env python3
help = """
Usage:

    $ create-schedule.py

Should be executed in a directory containing "responses.yaml"

The processed schedule will be saved to schedule.txt.
"""

import sys
import os
import random, re
from dateutil.rrule import *
from dateutil.parser import *
from datetime import *
from ruamel.yaml import YAML
yaml = YAML(typ='safe', pure=True)
import textwrap
from pprint import pprint
from collections import OrderedDict
# from icalendar import Calendar, Event, Todo
import uuid

leadingzero = re.compile(r'(?<!(:|\d|-))0+(?=\d)')

oneday = timedelta(days=1)
oneminute = timedelta(minutes=1)
onehour = timedelta(hours=1)

WIDTH = 70


WEEK_DAY = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat']


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
        talley.sort()
        new = talley[0][1]
        for name in chosen:
            freq[name][new] += 1
            freq[new][name] += 1
        chosen.append(new)
        remaining.remove(new)

    return freq, chosen, remaining


def makeSchedule(response_file):
    # file has the form <period>_responses.yaml
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

    fo = open(response_file, 'r')
    yaml_data = yaml.load(fo)
    fo.close()

    TITLE = yaml_data['TITLE']
    DAY = yaml_data['DAY']
    RESPONSES = yaml_data['RESPONSES']


    roster = f"../roster-{WEEK_DAY[DAY]}.yaml"
    if not os.path.exists(roster):
        print(f"Must be executed in the directory that contains '{roster}'.\nExiting")
        sys.exit()

    email_address = {}
    with open(roster, 'r') as fo:
        for line in fo.readlines():
            name, email = line.split(':')
            email_address[name] = email.strip()

    # get the roster
    NAMES = [x for x in RESPONSES.keys()]
    for name in NAMES:
        if name not in email_address:
            issues.append(f"{name} is missing from 'roster.yaml'")

    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        unselected[name] = 0
        opportunities[name] = 0
        available[name] = 0
        if RESPONSES[name] == 'na':
            notresponded.append(name)

    if notresponded:
        print("Not yet responded:\n  {0}\n".format("\n  ".join(notresponded)))

    schedule_name = f"./schedule.txt"

    BEGIN = parse(f"{yaml_data['BEGIN']} 12am")
    END = parse(f"{yaml_data['END']} 11pm")

    dates = [x.date() for x in list(rrule(WEEKLY, byweekday=DAY, dtstart=BEGIN, until=END))]
    DATES = [(dd.strftime("%m/%d"), dd.strftime("%a %b %d")) for dd in dates]

    NUM_COURTS = yaml_data['NUM_COURTS']

    schedule = OrderedDict({})

    # get available players for each date
    for name in NAMES:
        # initialize all the name counters
        captain[name] = 0
        notcaptain[name] = 0
        substitute[name] = 0
        available[name] = 0
        if RESPONSES[name] in ['na', 'all']:
            notavailable = [x.strip() for x in yaml_data['DATES'].split(",")]
            continue

        if RESPONSES[name] == 'sub':
            substitutedates[name] = [x.strip() for x in yaml_data['DATES'].split(",")]
            notavailable = []
        else:
            substitutedates[name] = [x[:-1] for x in RESPONSES[name] if x.endswith("*")]
            notavailable = [x for x in RESPONSES[name] if not x.endswith("*")]

        availabledates[name] = [x.strip() for x in yaml_data['DATES'].split(",")]

        for x in substitutedates[name] + notavailable:
            if x in availabledates[name]:
                availabledates[name].remove(x)
            else:
                issues.append("{0} listed for {1} is not an available date".format(x, name))

        unavailable[name] = notavailable

        for dd in dates:
            dstr = leadingzero.sub('', dd.strftime("%m/%d"))
            if dstr in availabledates[name]:
                availablebydates.setdefault(dstr, []).append(name)
                available[name] += 1
            elif dstr in substitutedates[name]:
                substitutebydates.setdefault(dstr, []).append(name)
                substitute[name] += 1

    num_dates = len(dates)

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
    dates.sort()
    for dd in dates:
        d = dd.strftime("%m/%d")
        dkey = leadingzero.sub('', d)
        courts = []
        substitutes = []
        unsched = []
        selected = availablebydates.get(dkey, [])
        possible = availablebydates.get(dkey, [])
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
            playerdates.setdefault(name, []).append(d)

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
                    captaindates.setdefault(court[j], []).append(dkey)
                else:
                    c = cp = ""
                    notcaptain[court[j]] += 1
            lst = []
            for court in courts:
                num, pstr = court.split(':')
                tmp = [x.strip() for x in pstr.split(',')]
                lst.append(tmp)
        dkey = dd.strftime("%m/%d")
        random.shuffle(lst)
        lst.append(unsched)
        schedule[dkey] = lst

    if issues:
        # print any error messages that were generated and quit
        for line in issues:
            print(line)
        return

    DATES_SCHED = [leadingzero.sub('', dd.strftime("%m/%d")) for dd in dates_scheduled]
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
    dates.sort()

    for d in dates:
        dd = d.strftime("%m/%d")
        dkey = leadingzero.sub('', d.strftime("%m/%d"))
        dtfmt = leadingzero.sub('', d.strftime("%a %b %d"))
        if not dd in schedule:
            continue
        avail = schedule[dd].pop()

        subs = [f"{x}" for x in substitutebydates.get(dkey, [])]
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
        output.append(f"{name}: {email_address.get(name, 'no email address')}")

        if name in playerdates:
            playerdates[name].sort()
            player_dates = [leadingzero.sub('', x) for x in playerdates[name]]

            available_dates = availabledates[name]
            for date in available_dates:
                if date in DATES_SCHED:
                    indx = available_dates.index(date)
                    available_dates[indx] = f"{date}*"

            if name in captaindates:
                captaindates[name].sort()
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
            elif RESPONSES[name] == 'na':
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
        unsel.sort()
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
        cap.sort()
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
    lines = textwrap.wrap(s, width=WIDTH, subsequent_indent="        ")
    for line in lines:
        print(line)


def wrap_format(s):
    lines = textwrap.wrap(s, width=WIDTH, subsequent_indent="        ")
    return "\n".join(lines)


if __name__ == "__main__":
    if os.path.isfile("./responses.yaml"):
        makeSchedule("./responses.yaml")
    else:
        print(help)
