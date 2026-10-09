import json
import os
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


QMSG_KEY = os.environ["QMSG_KEY"]

SHOWROOM_API = (
    "https://"
    "www.showroom-live.com/api/time_table/time_tables"
)

SHOWROOM_ROOM_BASE = (
    "https://"
    "www.showroom-live.com/r/"
)

QMSG_ENDPOINT = (
    "https://"
    "qmsg.zendee.cn/v3/send/"
    + QMSG_KEY
)

CHECK_INTERVAL = 180
STATE_FILE = Path.home() / "akb_showroom_notified.json"


def load_state():
    if not STATE_FILE.exists():
        return set()

    try:
        return set(json.loads(STATE_FILE.read_text()))
    except Exception:
        return set()


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            sorted(state),
            ensure_ascii=False,
            indent=2,
        )
    )


def get_programmes():
    response = requests.get(
        SHOWROOM_API,
        params={
            "order": "asc",
            "started_at": int(time.time()),
        },
        timeout=15,
    )
    response.raise_for_status()

    programmes = []

    for item in response.json().get("time_tables", []):
        if "AKB48" not in item.get("main_name", ""):
            continue

        if not item.get("room_id"):
            continue

        if not item.get("started_at"):
            continue

        programmes.append(item)

    return programmes


def make_message(item):
    start_time = datetime.fromtimestamp(
        int(item["started_at"]),
        ZoneInfo("Asia/Tokyo"),
    )

    title = item.get("main_name", "AKB48成员")
    room_key = item.get("room_url_key", "")
    room_url = SHOWROOM_ROOM_BASE + room_key

    return (
        "AKB48 Showroom直播预告\n"
        f"成员：{title}\n"
        f"时间：{start_time:%Y-%m-%d %H:%M:%S}\n"
        f"房间：{room_url}"
    )


def send_qmsg(message):
    response = requests.post(
        QMSG_ENDPOINT,
        data={"msg": message},
        timeout=15,
    )

    print("Qmsg HTTP状态：", response.status_code)
    print("Qmsg返回：", response.text[:500])

    response.raise_for_status()

    result = response.json()

    if result.get("success") is not True:
        raise RuntimeError(f"Qmsg发送失败：{result}")


def main():
    notified = load_state()

    print("AKB48 Showroom监控已启动")
    print("监控范围：全部AKB48成员")
    print("检查间隔：", CHECK_INTERVAL, "秒")

    while True:
        try:
            programmes = get_programmes()
            print("当前节目数量：", len(programmes))

            changed = False

            for item in programmes:
                event_key = (
                    f'{item["room_id"]}:'
                    f'{item["started_at"]}'
                )

                if event_key in notified:
                    continue

                message = make_message(item)

                print("正在发送：")
                print(message)

                send_qmsg(message)

                notified.add(event_key)
                changed = True

            if changed:
                save_state(notified)

        except Exception as error:
            print("本轮检查失败：", repr(error))

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
