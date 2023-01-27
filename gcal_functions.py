import datetime
import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPESs, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SCHEDULING_CALENDAR_ID = os.getenv("SCHEDULING_CALENDAR_ID")
WORK_CALENDAR_ID = os.getenv("WORK_CALENDAR_ID")
CREDS_ROOT = os.getenv("GOOGLE_CREDENTIALS_BASE_DIR")


def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join(CREDS_ROOT, "token.json")):
        creds = Credentials.from_authorized_user_file(
            os.path.join(CREDS_ROOT, "token.json"), SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(CREDS_ROOT, "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.join(CREDS_ROOT, "token.json"), "w") as token:
            token.write(creds.to_json())
    return creds


def get_calendar_list():
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list["items"]:
            yield calendar_list_entry
        page_token = calendar_list.get("nextPageToken")
        if not page_token:
            break


def get_recent():
    creds = get_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId=SCHEDULING_CALENDAR_ID,
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        # Prints the start and name of the next 10 events
        for i, event in enumerate(events):
            if i < 1:
                print(event.keys())
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"], event["etag"])

    except HttpError as error:
        print("An error occurred: %s" % error)


def get_google_events(date_min, date_max):
    creds = get_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)
        page_token = None
        while True:
            events = (
                service.events()
                .list(
                    calendarId=SCHEDULING_CALENDAR_ID,
                    timeMin=date_min,
                    timeMax=date_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            for event in events["items"]:
                event_title = event["summary"] if "summary" in event else "busy"
                event_start = datetime.datetime.fromisoformat(
                    event["start"]["dateTime"]
                )
                event_end = datetime.datetime.fromisoformat(event["end"]["dateTime"])
                duration = int((event_end - event_start).total_seconds() / 60)
                event_start = {"hour": event_start.hour, "minute": event_start.minute}
                event_end = {"hour": event_end.hour, "minute": event_end.minute}
                yield {
                    "title": event_title,
                    "start": event_start,
                    "end": event_end,
                    "duration": duration,
                }
            page_token = events.get("nextPageToken")
            if not page_token:
                break

    except HttpError as error:
        print("An error occurred: %s" % error)

    try:
        service = build("calendar", "v3", credentials=creds)
        page_token = None
        while True:
            events = (
                service.events()
                .list(
                    calendarId=WORK_CALENDAR_ID,
                    timeMin=date_min,
                    timeMax=date_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            for event in events["items"]:
                event_title = event["summary"] if "summary" in event else "busy"
                event_start = datetime.datetime.fromisoformat(
                    event["start"]["dateTime"]
                )
                event_end = datetime.datetime.fromisoformat(event["end"]["dateTime"])
                duration = int((event_end - event_start).total_seconds() / 60)
                event_start = {"hour": event_start.hour, "minute": event_start.minute}
                event_end = {"hour": event_end.hour, "minute": event_end.minute}
                yield {
                    "title": event_title,
                    "start": event_start,
                    "end": event_end,
                    "duration": duration,
                }
            page_token = events.get("nextPageToken")
            if not page_token:
                break

    except HttpError as error:
        print("An error occurred: %s" % error)


def add_google_event(
    work_block, project_name, event_title, description, event_start, event_end
):
    BLOCK_TO_COLOR = {
        "Deep Work": 3,
        "Buffer Time": 7,
        "Review Time": 5,
        "Morning Focus": 7,
        "Weekly Reset": 4,
        "General Work Block": 2,
    }
    desc_items = [
        "{}: {}".format("Project", project_name),
        "{}: {}".format("Title", event_title),
    ]
    if description != "":
        desc_items.append("{}: {}".format("Notes", description))
    event = {
        "summary": work_block,
        "description": "\n".join(desc_items),
        "colorId": BLOCK_TO_COLOR[work_block] if work_block in BLOCK_TO_COLOR else 8,
        "start": {
            "dateTime": event_start,
            "timeZone": "America/New_York",
        },
        "end": {
            "dateTime": event_end,
            "timeZone": "America/New_York",
        },
        "reminders": {
            "useDefault": True,
        },
    }
    creds = get_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)
        event = (
            service.events()
            .insert(calendarId=SCHEDULING_CALENDAR_ID, body=event)
            .execute()
        )
        return event
    except HttpError as error:
        print("An error occurred: %s" % error)
        return error


def get_colors():
    creds = get_credentials()
    try:
        service = build("calendar", "v3", credentials=creds)
        colors = service.colors().get().execute()
        for id, color in colors["event"].items():
            print("colorId: %s" % id)
            print("  Background: %s" % color["background"])
            print("  Foreground: %s" % color["foreground"])
        return event
    except HttpError as error:
        print("An error occurred: %s" % error)
        return error


def delete_google_event(id_):
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)
    try:
        service.events().delete(
            calendarId=SCHEDULING_CALENDAR_ID, eventId=id_
        ).execute()
        return True
    except HttpError as error:
        print("An error occurred: %s" % error)
        return False
