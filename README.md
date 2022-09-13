# Player Lineup Manager

## History

Some variant of these scripts have been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on the same weekday and time and the schedules are made for a three months (one quarter) at a time. This process involves these steps.

1. Email a request for the dates that the player cannot play to each player.
2. When the responses have been received, randomly sort available players for each date into groups of 4 taking account of previous pairings.
3. From each group, randomly select a 'captain' taking account of previous selections.
4. Email both group and individual schedules to each player.


This program uses `python3` which must be installed on your system. To check this open a terminal window and execute the following.

		~ % which python3

The response would be

		`python3 not found`

if it is not installed and, otherwise, something like

		/Library/Frameworks/Python.framework/Versions/3.10/bin/python3


The two scripts in this program automate each of the steps in this process and allow some flexibility in scheduling dates, number of players per court (doubles or singles), et cetera.

- `create-project.py` prompts for the roster file *tag* which identifies the relevant players and other scheduling details and then creates a corresponding project directory with two files:
	- `letter.txt` contains the email addresses of the players, the subject and the body of an email to be sent requesting their "cannot play" dates. These can be copied and pasted into your favorite email application.
	- `responses.yaml` contains various details about the project together with a *responses* section with lines having the format

			lastname, firstname: nr

	as responses are received from players, the `nr` (no response) should be changed to refect the actual response.

- `make-schedule.py` is invoked when all the responses from the players have been recorded. This script performs steps 2 and 3 listed above to produce the schedule for the project, `schedule.txt`.

Both scripts can be run more than once but will warn if file is to be overwritten and ask permission to do so.


## Initial Setup

- open a terminal window. The prompt should look something like this:

        ~ %

- enter the following to create a directory to use for *plm*

        ~ % mkdir plm_root

    The name `plm_root` is used just for illustrative purposes - the name can be anything you like.

    Within this directory, create a sub-directory called `projects` and a file called `roster.yaml`:

        ~ % cd plm_root
        ~/plm_root % mkdir projects
        ~/plm_root % touch roster.yaml
        ~/plm_root % ls
        projects/  roster.yaml

- use your file manager to place a copy of the *plm* scripts `create-project.py`, `make-schedule.py` and `install_missing.sh` in the `plm_root` directory and then make them executable:

        ~/plm_root % chmod +x *.py *.sh
        ~/plm_root % ls
        projects/            install_missing.sh  roster.yaml
        create-projects.py*  make-schedule.py*

- install the needed python support files by invoking `install_missing.sh`:

		~/plm_root % ./install_missing.sh

- Next open `roster.yaml` in a text editor and add player information. Each line in the roster file should have the format

        lastname, firstname: [emailaddress,  tag1, tag2, ... ]

    For example:

        Doaks, Steve: [stvdoaks321@gmail.com, mon, tue]
        Smith, John: [jsmith123@gmail.com, tue, fri]
        ...

    My schedules involve groups that play on a particular week day so I tend to use tags for the week day that the group plays, e.g., `mon` for the group that plays on *Monday*.

    When creating a new project, you will be prompted for the tag of the players to be included so that, in the above example, the tag `mon` would included only Steve, but the tag `tue` would include both Steve and John.


## Creating a Project


