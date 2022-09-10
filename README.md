# Player Lineup Manager

## History

Some variant of these scripts have been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on the same weekday and time and the schedules are made for a three months (one quarter) at a time. This process involves these steps.

1. Email a request for the dates that the player cannot play to each player.
2. When the responses have been received, randomly sort available players for each date into groups of 4 taking account of previous pairings.
3. From each group, randomly select a 'captain' taking account of previous selections.
4. Email both group and individual schedules to each player.

The four scripts in this program automate each of the steps in this process.

- `create-project.py` prompts for the name of a roster file with the names and email addresses of the players and other relevant details for the schedule and then creates a letter requesting dates to be mailed to the players and a responses file for recording their replies.

- `get-dates.py` sends the prepared letter to each of the players in the roster file.

- `make-schedules.py` is invoked when the responses from the players have been received to perform steps 2 and 3 above and produce the group and individual schedules.

- `send-schedules.py` sends the group and individual schedules to each of the players in the roster file.

## initial setup

- create a directory to use for *plm* and, within it, sub directories called rosters and schedules

        ~/plm-home
            rosters/
            schedules/

- create a subdirectory called `rosters` in your scheduling directory
- create a roster file in rosters for each event you will be scheduling with the names and email address of the players who will potentially be participating in the event
    e.g., ~/scheduling/rosters/tuesday.yaml
    each line in this file should have the format `firstname lastname: emailaddress`

## Schedule

- invoke `create-schedule.py`

- Create directory for relevant file and cwd to this directory
    e.g., ~/tennis/2022-q4
- Create or add roster.yaml [list of "name: email address" lines]
- Run `create-template.py` to create "respones.yaml" and "letter.txt"

