from pynostr.relay_manager import RelayManager
import threading
import time

relay_manager = RelayManager()

OUTBOUND_RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol",
    "wss://relay.snort.social",
    "wss://nip17.com",
    "wss://relay.nostr.band",
    "wss://auth.nostr1.com"
]

LOCAL_RELAY = "ws://127.0.0.1:7777"

relay_status = {}
initialized = False


def _relay_loop():

    relay_manager.open_connections()


def init_relays():

    global initialized

    if initialized:
        return

    for r in OUTBOUND_RELAYS:
        relay_manager.add_relay(r)
        relay_status[r] = "connecting"

    relay_manager.add_relay(LOCAL_RELAY)
    relay_status[LOCAL_RELAY] = "connecting"

    t = threading.Thread(target=_relay_loop, daemon=True)
    t.start()

    time.sleep(2)

    initialized = True


def get_relay_manager():
    return relay_manager


def get_relay_status():

    for url, relay in relay_manager.relays.items():

        try:
            if relay.ws.sock and relay.ws.sock.connected:
                relay_status[url] = "connected"
            else:
                relay_status[url] = "disconnected"

        except:
            relay_status[url] = "unknown"

    return relay_status