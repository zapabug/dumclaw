import os
import time
from dotenv import load_dotenv

from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage

load_dotenv()

private_key = PrivateKey.from_nsec(os.getenv("NOSTR_SECRET"))
public_key = private_key.public_key.hex()

relay_manager = RelayManager()

# General read/write relays
GENERAL_RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol"
]

# Relay list aggregator
OUTBOX_RELAYS = [
    "wss://purplepag.es"
]

# DM relays
DM_RELAYS = [
    "wss://nip17.com"
]

ALL_RELAYS = GENERAL_RELAYS + PAID_RELAYS + OUTBOX_RELAYS + DM_RELAYS

for relay in ALL_RELAYS:
    relay_manager.add_relay(relay)

relay_manager.open_connections()

time.sleep(2)


def send_note(text):

    event = Event(
        content=text,
        public_key=public_key,
        kind=1
    )

    private_key.sign_event(event)
    relay_manager.publish_event(event)

    print("Published:", text)


def send_dm(target_pubkey, text):

    dm = EncryptedDirectMessage(
        recipient_pubkey=target_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(private_key)

    relay_manager.publish_event(event)

    print("DM sent")