import base64
import datetime
import pytz
import time

from daily_timeline import DailyTimeline
from gcal_functions import get_google_events, add_google_event, delete_google_event
from notion_functions import get_notion_events, update_notion_event

MIN_PER_HR = 60.0


def get_date_today():
    tz = "US/Eastern"
    dt = datetime.datetime.now()
    today = datetime.datetime(
        dt.year, dt.month, dt.day, 0, 0, 0, 0, tzinfo=pytz.timezone(tz)
    )
    return today


def get_today_delta(days, hours, minutes):
    dt = datetime.datetime.now()
    today_with_time = datetime.datetime(
        dt.year,
        dt.month,
        dt.day + days,
        hours,
        minutes,
        0,
        0,
    )
    return today_with_time.isoformat()


def add_day(curr_day, days=1):
    next_day = curr_day + datetime.timedelta(days=days)
    return next_day.isoformat()


def get_today():
    return get_date_today().isoformat()


def get_date_relative(days=1):
    return add_day(get_date_today(), days)


def get_tomorrow():
    return get_date_relative()


def schedule_notion_to_google(today=True, num_days=1, reschedule=False, delete=False):
    if today:
        delta_start = 0
    else:
        delta_start = 1
    for delta_days in range(delta_start, delta_start + num_days):
        day_start = get_date_relative(delta_days)
        day_end = get_date_relative(delta_days + 1)
        nevents = get_notion_events(day_start, day_end)
        projects = sorted(list(set([event["project"] for event in nevents])))
        projects = projects + ["Google"]
        total_hours = sum(e["estimate"] for e in nevents)
        if reschedule or delete:
            for event in nevents:
                title = event["title"]
                gcal_id = event["gcal_id"]
                if gcal_id != "":
                    print("Deleting old event: {}".format(title))
                    eid = str(
                        base64.b64decode(
                            gcal_id["text"]["link"]["url"].split("eid=")[-1]
                        )
                    )[2:-1].split()[0]
                    delete_google_event(eid)
                    update_notion_event(event["id"], None, None)
        if delete:
            continue

        print("Need to schedule {} hours of events.".format(total_hours))
        print("Projects today: {}".format(" ".join(projects)))

        gevents = get_google_events(day_start, day_end)
        timeline = DailyTimeline(projects=projects)
        for event in gevents:
            timeline.add_event(
                "General",
                event["title"],
                event["start"]["hour"] + event["start"]["minute"] / MIN_PER_HR,
                event["end"]["hour"] + event["end"]["minute"] / MIN_PER_HR,
            )

        for event in nevents:
            title = event["title"]
            gcal_id = event["gcal_id"]
            if gcal_id != "" and not reschedule:
                print("{} is already scheduled".format(event["title"]))
                continue
            estimate = event["estimate"]
            project = event["project"]
            work_block = event["work_block"]
            description = event["description"]
            smart_start = timeline.find_next_time(estimate)
            if smart_start:
                # Buffer time in the morning is morning focus. morning focus
                # in the afternoon is buffer time.
                if work_block == "Buffer Time" and smart_start < 11.5:
                    work_block = "Morning Focus"
                elif work_block == "Morning Focus" and smart_start > 11.5:
                    work_block = "Buffer Time"
                smart_end = smart_start + estimate
                days = delta_days
                hours = int(smart_start)
                minutes = int(smart_start % 1 * MIN_PER_HR)
                start_datetime = get_today_delta(days, hours, minutes)
                hours = int(smart_end)
                minutes = int(smart_end % 1 * MIN_PER_HR)
                end_datetime = get_today_delta(days, hours, minutes)
                new_event = add_google_event(
                    work_block,
                    project,
                    title,
                    description,
                    start_datetime,
                    end_datetime,
                )
                update_notion_event(event["id"], new_event["id"], new_event["htmlLink"])
                timeline.add_event(
                    project,
                    title,
                    smart_start,
                    smart_start + estimate,
                )
                print("Scheduled event: {}".format(title))
            else:
                print("Couldnt find a time. {} {}".format(title, estimate))
