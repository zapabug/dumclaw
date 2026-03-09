import time

from pynostr.relay_manager import RelayManager
from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage

from config import PRIVATE_KEY, PUBLIC_KEY

relay_manager = RelayManager()

GENERAL_RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol"
]

OUTBOX_RELAYS = [
    "wss://purplepag.es"
]

DM_RELAYS = [
    "wss://nip17.com"
]

ALL_RELAYS = GENERAL_RELAYS + OUTBOX_RELAYS + DM_RELAYS

for relay in ALL_RELAYS:
    relay_manager.add_relay(relay)

relay_manager.open_connections()

time.sleep(2)


def send_note(text):

    event = Event(
        content=text,
        public_key=PUBLIC_KEY,
        kind=1
    )

    PRIVATE_KEY.sign_event(event)
    relay_manager.publish_event(event)

    print("Published:", text)


def send_dm(target_pubkey, text):

    dm = EncryptedDirectMessage(
        recipient_pubkey=target_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(PRIVATE_KEY)

    relay_manager.publish_event(event)

    print("DM sent")

from llm import decide_tool, gerald_reply
from tools import get_weather