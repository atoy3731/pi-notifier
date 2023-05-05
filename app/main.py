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
COUNTRY = os.environ.get('COUNTRY', '')
PI_LOCATOR_TZ = os.environ.get('PI_LOCATOR_TZ', 'GMT')
LOCAL_TZ = os.environ.get('LOCAL_TZ', 'EST')

SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_CHANNEL = os.environ.get('SLACK_CHANNEL', '#pi-notify')

PROCESS_INIT = os.environ.get('PROCESS_INIT', 'true')

FILTERS_ARRAY = []
slack_client = WebClient(token=os.environ['SLACK_TOKEN'])
last_item_id = ''


def _getFiltersArray():
    global FILTERS_ARRAY

    if FILTERS != '':
        FILTERS_ARRAY = list(map(str.strip, FILTERS.split(',')))


def _getInitialItem(xmlUrl):
    global last_item_id

    socket.setdefaulttimeout(60)

    parsed = feedparser.parse(xmlUrl)
    items = [entry for entry in parsed.entries]
    last_item_id = items[0].id


def _getItemsForChannel(xmlUrl):
    global last_item_id

    socket.setdefaulttimeout(60)

    parsed = feedparser.parse(xmlUrl)
    items = [entry for entry in parsed.entries]
    new_item_id = items[0].id

    filtered_items = []
    for item in items:
        if item.id == last_item_id:
            break

        if len(FILTERS_ARRAY) > 0:
            matches = True
            for filter in FILTERS_ARRAY:
                if filter not in item.summary:
                    matches = False
                    break
            if matches:
                if COUNTRY != '':
                    for tag in item.tags:
                        if tag.term == COUNTRY:
                            filtered_items.append(item)
                            break
                else:
                    filtered_items.append(item)
        else:
            if COUNTRY != '':
                for tag in item.tags:
                    if tag.term == COUNTRY:
                        filtered_items.append(item)
                        break
            else:
                filtered_items.append(item)

    last_item_id = new_item_id
    return filtered_items


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
    print("  Filters:\t{}".format(FILTERS if FILTERS != '' else '(None Supplied)'))
    print("  Country:\t{}".format(COUNTRY if COUNTRY != '' else '(None Supplied)'))
    print("  Interval:\t{}s".format(CHECK_INTERVAL))

    _getFiltersArray()

    if PROCESS_INIT.lower() != 'true':
        _getInitialItem('https://rpilocator.com/feed/')

    while True:
        items = _getItemsForChannel('https://rpilocator.com/feed/')

        if len(items) > 0:
            _notify(items)

        time.sleep(CHECK_INTERVAL)