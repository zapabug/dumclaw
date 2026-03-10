from config import PRIVATE_KEY, PUBLIC_KEY
from relay import get_relay_manager

from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage

import time


def send_note(text):

    relay_manager = get_relay_manager()

    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    PRIVATE_KEY.sign_event(event)

    relay_manager.publish_event(event)

    time.sleep(1)

    print("NOTE SENT:", text)


def send_note_tagged(text, tagged_pubkey):

    relay_manager = get_relay_manager()

    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    event.tags.append(["p", tagged_pubkey])

    PRIVATE_KEY.sign_event(event)

    relay_manager.publish_event(event)

    time.sleep(1)

    print("NOTE SENT:", text)


def send_dm(recipient_pubkey, text):

    relay_manager = get_relay_manager()

    dm = EncryptedDirectMessage(
        recipient_pubkey=recipient_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(PRIVATE_KEY)

    event.tags.append(["p", recipient_pubkey])

    relay_manager.publish_event(event)

    time.sleep(1)

    print("DM SENT →", recipient_pubkey)