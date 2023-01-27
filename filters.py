from datetime import datetime, timedelta


def get_today_ISO8601():
    today = datetime.now()
    iso_date = today.isoformat()
    return iso_date


def get_tomorrow_ISO8601():
    tomorrow = datetime.today() + timedelta(days=1)
    iso_date = tomorrow.isoformat()
    return iso_date


def today_filter():
    return {
        "and": [
            {"property": "Status", "status": {"does_not_equal": "Done"}},
            {
                "property": "Goal Date",
                "date": {
                    "on_or_before": get_today_ISO8601(),
                },
            },
        ]
    }


def tomorrow_filter():
    return {
        "and": [
            {"property": "Status", "status": {"does_not_equal": "Done"}},
            {
                "property": "Goal Date",
                "date": {
                    "after": get_today_ISO8601(),
                },
            },
            {
                "property": "Goal Date",
                "date": {
                    "on_or_before": get_tomorrow_ISO8601(),
                },
            },
        ]
    }
