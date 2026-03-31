# Player Lineup Manager

## History

Some variant of *plm* has been used privately since 2014 to schedule tennis doubles matches for a group of around 30 tennis players. Play for this group occurs weekly on Tuesdays using as many courts as necessary and the schedules are made for three months (one quarter) at a time. More recently, smaller Monday and Friday groups have been added each using at most one court. 

The process involves using *plm* for these steps.

- Press "c" to create a "project" by entering the year, quarter and weekday. E.g., for Tuesdays in the 3rd quarter of 2026, the corresponding values would be 2026, 3, and 1. (Weekday numbers begin with 0 for Monday.)
- Press "a" to generate an email asking players for their can/cannot play dates for the quarter.
- Press "r" to record player responses. Dates can be entered by choosing the player and then copy and pasting the dates from that player's email.
- When all responses have been received, press "s" to generate a schedule that 
  - randomly sorts available players for each date into groups of two (singles) or four (doubles) taking account of previous pairings. 
  - randomly selects from each group a 'captain' taking account of previous selections.
  - prepares a "user friendly" version of the schedule organized both by date and by player to email to the players. In addition to showing the players who are scheduled for each date, the scheduled also lists, with contact information, players who were not scheduled and might be available to substitute.
- Press "d" to deliver the completed schedule to the players.

Setup for using *plm* requires constructing a "roster" file lising players with their email addresses and tags indicating the weekdays on which they generally wish to play. 

