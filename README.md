# Player Lineup Manager

## History

Some variant of this program has been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on Tuesdays using as many courts as necessary and the schedules are made for a three months (one quarter) at a time. More recently, smaller Monday and Friday groups have been added using at most one court. The process involved these steps.

- Obtain a list of the dates that each player can play.
- Randomly sort available players for each date into groups of 4 taking account of previous pairings.
- From each group, randomly select a 'captain' taking account of previous selections.
- Produce a "user friendly" version of the schedule organized both by date and by player.
- Send the completed schedule to each player.


This program uses `python3` which must be installed on your system. To check this open a terminal window and execute the following.

		~ % which python3

If python3 is installed the response should be something like

		/Library/Frameworks/Python.framework/Versions/3.10/bin/python3

and, otherwise,

		python3 not found

The current version of this program automates each of the steps in this process and allows some flexibility in scheduling dates, indicating a willingness to be a substitute, specifying the number of players per court (doubles or singles), and so forth. A further change is that all information relevant to a project is now stored in a single, project file in *yaml* format with players's responses listing the dates that the player *can* play rather than the dates the player *cannot* play. A final change is that *plm* is now available both from *PyPi*, [plm-dgraham](https://pypi.org/project/plm-dgraham/), and from *GitHub*, [dagraham/plm-dgraham](https://github.com/dagraham/plm-dgraham).

## Initial Setup

- open a terminal window. The prompt should look something like this:

        ~ %

- update the python installation module, *pip*, using python3

        ~ % python3 -m pip install -U pip

- and then *plm* itself

        ~ % python3 -m pip install -U plm-dgraham

    This will install *plm* and any needed supporting python modules. This same process can also be used to update *plm* when a new version is available.

- When *plm* is started, it needs to use a *home directory*. This home directory is determined as follows:

	- if the current working directory contains a file 'roster.yaml' and a directory 'projects', it will be used as the home directory for *plm*,
	- else if the environmental variable 'plmHOME' is set and points to a directory, then that directory will be used as the home directory for *plm*
	- else `~/plm` will be used as the home directory for *plm* and, after confirmation, created if it does not already exist.

	If necessary, a sub-directory called `projects` and a file called `roster.yaml` will be created in the home directory.

	In the examples below, it is assumed that `~/plm` is the home directory.


- invoking *plm* itself without any of the 'switches' gives something like

		~ % plm
		usage: plm [-h] [-r] [-p] [-q] [-e] [-s] [-d] [-v]

		Player Lineup Manager

		options:
		-h, --help      show this help message and exit
		-r, --roster    Open 'roster.yaml' using the default text editor to
						enter player names and email addresses
		-p, --project   Create a project (requires roster.yaml with names and
						email addresses of relevant players)
		-q, --query     Query players for their 'can play' dates (requires
						existing project)
		-e, --enter     Enter players' responses for their 'can play' dates
						(requires existing project)
		-s, --schedule  Process player 'can play' responses to create the
						project schedule (requires that player responses have
						been recorded)
		-d, --deliver   Deliver the completed schedule to the players
						(requires that project schedule has been processed)
		-v, --version   check for an update to a later plm version

- You can now open `roster.yaml` in your favorite editor or invoke

        ~ % plm -r

    to have *plm* open the file for you. Each line in the roster file should have the format

        lastname, firstname: [emailaddress,  tag1, tag2, ... ]

    For example:

        Doaks, Steve: [stvdoaks321@gmail.com, mon, tue]
        Smith, John: [jsmith123@gmail.com, tue, fri]
        ...

    My schedules involve groups that play on a particular week day so I tend to use tags for the week day that the group plays, e.g., `mon` for the group that plays on *Monday*.

    When creating a new project, you will be prompted for the tag of the players to be included so that, in the above example, the tag `mon` would included only Steve, but the tag `tue` would include both Steve and John.


## A New Project From Start to Finish

### 1. Create the project file

Change the working directory to `plm`, if necessary, and invoke *plm* with the `-p`, create project, switch:

        ~ % plm -p

Then follow the on-line prompts to enter the project information. This information will be stored in a new file, `plm/projects/<project_name>.yaml`, where `<project_name>` is the name you provide for the project. A short name that sorts well and is suggestive is recommended, e.g., `2022-4Q-TU`.

### 2. Request players' availability dates

With the project file created, the next step is to request the "can play" dates from the players. To do this, invoke *plm* with the `-q`, query players, switch:

        ~ % plm -q

You will be advised to open your favorite email application and create a new, empty email. You will then be prompted to select the relevant project. Tab completion is available to choose the project you created in the previous step. When you have selected the project, you will then be advised that the relevant email addresses have been copied to the system clipboard. Paste these into the "To" section of your new email and then press *return* in *plm* to continue. You will next be advised that the relevant subject has been copied to the system clipboard. Paste this into the "Subject" section of your email and again press *return* in *plm* to continue. You will finally be advised that the body of the request email has been copied to the system clipboard for you to paste into your email. The request step is complete when you have sent the completed email.


### 3. Enter player availability responses

To do this, invoke *plm* with the `-e`, enter responses, switch:

        ~ % plm -e

Again you will be prompted to choose the relevant project with tab completion available. This begins a loop in which you can choose a player using tab completion and then enter the player's response to the "can play" dates query. The response for a player can be 'all', 'none', 'nr' (no response) or a comma separated list of dates using the month/day format. Asterisks can be appended to dates in which the player wants to be listed as a sub, e.g., '10/4, 10/18*, 10/25' for can play on 10/4 or 10/25 and might be able to subsitute on 10/18. This process continues until you enter a 'q' to end the loop and, if changes have been made, indicate whether or not you would like to save them. This entry process can be repeated as often as you like until you are satisfied that all responses have been correctly entered.


### 4. Process responses to create the schedule

Invoke *plm* with the `-s`, schedule, switch after all player responses have been received and recorded.

        ~ % plm -s

Again, you will be prompted to choose the relevant project using tab completion. The schedule will be processed and added to the project file with no further input required.


### 5. Deliver the completed schedule to the players

This step involves invoking *plm* with the `-d`, deliver, switch.

        ~ % plm -d

As with the process for requesting "can play" dates, this prompts for the relevant project and then successively copies 1) the email addresses, 2) the subject and 3) the schedule itself to the system clipboard so that each can be pasted in turn into an email to be sent to the relevant players.
