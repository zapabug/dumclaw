import json
import websocket
import time
import sqlite3

from config import PRIVATE_KEY, PUBLIC_KEY
from llm import ask_llm
from nostr_client import send_dm
from pynostr.encrypted_dm import EncryptedDirectMessage


RELAY = "ws://127.0.0.1:7777"

# -------------------
# Seen events storage
# -------------------

conn = sqlite3.connect("seen_events.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS seen (
    id TEXT PRIMARY KEY
)
""")

conn.commit()


def already_seen(event_id):

    cur.execute("SELECT 1 FROM seen WHERE id=?", (event_id,))
    return cur.fetchone() is not None


def mark_seen(event_id):

    cur.execute("INSERT OR IGNORE INTO seen VALUES (?)", (event_id,))
    conn.commit()


# -------------------
# Websocket handlers
# -------------------

def on_open(ws):

    print("Connected to relay")

    since = int(time.time())

    req = [
        "REQ",
        "gerald-dm",
        {
            "kinds": [4],
            "#p": [PUBLIC_KEY],
            "since": since
        }
    ]

    ws.send(json.dumps(req))

    print("Subscription sent")


def on_message(ws, message):

    data = json.loads(message)

    if data[0] != "EVENT":
        return

    event = data[2]

    if event["kind"] != 4:
        return

    # ignore own messages
    if event["pubkey"] == PUBLIC_KEY:
        return

    # ignore duplicates
    if already_seen(event["id"]):
        return

    mark_seen(event["id"])

    print("EVENT RECEIVED:", event["id"])

    try:

        dm = EncryptedDirectMessage.from_event_dict(event)

        message = dm.decrypt(PRIVATE_KEY)

        print("DM received:", message)

        reply = ask_llm(message)

        print("Gerald reply:", reply)

        send_dm(event["pubkey"], reply)

        print("Reply sent")

    except Exception as e:

        print("Decrypt failed:", e)


def start():

    print("Gerald listener starting")
    print("Pubkey:", PUBLIC_KEY)

    ws = websocket.WebSocketApp(
        RELAY,
        on_open=on_open,
        on_message=on_message
    )

    ws.run_forever()


if __name__ == "__main__":
    start()