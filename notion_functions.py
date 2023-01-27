import requests
import os
from filters import today_filter, tomorrow_filter
import pprint

printer = pprint.PrettyPrinter()
pprint = printer.pprint

# Notion Environment Variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_TASK_LIST = os.getenv("NOTION_TASK_LIST")
NOTION_PROJECTS_LIST = os.getenv("NOTION_PROJECTS_LIST")

cache = {}
priorities = ["High", "Medium", "Low"]


def get_event_content(event_id):
    url = "https://api.notion.com/v1/blocks/{}/children".format(event_id)
    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    return data["results"]


def get_event_data(event, projects):
    event_content = get_event_content(event["id"])
    if len(event_content) == 0:
        description = ""
    else:
        description = event_content[0]["paragraph"]["rich_text"][0]["plain_text"]
    event["properties"] = {
        str(key.encode("ascii", errors="ignore"))[2:-1].strip(): value
        for key, value in event["properties"].items()
    }
    project_ids = event["properties"]["Projects"]["relation"]
    project = "Personal Management"
    if len(project_ids) > 0:
        project = projects[project_ids[0]["id"]]
        project = project["properties"]["Project Name"]["title"][0]["plain_text"]
    priority = event["properties"]["Priority"]["select"]
    priority = priority["name"] if priority else "Low"
    priority = priorities.index(priority)
    try:
        work_block = event["properties"]["Work Block"]["multi_select"][0]["name"]
    except:
        work_block = "General"
    title = event["properties"]["Name"]["title"][0]["plain_text"]
    gcal_id = event["properties"]["gcal_id"]["rich_text"]
    gcal_id = "" if len(gcal_id) == 0 else gcal_id[0]
    date = event["properties"]["Goal Date"]["date"]["start"]
    created_time = event["properties"]["Created time"]["created_time"]
    est_time = 1
    est_time = event["properties"]["Estimated Time (hours)"]["number"]
    if len(event["properties"]["Parent item"]["relation"]) > 0:
        pid = event["properties"]["Parent item"]["relation"][0]["id"]
        if pid in cache:
            parent_event = cache[pid]
        else:
            parent_event = get_event_by_id(pid)
            cache[pid] = parent_event
        parent_title = get_event_data(parent_event, projects)["title"]
        title = "[{}] {}".format(parent_title, title)
    is_parent = len(event["properties"]["Sub-item"]["relation"]) > 0
    result = {
        "id": event["id"],
        "gcal_id": gcal_id,
        "is_parent": is_parent,
        "title": title,
        "date": date,
        "created_time": created_time,
        "estimate": est_time,
        "priority": priority,
        "project": project,
        "work_block": work_block,
        "description": description,
    }
    return result


def get_event_by_id(id_):
    url = "https://api.notion.com/v1/pages/{}".format(id_)

    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    return data


def get_notion_today():
    # Get all events for today and prior
    url = "https://api.notion.com/v1/databases/{}/query".format(NOTION_TASK_LIST)
    payload = {
        "page_size": 100,
        "filter": today_filter(),
    }
    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    events = data["results"]
    return events


def get_notion_projects():
    # Get all events for tomorrow and prior
    url = "https://api.notion.com/v1/databases/{}/query".format(NOTION_PROJECTS_LIST)
    payload = {
        "page_size": 100,
    }
    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    projects = {p["id"]: p for p in data["results"]}
    return projects


def get_notion_tomorrow():
    # Get all events for tomorrow and prior
    url = "https://api.notion.com/v1/databases/{}/query".format(NOTION_TASK_LIST)
    payload = {
        "page_size": 100,
        "filter": tomorrow_filter(),
    }
    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    events = data["results"]
    return events


def get_notion_events(today=True):
    projects = get_notion_projects()
    if today:
        events = get_notion_today()
    else:
        events = get_notion_tomorrow()
    event_data = [
        e
        for e in sorted(
            [get_event_data(e, projects) for e in events],
            key=lambda x: (
                x["priority"],
                float(x["estimate"]),
                x["date"],
                x["created_time"],
            ),
        )
        if not e["is_parent"]
    ]
    return event_data


def update_notion_event(notion_id, gcal_id, gcal_link):
    url = "https://api.notion.com/v1/pages/{}".format(notion_id)
    payload = {
        "properties": {
            "gcal_id": {
                "rich_text": [
                    {
                        "type": "text",
                    }
                ]
            },
        }
    }
    if not gcal_id or not gcal_link:
        payload["properties"]["gcal_id"]["rich_text"] = []

    else:
        payload["properties"]["gcal_id"]["rich_text"] = [
            {
                "type": "text",
                "plain_text": gcal_id,
                "text": {
                    "content": "Google Calendar Link",
                    "link": {"url": gcal_link},
                },
            }
        ]
    headers = {
        "accept": "application/json",
        "Notion-Version": "2022-06-28",
        "Authorization": "Bearer {}".format(NOTION_API_KEY),
        "content-type": "application/json",
    }

    response = requests.patch(url, json=payload, headers=headers)
