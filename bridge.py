import json
import time
import websocket
import threading
from config import PUBLIC_KEY   # ← your existing config

RELAY_PUBLIC = "ws://relay.snort.social"   #not syncying to avoid      
RELAY_LOCAL  = "ws://127.0.0.1:7777"

RECONNECT_DELAY = 5

# Persistent publisher to local strfry (so policy + broadcast happens)
publisher_ws = None

def connect_publisher():
    global publisher_ws
    def on_open(ws):
        print("Bridge: connected to local strfry for republishing")
    def on_close(ws, *a):
        print("Bridge: local disconnected")
    ws = websocket.WebSocketApp(RELAY_LOCAL, on_open=on_open, on_close=on_close)
    threading.Thread(target=ws.run_forever, daemon=True, kwargs={"ping_interval": 20}).start()
    time.sleep(1)
    publisher_ws = ws

def forward_event(event):
    """Republish → strfry policy runs AGAIN + broadcasts to listener.py"""
    try:
        msg = json.dumps(["EVENT", event])
        publisher_ws.send(msg)
        print(f"✅ REPUBLISHED: kind={event.get('kind')} id={event.get('id','')[:16]}...")
    except Exception as e:
        print(f"Forward failed: {e}")

# Public listener — exact same filter as your 4 sync workers
def start_bridge():
    print("=== Dumclaw Live Bridge Starting ===")
    print(f"Public: {RELAY_PUBLIC} | Local: {RELAY_LOCAL}")
    print("Only forwarding DMs/gift-wraps that already passed your policy")

    def on_open(ws):
        print("Bridge: subscribed to public relay (same filter as your sync workers)")
        since = int(time.time()) - 172800  # 2 days (covers NIP-17 randomization)
        req = ["REQ", "bridge-dms", {
            "kinds": [4, 1059],
            "#p": [PUBLIC_KEY],
            "since": since
        }]
        ws.send(json.dumps(req))

    def on_message(ws, message):
        try:
            data = json.loads(message)

            if len(data) >= 3 and data[0] == "EVENT":
                event = data[2]

            # Ignore events authored by our own pubkey
            if event.get("pubkey") == PUBLIC_KEY:
                return

            if event.get("kind") in (4, 1059):
                forward_event(event)   # ← triggers policy + real-time broadcast
        except:
            pass

    while True:
        ws = websocket.WebSocketApp(
            RELAY_PUBLIC,
            on_open=on_open,
            on_message=on_message,
            on_error=lambda ws, err: print(f"Bridge public error: {err}"),
            on_close=lambda ws, *a: print("Bridge public closed, reconnecting...")
        )
        ws.run_forever(ping_interval=30, ping_timeout=10)
        time.sleep(RECONNECT_DELAY)

if __name__ == "__main__":
    connect_publisher()
    start_bridge()