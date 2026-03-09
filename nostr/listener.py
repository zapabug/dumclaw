import os
import time
from dotenv import load_dotenv
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from pynostr.filters import Filters
from pynostr.encrypted_dm import EncryptedDirectMessage

load_dotenv()

private_key = PrivateKey.from_nsec(os.getenv("NOSTR_SECRET"))
public_key = private_key.public_key.hex()

relay_manager = RelayManager()

LISTEN_RELAYS = ["ws://127.0.0.1:7777"]

for relay in LISTEN_RELAYS:
    relay_manager.add_relay(relay)

relay_manager.open_connections()

time.sleep(2)

subscription = Filters({
    "kinds": [4, 44, 1059],
    "#p": [public_key]
})

relay_manager.add_subscription("dm-listener", subscription)


def start_listener():

    print("Listening for DM commands...")

    while True:

        relay_manager.poll()

        while relay_manager.message_pool.has_events():

            event_msg = relay_manager.message_pool.get_event()
            event = event_msg.event

            if event.pubkey == public_key:
                continue

            try:

                dm = EncryptedDirectMessage.from_event(event)
                message = dm.decrypt(private_key)

                print("DM received:", message)
                reply = ask_llm(message, GERALD_PROMPT)

                print("Gerald reply:", reply)

                send_dm(event.pubkey, reply)

            except Exception as e:

                print("DM decrypt failed:", e)

        time.sleep(1)