from config import PRIVATE_KEY, PUBLIC_KEY

from pynostr.relay_manager import RelayManager
from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage

import time


relay_manager = RelayManager()

# Main relays
relay_manager.add_relay("wss://relay.damus.io")
relay_manager.add_relay("wss://relay.primal.net")
relay_manager.add_relay("wss://nos.lol")
relay_manager.add_relay("wss://relay.snort.social")

# DM / inbox relays
relay_manager.add_relay("wss://nip17.com")
relay_manager.add_relay("wss://relay.nostr.band")
relay_manager.add_relay("wss://auth.nostr1.com")

# Local strfry relay
relay_manager.add_relay("ws://127.0.0.1:7777")

relay_manager.open_connections()

# allow connections to establish
time.sleep(2)


def send_note(text):
    """Publish a kind 1 note (public post)."""
    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    PRIVATE_KEY.sign_event(event)

    relay_manager.publish_event(event)

    time.sleep(2)

    print("NOTE SENT:", text)


def send_note_tagged(text, tagged_pubkey):
    """Publish a kind 1 note with a p-tag mentioning someone."""
    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    event.tags.append(["p", tagged_pubkey])

    PRIVATE_KEY.sign_event(event)

    relay_manager.publish_event(event)

    time.sleep(2)

    print(f"NOTE SENT (tagged {tagged_pubkey[:16]}...):", text)


def send_dm(recipient_pubkey, text):
    """Send a NIP-04 encrypted DM (kind 4)."""
    dm = EncryptedDirectMessage(
        recipient_pubkey=recipient_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(PRIVATE_KEY)

    # required tag so clients know the recipient
    event.tags.append(["p", recipient_pubkey])

    relay_manager.publish_event(event)

    time.sleep(2)

    print("DM SENT →", recipient_pubkey)
