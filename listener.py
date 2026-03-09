import time

from pynostr.relay_manager import RelayManager
from pynostr.filters import Filters
from pynostr.encrypted_dm import EncryptedDirectMessage

from config import PRIVATE_KEY, PUBLIC_KEY
from llm import ask_llm
from nostr_client import send_dm


print("Gerald pubkey:", PUBLIC_KEY)

relay_manager = RelayManager()

LISTEN_RELAYS = ["ws://127.0.0.1:7777"]

for relay in LISTEN_RELAYS:
    relay_manager.add_relay(relay)

relay_manager.open_connections()

time.sleep(2)

subscription = Filters([
    {
        "kinds": [4],
        "#p": [PUBLIC_KEY]
    }
])

relay_manager.add_subscription("dm-listener", subscription)

print("Subscription started")


def start_listener():

    print("Listening for DM commands...")

    while True:

        relay_manager.poll()

        while relay_manager.message_pool.has_events():

            event_msg = relay_manager.message_pool.get_event()
            event = event_msg.event

            print("EVENT RECEIVED:", event.kind, event.pubkey)

            if event.pubkey == PUBLIC_KEY:
                continue

            try:

                dm = EncryptedDirectMessage.from_event(event)
                message = dm.decrypt(PRIVATE_KEY)

                print("DM received:", message)

                reply = ask_llm(message)

                print("Gerald reply:", reply)

                send_dm(event.pubkey, reply)

            except Exception as e:

                print("DM decrypt failed:", e)

        time.sleep(1)


if __name__ == "__main__":
    start_listener()