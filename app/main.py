import socket
from datetime import datetime, timedelta, timezone
from time import mktime
import time
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import feedparser
from pytz import timezone


# Default to 15min
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL_SECS', '60'))
FILTERS = os.environ.get('FILTERS', '')
PI_LOCATOR_TZ = os.environ.get('PI_LOCATOR_TZ', 'GMT')
LOCAL_TZ = os.environ.get('LOCAL_TZ', 'EST')

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#pi-notify')


FILTERS_ARRAY = []
slack_client = WebClient(token=os.environ['SLACK_TOKEN'])


def _getFiltersArray():
    global FILTERS_ARRAY

    if FILTERS != '':
        FILTERS_ARRAY = list(map(str.strip, FILTERS.split(',')))


def _convertTimezone(lastUpdate, tz):
    pre_tz = timezone(tz)
    pre_time = pre_tz.localize(lastUpdate, is_dst=None)
    return pre_time.astimezone(timezone(PI_LOCATOR_TZ))

def _getItemsForChannel(xmlUrl, lastUpdate):
    socket.setdefaulttimeout(60)

    parsed = feedparser.parse(xmlUrl)
    items = [entry for entry in parsed.entries if
             _convertTimezone(datetime.fromtimestamp(mktime(entry.updated_parsed)), PI_LOCATOR_TZ) > _convertTimezone(datetime.fromisoformat(lastUpdate), LOCAL_TZ)]

    if len(FILTERS_ARRAY) > 0:
        filtered_items = []
        for item in items:
            matches = True
            for filter in FILTERS_ARRAY:
                if filter not in item['description']:
                    matches = False
                    break
            if matches:
                filtered_items.append(item)
        return filtered_items
    else:
        return items


def _notify(items):
    blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":rotating_light: *PiLocator Notification* :rotating_light:",
                },
            },
            {"type": "divider"}
        ]

    for item in items:
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*<{0}|{1}>*".format(item['links'][0]['href'], item['title']),
                }
            ],
        })

    try:
        print('Found {} new RPIs. Notifying..'.format(len(blocks)))
        slack_client.chat_postMessage(
            channel=SLACK_CHANNEL,
            blocks=blocks,
            icon_emoji=":robot_face:",
            text='PiLocation Notification'
        )
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]
        print(f"Got an error: {e.response['error']}")


if __name__ == '__main__':
    print("Starting PiNotify..")
    print("  Channel:\t{}".format(SLACK_CHANNEL))
    print("  Filters:\t{}".format(FILTERS))
    print("  Interval:\t{}".format(CHECK_INTERVAL))
    _getFiltersArray()

    while True:
        items = _getItemsForChannel('https://rpilocator.com/feed/', (datetime.now() - timedelta(seconds=CHECK_INTERVAL)).isoformat())

        if len(items) > 0:
            _notify(items)

        time.sleep(CHECK_INTERVAL)