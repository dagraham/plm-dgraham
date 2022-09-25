# Player Lineup Manager

## History

Some variant of this program has been used since 2014 to schedule tennis doubles matches for a group of around 30 players. Play takes place weekly on the same weekday and time and the schedules are made for a three months (one quarter) at a time. This process involves these steps.

- Obtain a list of the dates that each player cannot play.
- Randomly sort available players for each date into groups of 4 taking account of previous pairings.
- From each group, randomly select a 'captain' taking account of previous selections.
- Send the completed schedules to each player.


This program uses `python3` which must be installed on your system. To check this open a terminal window and execute the following.

		~ % which python3

The response would be

		python3 not found

if it is not installed and, otherwise, something like

		/Library/Frameworks/Python.framework/Versions/3.10/bin/python3

The current version of this program automates each of the steps in this process and allows some flexibility in scheduling dates, the number of players per court (doubles or singles), et cetera.

## Initial Setup

- open a terminal window. The prompt should look something like this:

        ~ %

- update the python installation module,  *pip*, using python3

        ~ % python3 -m pip install -U pip

- and then *plm* itself

        ~ % python3 -m pip install -U plm-dgraham

    This will install *plm* and any needed supporting python modules. This same process can also be used to update *plm* when a new version is available.

- invoking *plm* itself without any of the 'switches' gives something like

        ~ % plm
        usage: plm [-h] [-r] [-p] [-q] [-e] [-s] [-d] [-o] [-v]

        Player Lineup Manager [v 0.0.7]

        options:
          -h, --help      show this help message and exit
          -r, --roster    Open 'roster.yaml' using the default text editor to
                          enter player names and email addresses
          -p, --project   Create a project (requires roster.yaml)
          -q, --query     Query players for their cannot play dates (requires
                          project)
          -e, --enter     Enter player's responses for their cannot play dates
                          (requires project)
          -s, --schedule  Process player responses to create the project
                          schedule (requires project responses)
          -d, --deliver   Deliver the project schedule to the players (requires
                          project schedule)
          -o, --open      Open an existing project file using the default text
                          editor
          -v, --version   check for an update to a later plm version

        ~ % plm

- enter the following to create a directory to use for *plm*

        ~ % mkdir plm

    The name "plm" used for the directory is just for illustrative purposes - the directory name can be anything you like.

    Within this directory, create a sub-directory called `projects` and a file called `roster.yaml`:

        ~ % cd plm
        ~/plm % mkdir projects
        ~/plm % touch roster.yaml
        ~/plm % ls
        projects/  roster.yaml

- You can now open `roster.yaml` in your favorite editor or invoke

        ~ % plm -r

    to let *plm* open the file for you. Each line in the roster file should have the format

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

        ~/plm % plm -p

Then follow the on-line prompts to enter the project information. This information will be stored in a new file, `plm/projects/<project_name>.yaml`, where `<project_name>` is the name you provide for the project. A short name that sorts well and is suggestive is recommended, e.g., `2022-4Q-TU`.

### 2. Request cannot play dates

With the project file created, the next step is to request the cannot play dates from the players. To do this, invoke *plm* with the `-q`, query players, switch:

        ~/plm % plm -q

You will be advised to open your favorite email application and create a new, empty email. You will then be prompted to select the relevant project. Tab completion is available to choose the project you created in the previous step. When you have selected the project, you will then be advised that the relevant email addresses have been copied to the system clipboard. Paste these into the "To" section of your new email and then press <return> in *plm* to continue. You will next be advised that the relevant subject has been copied to the system clipboard. Paste this into the "Subject" section of your email and again press <return> in *plm* to continue. You will finally be advised that the body of the request email has been copied to the system clipboard for you to paste into your email. The request step is complete when you have sent the completed email.


### 3. Enter player cannot play responses

To do this, invoke *plm* with the `-e`, enter responses, switch:

        ~/plm % plm -e

Again you will be prompted to choose the relevant project with tab completion available. This begins a loop in which you can choose a player using tab completion and then enter the player's response. This process continues until you enter a 'q' to end the loop and, if changes have been made, you are asked whether or not you would like to save them.


### 4. Process responses to create the schedule

Invoke *plm* with the `-s`, schedule, switch after all player responses have been received and recorded. Again, you will be prompted to choose the relevant project using tab completion. The schedule will be processes and added to the project file with no further input required.

### 5. Deliver the completed schedule to the players

This step involves invoking *plm* with the `-d`, deliver, switch.

        ~/plm % plm -s

As with the process for requesting cannot play dates, this prompts for the relevant project and then successively copies 1) the email addresses, 2) the subject and 3) the schedule itself to the system clipboard so that each can be pasted in turn into an email to be sent to the relevant players.
