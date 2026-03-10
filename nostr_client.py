from config import PRIVATE_KEY, PUBLIC_KEY

from pynostr.relay_manager import RelayManager
from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage

import time


relay_manager = RelayManager()

relay_manager.add_relay("ws://127.0.0.1:7777")

relay_manager.open_connections()

time.sleep(1)


def send_note(text):

    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    PRIVATE_KEY.sign_event(event)

    relay_manager.publish_event(event)

    print("NOTE SENT:", text)


def send_dm(recipient_pubkey, text):

    dm = EncryptedDirectMessage(
        recipient_pubkey=recipient_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(PRIVATE_KEY)

    relay_manager.publish_event(event)

    print("DM SENT →", recipient_pubkey)