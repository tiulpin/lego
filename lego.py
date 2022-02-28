import time
from json import dumps, loads
from os import getenv

import requests
from telegram import Bot, ParseMode

HEADERS = {
    "Accept": "*/*",
    "Origin": "https://www.tinkoff.ru",
    "Content-Length": "219",
    "Accept-Language": "en-US,en;q=0.9",
    "Host": "api.tinkoff.ru",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
    "Referer": "https://www.tinkoff.ru/",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
OK_LIMIT = 500
DATA = {  #
    "bounds": {
        "bottomLeft": {
            "lat": 59.77858262667984,
            "lng": 30.1897874816115,
        },
        "topRight": {
            "lat": 60.146283140861684,
            "lng": 30.519377325361496,
        },
    },
    "filters": {
        "banks": [
            "tcs",
        ],
        "showUnavailable": True,
        "currencies": ["USD"],
    },
    "zoom": 11,
}
BOT = Bot(token=getenv("TELEGRAM_TOKEN"))
CHAT_ID = getenv("CHAT_ID")
MESSAGES = 0


def send_post(text, latitude, longitude):
    """Send post to the channel. Avoids limit of messages per second / per minute."""
    global MESSAGES
    while True:
        try:
            BOT.sendMessage(
                chat_id=CHAT_ID,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
            BOT.sendLocation(
                chat_id=CHAT_ID,
                latitude=latitude,
                longitude=longitude,
            )
            MESSAGES += 1
            if MESSAGES >= 20:
                print("Sleeping 60 seconds...")
                time.sleep(60)
                MESSAGES = 0
            else:
                time.sleep(1)
                print("Sleeping 1 second...")
            break
        except Exception as e:
            print(e)
            print("Sleeping 5 seconds...")
            time.sleep(5)
            print("Woke up!")


def main():
    response = requests.post(
        "https://api.tinkoff.ru/geo/withdraw/clusters", headers=HEADERS, json=DATA
    )
    data = loads(response.content.decode("utf-8"))
    try:
        clusters = data["payload"]["clusters"]
        print(f"Found {len(clusters)} clusters...")
        for cluster in clusters:
            points = cluster["points"]
            print(f"Found {len(points)} points...")
            for point in points:
                if point["brand"]["id"] == "tcs" and point["atmInfo"]["available"]:
                    usd_limit, eur_limit = 0, 0
                    for limit in point["limits"]:
                        if limit["currency"] == "USD":
                            usd_limit = limit["amount"]
                        elif limit["currency"] == "EUR":
                            eur_limit = limit["amount"]
                    if usd_limit >= OK_LIMIT or eur_limit >= OK_LIMIT:
                        message = "📍{}\n💵 **USD**: {}\n💶 **EUR**: {}".format(
                            point["address"], usd_limit, eur_limit
                        )
                        send_post(
                            message,
                            point["latitude"],
                            point["longitude"],
                        )
    except Exception as e:
        print(e)
        print(dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
