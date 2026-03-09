from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager
from pynostr.event import Event
from pynostr.encrypted_dm import EncryptedDirectMessage
import time
import os
from dotenv import load_dotenv

load_dotenv()

private_key = PrivateKey.from_nsec(os.getenv("NOSTR_SECRET"))
public_key = private_key.public_key

relay_manager = RelayManager()
relay_manager.add_relay("ws://localhost:7777")
relay_manager.open_connections()

time.sleep(1)


def send_note(text):

    event = Event(
        content=text,
        public_key=public_key.hex()
    )

    private_key.sign_event(event)

    relay_manager.publish_event(event)

def send_dm(recipient_pubkey, text):

    dm = EncryptedDirectMessage(
        recipient_pubkey=recipient_pubkey,
        cleartext_content=text
    )

    event = dm.to_event(private_key)

    relay_manager.publish_event(event)
# testing
send_note("Gerald boot sequence complete. Regrettably.")