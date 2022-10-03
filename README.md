## Player Lineup Manager


### History

Some variant of *plm* has been used since 2014 to schedule tennis doubles matches for a group of around 30 tennis players. Play still occurs weekly on Tuesdays using as many courts as necessary and the schedules are made for a three months (one quarter) at a time. More recently, smaller Monday and Friday groups have been added each using at most one court. The process involves these steps.

- Obtain a list of the dates that each player can play.
- Randomly sort available players for each date into groups of four taking account of previous pairings.
- From each group, randomly select a 'captain' taking account of previous selections.
- Produce a "user friendly" version of the schedule organized both by date and by player.
- Send the completed schedule to each player.

The current version of this program automates each of the steps in this process and allows some flexibility in scheduling dates, indicating a willingness to be a substitute, specifying the number of players per court (doubles or singles), and so forth. A further change is that all information relevant to a project is now stored in a single, project file in *yaml* format with players's responses listing the dates that the player *can* play rather than the dates the player *cannot* play. A final change is that *plm* is now available both from *PyPi*, [plm-dgraham](https://pypi.org/project/plm-dgraham/), and from *GitHub*, [dagraham/plm-dgraham](https://github.com/dagraham/plm-dgraham).

### Requirements

The program requires `python3` which must be installed on your system. To check this open a terminal window and execute the following.

		~ % which python3

If python3 is installed the response should be something like

		/Library/Frameworks/Python.framework/Versions/3.10/bin/python3

and, otherwise,

		python3 not found

If *python3* is installed, the next step is to install *plm*. First update the python package manager, *pip*, using python3

        ~ % python3 -m pip install -U pip

and then install *plm* itself

        ~ % python3 -m pip install -U plm-dgraham

This will install *plm* and any needed supporting python modules. This same process is also used to update *plm* when a new version is available.


### Initial Setup


- A *home directory* is required when *plm* starts. These are the options:

	- If the current working directory contains a file 'roster.yaml' and a directory 'projects', then it will be used as the *home directory*.
	- Otherwise if the environmental variable 'plmHOME' is set and points to a directory, then that directory will be used as the *home directory*.
	- Otherwise `~/plm` will be used as the *home directory* and, with your confirmation, created if necessary.

	A sub-directory called `projects` and a file called `roster.yaml` will be created in the *home directory* if they do not already exist

- Invoking *plm* itself without any of the 'switches' gives something like

		~ % plm
		usage: plm [-h] [-r] [-p] [-q] [-e] [-s] [-d] [-v]

		Player Lineup Manager

		options:
		-h, --help      show this help message and exit
		-r, --roster    Open 'roster.yaml' using the default text editor
		-p, --project   Create a project
		-q, --query     Query players for their 'can play' dates
		-e, --enter     Enter players' responses for their 'can play' dates
		-s, --schedule  Create project schedule using 'can play' responses
		-d, --deliver   Deliver the completed schedule to the players
		-v, --version   check for an update to a later plm version

		home directory: ~/plm

- You can now open `roster.yaml` in your favorite editor or invoke

        ~ % plm -r

    to have *plm* open the file for you. Each line in the roster file should have the format

        lastname, firstname: [emailaddress,  tag1, tag2, ... ]

    For example:

        Doaks, Steve: [stvdoaks321@gmail.com, mon, tue]
        Smith, John: [jsmith123@gmail.com, tue, fri]
        ...

    My schedules involve groups that play on a particular week day so I tend to use tags for the week day that the group plays, e.g., `mon` for the group that plays on *Monday*. Note that tags are case sensitive so `mon`, `Mon` and `MON` are all different tags.

    When creating a new project, you will be prompted for the tag of the players to be included so that, in the above example, the tag `mon` would include only Steve, but the tag `tue` would include both Steve and John.

    It is worth devoting some thought to the *tag* scheme you will use at this stage - changes made now are much easier than when projects have been created that rely upon existing tags.



### A New Project From Start to Finish

#### 1. Create the project file

Invoke *plm* with the `-p`, create project, switch:

        ~ % plm -p

Then follow the on-line prompts to enter the project information. This information will be stored in a new file in the projects directory, `<project_name>.yaml`, where `<project_name>` is the name you provide for the project. A short name that sorts well and is suggestive is recommended, e.g., `2022-4Q-TU`.


#### 2. Request players' availability dates

With the project file created, the next step is to request the "can play" dates from the players. To do this, invoke *plm* with the `-q`, query players, switch:

        ~ % plm -q

You will be advised to open your favorite email application and create a new, empty email. You will then be prompted to select the relevant project. Tab completion is available to choose the project you created in the previous step. When you have selected the project, you will then be advised that the relevant email addresses have been copied to the system clipboard. Paste these into the "To" section of your new email and then press *return* in *plm* to continue. You will next be advised that the relevant subject has been copied to the system clipboard. Paste this into the "Subject" section of your email and again press *return* in *plm* to continue. You will finally be advised that the body of the request email has been copied to the system clipboard for you to paste into your email. When you are satisfied with the result, you can send the completed email.


#### 3. Enter player "can play" responses

As you receive responses, you can invoke *plm* with the `-e`, enter responses, switch to record them:

        ~ % plm -e

Again you will be prompted to choose the relevant project with tab completion available. This begins a loop in which you can choose a player using tab completion and then enter the player's response to the "can play" dates query. The response for a player can be 'all', 'none', 'nr' (no response) or a comma separated list of dates using the month/day format. Asterisks can be appended to dates in which the player wants to be listed as a sub, e.g., '10/4, 10/18*, 10/25' for can play on 10/4 or 10/25 and might be able to subsitute on 10/18. This process continues until you enter a 'q' to end the loop and, if changes have been made, indicate whether or not you would like to save them. This entry process can be repeated as often as you like until you are satisfied that all responses have been correctly entered.


#### 4. Process responses to create the schedule

Invoke *plm* with the `-s`, schedule, switch after all player responses have been received and recorded.

        ~ % plm -s

Again, you will be prompted to choose the relevant project using tab completion. The schedule will be processed and added to the project file with no need for further input.


#### 5. Deliver the completed schedule to the players

This step involves invoking *plm* with the `-d`, deliver, switch.

        ~ % plm -d

As with the process for requesting "can play" dates, this prompts for the relevant project and then successively copies 1) the email addresses, 2) the subject and 3) the schedule itself to the system clipboard so that each can be pasted in turn into an email to be sent to the relevant players.

### Modifying an existing project

You might want to add a player to a project you've already created, update the email address of an existing player or make some other change to an existing project. To do this, first make the needed changes to `roster.yaml` using

        ~ % plm -r

When adding new players or modifying the email addresses of existing players, the changes will be incorporated into an existing project in the next step. Changing the *name* of an existing player, however, will effectively delete the original player and add the new player in the next step. Any "can play" response you might have recorded under the original name would be lost in this process.

When you've finished updating `roster.yaml`, invoke *create project* with the `-p` switch

        ~ % plm -p

and select (using tab completion) the project you want to update. You will be prompted for the same information as when you first created the project, but this time your previous responses will be the defaults. In each case, you can simply press *enter* to accept the default or make any changes you like and then press *enter* to record the changes.
