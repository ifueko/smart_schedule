# Second Brain Smart Scheduling: Notion + Google

## Usage
```
usage: second_brain.py [-h] [--today] [--days DAYS] [--reschedule] [--force]

options:
  -h, --help    show this help message and exit
  --today       start scheduling events today
  --days DAYS   number of days to schedule events
  --reschedule  reschedule events if already scheduled
  --force       don't ask for confirmation before rescheduling events
```

## Requirements
 - Python 3.7+ (tested with python 3.11)
 - installation of requirements `pip install -r reqirements.txt`
 - bashrc with API integration setup
```
# File: ~/.bashrc

standard file contents...

...
export GOOGLE_CREDENTIALS_BASE_DIR="/home/user/.second_brain_credentials" 
export NOTION_API_KEY="<< notion api key>>"
export NOTION_TASK_LIST="<< notion task list id >>"
export NOTION_PROJECTS_LIST="<< list of notion projects >>"
export SCHEDULING_CALENDAR_ID="<< schedule calendar id >>"
export WORK_CALENDAR_ID="<< work calendar id >>"
```

## Feature TODO
[x] Notion API Integration
[x] G-Cal API Integration
[x] Notion/G-Cal Sync
    [x] Add events formatted using worl block as title and content as event description
    [x] Adding Calendar Events from Notion that are not in google (gcal id is empty)
    [x] Rescheduling events option
[ ] Beter Optimization 
    [ ] Finding better start times?
    [ ] Gradient Descent using old calendar data?
    [ ] Total number of hours can be split up into blocks?
