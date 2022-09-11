# Player Lineup Manager

## History

Some variant of these scripts have been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on the same weekday and time and the schedules are made for a three months (one quarter) at a time. This process involves these steps.

1. Email a request for the dates that the player cannot play to each player.
2. When the responses have been received, randomly sort available players for each date into groups of 4 taking account of previous pairings.
3. From each group, randomly select a 'captain' taking account of previous selections.
4. Email both group and individual schedules to each player.

The four scripts in this program automate each of the steps in this process and allow some flexibility in scheduling dates, number of players per court (doubles or singles), et cetera.

- `create-project.py` prompts for the roster file *tag* which identifies the relevant players and other scheduling details and then creates a corresponding project file.

- `get-dates.py` uses the contents of the project file to send a letter to each of the relevant players requesting their *cannot play* dates.

- `make-schedule.py` is invoked when the responses from the players have been recorded.  This script performs steps 2 and 3 listed above to produce the group and individual schedule for the project.

- `send-schedule.py` sends the group and individual schedules to each of the players in the roster file.

## Initial Setup

- create a directory to use for *plm* and, within it, a sub-directory called `projects` and a file called `roster.yaml`

        ~/plm-home
            projects/
            roster.yaml

Each line in the roster file should have the format

    lastname, firstname: [emailaddress,  tag1, tag2, ... ]

For example:

    Doaks, Steve: [stvdoaks321@gmail.com, mon, tue]
    Smith, John: [jsmith123@gmail.com, tue, fri]
    ...

When creating a new project, you will be prompted for the tag of the players to be included so that, in the above example, the tag *mon* would included only Steve, but the tag *tue* would include both Steve and John.


## Schedule

- invoke `create-schedule.py`

- Create directory for relevant file and cwd to this directory
    e.g., ~/tennis/2022-q4
- Create or add roster.yaml [list of "name: email address" lines]
- Run `create-template.py` to create "respones.yaml" and "letter.txt"

