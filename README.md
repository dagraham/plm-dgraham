# Player Lineup Manager

## History

Some variant of these scripts have been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on the same weekday and time and the schedules are made for a three months (one quarter) at a time. This process involves these steps.

1. Email a request for the dates that the player cannot play to each player.
2. When the responses have been received, randomly sort available players for each date into groups of 4 taking account of previous pairings.
3. From each group, randomly select a 'captain' taking account of previous selections.
4. Email both group and individual schedules to each player.

The four scripts in this program automate each of the steps in this process and allow some flexibility in scheduling dates, number of players per court (doubles or singles), et cetera.

- `create-project.py` prompts for the roster file *tag* which identifies the relevant players and other scheduling details and then creates a corresponding project directory with two files:
	- `letter.txt` contains the email addresses of the players, the subject and the body of an email to be sent requesting their "cannot play" dates. These can be copied and pasted into your favorite email application.
	- `responses.yaml` contains various details about the project together with a *responses* section with lines having the format

			lastname, firstname: na

	as responses are received from players, the `na` (no answer) should be changed to refect the actual response.

- `make-schedule.py` is invoked when all the responses from the players have been recorded. This script performs steps 2 and 3 listed above to produce the schedule for the project, `schedule.txt`.


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


## Creating a Project

- cwd to `plm-home`
- invoke `create-project.py`