- Change the working directory to `plm_root`, if necessary, and invoke `create-project.py`:

        ~/plm_root % ./create-project.py

    Then follow the on-line prompts to enter the project information.

    This script will create a new directory in `plm_root/projects` containing two files, `responses.yaml` and `letter.txt`. The later contains the email addresses of the players and the subject and body of an email to send to them requesting their "cannot play" dates. This is an illustration of the body of `letter.txt`:

    > It's time to set the schedule for these dates:

    >> 10/4, 10/11, 10/18, 10/25, 11/1, 11/8, 11/15, 11/22, 11/29, 12/6, 12/13, 12/20, 12/27

    > Please make a note on your calendars to let me have your cannot play dates from this list no later than 6PM on Saturday, September 17. I will suppose that anyone who does not reply by this date cannot play on any of the scheduled dates.
    >
    > It would help me to copy and paste from your email if you would list your cannot play dates on one line, separated by commas in the same format as the list above. E.g., using 10/11, not October 11.
    >
    > If you want to be listed as a possible substitute for any of these dates, then append asterisks to the relevant dates. If, for example, you cannot play on 10/4 and 10/25 but might be able to play on 10/18 and thus want to be listed as a substitute for that date, then your response should be:

    >> 10/4, 10/18*, 10/25

    > Alternative shortcut responses:

    > all: you cannot play on any of the dates - equivalent to a list with all of the dates
    >
    > sub: you want to be listed as a possible substitute on all of the dates - equivalent to a list of all of the dates with asterisks appended to each
    >
    > none: there are no dates on which you cannot play - equivalent to a list without any dates



    And this is an illustration of the relevant part of `reponses.yaml`:

	> RESPONSES:
	>>	Doaks, Steve: nr
	>>	Smith, John: nr
	>>	...

    The `nr` stands for "no response" (yet).

    As the responses from the players are received, they can be entered into `responses.yaml`.

		RESPONSES:
			Doaks, Steve: none
			Smith, John: [10/4, 10/18*, 10/25]
			...

    Notice the square brackets around the list of Smith's cannot play dates.

    Note: *yaml* files have a format that makes them both easy to edit and easy for programs, such as python, to read. The important thing to remember is that the indentions matter and that they always use *spaces* and not *tabs*.

- invoke `make-schedule.py` after all player responses have been received and recorded and follow the on-line prompts.

        ~/plm_root % ./make-schedule.py

    This script will create another file, `schedule.txt` in the project directory, containing the completed schedule to be emailed to the players. The list of email addresses can be copied from `letter.txt` and pasted into your email agent together with the body from `schedule.txt`.

	Here is an illustration of `schedule.txt`

    > TUESDAY TENNIS
    >
    > 1) The captain is responsible for reserving a court and providing
    > balls.
    > 2) A player who is scheduled to play but, for whatever reason,
    > cannot play is responsible for finding a substitute and for
    > informing the other three players in his group.
    >
    >
    > BY DATE
    >
    > 1) The player listed first in each 'Scheduled' group is the
    > captain for that group.
    > 2) 'Unscheduled' players for a date were available to play but were
    > not assigned. If you are among these available but unassigned
    > players, would you please reach out to other players, even
    > players from outside the group, before other plans are made to
    > see if a foursome could be scheduled? Email addresses are in
    > the 'BY PLAYER' section below for those in the group.
    > 3) 'Substitutes' for a date asked not to be scheduled but instead
    > to be listed as possible substitutes.
    >
    > Tue Oct 4
    > 	Scheduled
    > 	1: Steve Doaks, ...
    > 	2: ...
    > 	Unscheduled: ...
    > 	Substitutes: ...
    >
    > Tue Oct 11
    >   ...
    >
	> ...

    > BY PLAYER
    >
    > Scheduled dates on which the player is captain and available
    > dates on which a court is scheduled have asterisks.
    >
    > Steve Doaks: stvdoaks312@gmail.com
    > 	SCHEDULED (3): 10/4*, 10/11, ...
    > 	available (13): 10/4*, 10/11*, ...
    > 	unavailable (0):
    > 	substitute (0): none
    > 	with: John Smith 2, ...
    >
    > John Smith: jsmith123@gmail.com
    > 	...
    >
	> ...
    >
    >
    > SUMMARY
    >
    > Times unscheduled/times available and others scheduled: ...
    >
    > Times captain/times scheduled: ...
    >
    > Scheduled dates (13): 10/4, 10/11, 10/18, 10/25, 11/1, 11/8, 11/15,
    > 		11/22, 11/29, 12/6, 12/13, 12/20, 12/27

