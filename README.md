# README

## Issues

- Directory/File names and event titles
- Singles as well as doubles?
- Times as well as dates?
-



## The Problem

Suppose, for example, that a group of players would like to schedule tennis matches on Tuesdays in the 4th quarter of 2022.


A player may not be able to play on some of the relevant dates so the availablity of each player must be determined. Players also prefer to have variety in those with whom they play.

## Scripts

### 1. `create-event.py`

Inputs:

- Which file in `rosters` contains the names and addresses of the relevant players?
- How many courts are available for matches?
- How many players should be assigned to each court? (Usually 2 or 4)
- What dates (times) should be scheduled? One of the following:
    - a list of dates or datetimes.
    - a starting date (datetime), an ending date (datetime) and an recurrence rule specification.

### 2. `request-dates.py`

### 3. `create-schedule.py`

### 4. `send-schedules.py`

## initial setup
- create a directory to use for scheduling and, within it, subdirectories called rosters and schedules

        ~/scheduling
            rosters/
            schedules/

- put copies of scheduling scripts in this directory and make them executable
- create a subdirectory called `rosters` in your scheduling directory
- create a roster file in rosters for each event you will be scheduling with the names and email address of the players who will potentially be participating in the event
    e.g., ~/scheduling/rosters/tennis-tuesdays
    each line in this file should have the format `firstname lastname: emailaddress`

## Scheduling an event

- invoke `create-event.py`
    ~/scheduling
        rosters
        events

- Create directory for relevant file and cwd to this directory
    e.g., ~/tennis/2022-q4
- Create or add roster.yaml [list of "name: email address" lines]
- Run `create-template.py` to create "respones.yaml" and "letter.txt"