*plm* is available from *PyPi*, [plm-dgraham](https://pypi.org/project/plm-dgraham/), and from *GitHub*, [dagraham/plm-dgraham](https://github.com/dagraham/plm-dgraham).

## Requirements

This program requires `python3`. To check for this requirement, open a terminal window and execute:

        ~ % which python3

If *python3* is installed the response should be something like

        /Library/Frameworks/Python.framework/Versions/3.10/bin/python3

and, otherwise,

        python3 not found

If *python3* is not installed, follow the appropriate installation procedure for your platform.

## Initial Setup

If *python3* is installed, the next step is to setup a *home directory* for *plm* to use when it starts. These are the options:

- If the current working directory contains a file 'roster.yaml' and a directory 'projects', then it will be used as the *home directory*.
- Otherwise if the environmental variable 'plmHOME' is set and points to a directory, then that directory will be used as the *home directory*.
- Otherwise `~/plm` will be used as the *home directory* and, with your permission, created if it does not already exist.

When *plm* is started for the first time, a sub-directory called `projects` and a file called `roster.yaml` will be created in the *home directory* if they do not already exist.

## Installation

### For personal use

The easiest way to install *plm* for personal use is to use *pip*. First update the python package manager, *pip*, using python3

        ~ % python3 -m pip install -U pip

and then install *plm* itself

        ~ % python3 -m pip install -U plm-dgraham

This will install *plm* and any needed supporting python modules. The same command can be used to update *plm* when a new version becomes available.

If you need to install a dependency manually, note that Python package names can differ between installation and import. For example, install `prompt-toolkit` but import `prompt_toolkit`.

### For use in a virtual environment

Using a virtual environment is a reliable approach, especially on macOS. For local development or testing, create and activate a virtual environment and then install *plm*:

    $ python3 -m venv .venv
    $ . .venv/bin/activate
    $ python3 -m pip install --upgrade pip
    $ python3 -m pip install -e .

If you only need a single dependency in an already activated virtual environment, e.g., `prompt_toolkit`, use:

    $ python3 -m pip install prompt-toolkit

### For use with uv

If you use `uv`, a typical development workflow is:

    $ uv venv
    $ uv sync
    $ uv run plm

### For use in an isolated application environment with pipx

Installing plm in an isolated environment is also possible with *pipx*. Begin by using *pip* to install *pipx*:

    $ python3 -m pip install -U pipx

Now run:

    $ pipx ensurepath

to ensure that directories necessary for *pipx* operation are in your PATH environment variable and finally to install *plm* itself:

    $ pipx install plm-dgraham

To upgrade *plm* when a new version becomes available, simply replace "install" in this command with "upgrade".

## Starting *plm*

After installation, you can start *plm* with any of these:

    $ plm
    $ python3 -m plm
    $ python3 start_plm.py

*plm* does not take a home-directory path argument. Instead it determines the home directory in this order:

- If the current working directory contains both `projects` and `roster.yaml`, then the current working directory is used.
- Otherwise if the environment variable `plmHOME` is set and points to a directory, then that directory is used.
- Otherwise `~/plm` is used and will be created with your permission if it does not already exist.

You will then see something like this

and you will see something like this

        Player Lineup Manager (0.5.3)
        home directory: ~/plm
        project: The active project has not yet been chosen.
        Use command 'c' to create one or 'p' to select one.

        commands:
            h:  show this help message
            H:  show on-line documentation
            e:  edit 'roster.yaml' using the default text editor
            c:  create a new quarterly doubles project            (1)
            m:  modify an existing project                        (1)
            p:  select the active project from existing projects  (1)
            a:  ask players for their "can play" dates            (2)
            r:  record the "can play" responses                   (3)
            n:  nag players to submit can play responses          (4)
            s:  schedule play using the "can play" responses      (5)
            d:  deliver the schedule to the players               (6)
            v:  view the current settings of a project
            u:  check for an update to a later plm version
            q:  quit

        command:

This begins a loop in which *plm* waits for you to enter a command at the prompt, processes the command and, unless the command *q* (quit) is given, waits for your next command.

Note: the commands *a*, *r*, *s*, *d* and *v* begin with a request that you select the *active project* if you have not already done so with either *c* or *p*. Tab completion is available and, once a selection is made, this project becomes the *active project* for any further use of the commands in this group while the command loop continues.

When using command *c* to create a new project, *plm* can optionally prefill values from bundled templates and, for repeating template-based projects, derive quarter-specific defaults from either a year/month or a year/quarter entry.

### The Player Directory: roster.yaml

This file is the directory for the players in all of your projects. It should be populated with all the relevant players for a project before you create the project itself.

You can open `roster.yaml` in your favorite editor or use command *e*:

        command: e

to have *plm* open the file for you. Each line in the roster file should have the format

        lastname, firstname: [emailaddress,  tag1, tag2, ... ]

For example:

        Doaks, Steve: [stvdoaks321@gmail.com, mon, tue]
        Smith, John: [jsmith123@gmail.com, tue, fri]
        ...

When creating a new project, you will be prompted for the tag of the players to be included so that, in the above example, the tag `mon` would include only Steve, but the tag `tue` would include both Steve and John.

It is worth devoting some thought to the *tag* scheme you will use before you start adding players. My schedules involve groups that play on a particular week day so I tend to use tags for the week day that the group plays, e.g., `mon` for the group that plays on *Monday*. Note that tags are case sensitive so `mon`, `Mon` and `MON` are all different tags.


### A New Project From Start to Finish

#### 1. Create the project file

Start *plm*, if necessary, and use the *create project* command:

        command: c

This command now provides a streamlined quarterly doubles workflow. You will be prompted for:

- the year
- the quarter
- the integer weekday, where `0: Monday, 1: Tuesday, 2: Wednesday, 3: Thursday, 4: Friday, 5: Saturday`

The defaults for year and quarter are the year and quarter immediately following the current quarter. For example, in December 2026 the defaults would be year `2027` and quarter `1`.

From these entries, *plm* generates the complete project settings, including:

- `NAME`, e.g., `2026-3Q-TU`
- `TITLE`, e.g., `Tuesday Tennis 3rd Quarter 2026`
- `PLAYER_TAG`, e.g., `tue`
- `REPLY_BY`, set to 14 days before the first generated playing date, e.g., `2026/06/23`
- the quarterly weekday `DATES`

It also uses these defaults:

- `CAN: y`
- `NUM_COURTS: 0`
- `NUM_PLAYERS: 4`
- `ASSIGN_TBD: n`
- `ALLOW_LAST: n`

After generating the project, *plm* presents the resulting settings for review. You can then save the project as generated, cancel, or enter a line number to modify selected settings such as `YEAR`, `QUARTER`, `DAY`, `NAME`, `TITLE`, `PLAYER_TAG`, `REPLY_BY`, `CAN`, `NUM_COURTS`, `NUM_PLAYERS`, `ASSIGN_TBD` and `ALLOW_LAST`. The generated `DATES` are also displayed for review, but they are informational and are not modified directly.

#### 2. Modify an existing project

To modify an existing project, use:

        command: m

You will be prompted to select an existing project and then shown the same numbered review screen used for project creation. You can save the project as-is, cancel, or enter a line number to modify selected settings. If you change `YEAR`, `QUARTER` or `DAY`, the derived fields are regenerated automatically.

Command `v` shows the current project settings in the same spirit as the review screen. It displays `YEAR`, `QUARTER`, `DAY`, `NAME`, `TITLE`, `PLAYER_TAG`, `REPLY_BY`, `CAN`, `NUM_COURTS`, `NUM_PLAYERS`, `ASSIGN_TBD` and `ALLOW_LAST`, followed by the generated `DATES`.

The value of `CAN` in the project settings affects both the request for player dates and the interpretation of the dates:

- When `CAN == y` (the default) the request is for a list of dates on which the player **CAN** play.
- When `CAN == n` the request is for a list of dates on which the player **CANNOT** play.

#### 2. Request player dates

With the project file created, the next step is to request the "CAN" or "CANNOT" play dates from the players (depending upon the setting for `CAN`). To do this start *plm*, if necessary, and use the *ask* command:

        command: a

You will be advised to open your favorite email application and create a new, empty email. You will then be prompted to select the relevant project. Tab completion is available to choose the project you created in the previous step. When you have selected the project, you will then be advised that the relevant email addresses have been copied to the system clipboard. Paste these into the "To" section of your new email and then press *return* in *plm* to continue. You will next be advised that the relevant subject has been copied to the system clipboard. Paste this into the "Subject" section of your email and again press *return* in *plm* to continue. You will finally be advised that the body of the request email has been copied to the system clipboard for you to paste into your email. When you are satisfied with the result, you can send the completed email.


#### 3. Enter player responses

As you receive responses, you can start *plm*, if necessary, and use the *record* command:

        command: r

Again you will be prompted to choose the relevant project with tab completion available. This begins a loop in which you can choose a player using tab completion and then enter the player's response to the dates request. The response for a player can be 'all', 'none', 'nr' (no response) or a comma separated list of dates using the month/day format. Asterisks can be appended to dates in which the player wants to be listed as a sub, e.g., '10/4, 10/18*, 10/25' for can or cannot play on 10/4 or 10/25 (depending upon `CAN`) and might be able to subsitute on 10/18. This process continues until you enter a 'q' to end the loop and, if changes have been made, indicate whether or not you would like to save them. This entry process can be repeated as often as you like until you are satisfied that all responses have been correctly entered.

Hint: you can have *plm* running in a terminal window near your email program with the `r` command activated so that when you get a reply from say, Joe Smith, you can just enter "j" at the prompt to choose "Joe Smith" using auto completion and then enter his reply. This is handy because the replies will, at best, arrive sporadically.


#### 4. Process responses to create the schedule

Start *plm*, if necessary, and use the *schedule* command when you are satisfied that all player responses have been received and recorded.

        command: s

Again, you will be prompted to choose the relevant project using tab completion. The schedule will be processed and added to the project file without further input.


#### 5. Deliver the completed schedule to the players

This step involves the *deliver* command.

        command: d

As with the process for requesting "can play" dates, this prompts for the relevant project and then successively copies 1) the email addresses, 2) the subject and 3) the schedule itself to the system clipboard so that each can be pasted in turn into an email to be sent to the relevant players.

### Modifying an existing project

You might want to add a player to a project you've already created, update the email address of an existing player or make some other change to an existing project. To do this, first make any needed changes to `roster.yaml` using

        command: e

When adding new players or modifying the email addresses of existing players, the changes will be incorporated into an existing project in the next step. Also, any responses that have been recorded for existing players will be preserved in the next step. However, changing the *name* of an existing player will effectively *delete* the original player and then *add* the new player. Any "can play" response you might have recorded in the project under the original name of the player would be lost in the process.

When you've finished updating `roster.yaml`, the next step is to use the  *project* command

        command: p

You will again be prompted for the same information you entered when you first created the project, but this time your previous responses will be the defaults. With each prompt, you can simply press *enter* to accept your original entry or make any changes you like and then press *enter* to update the entry. When you have finished with each of the prompts, you will be asked for a final confirmation before modifying the original project file. As noted above, any "can play" responses that had previously been recorded in the project will be preserved for players whose names have not been changed.
