import json
import time

from config import PRIVATE_KEY, PUBLIC_KEY
from nostr.relay import get_relay_manager

from pynostr.event import Event
from pynostr.key import PrivateKey

from nostr.nip44 import get_conversation_key, encrypt as nip44_encrypt


def send_note(text):

    relay_manager = get_relay_manager()

    event = Event(
        kind=1,
        content=text,
        pubkey=PUBLIC_KEY
    )

    event.sign(PRIVATE_KEY.hex())

    relay_manager.publish_event(event)

    print("NOTE SENT:", text)


def send_note_tagged(text, tagged_pubkey):

    relay_manager = get_relay_manager()

    event = Event(
        kind=1,
        content=text,
        pubkey=PUBLIC_KEY
    )

    event.tags.append(["p", tagged_pubkey])

    event.sign(PRIVATE_KEY.hex())

    relay_manager.publish_event(event)

    relay_manager.run_sync()

    print("NOTE SENT (tagged):", text)


def send_dm(recipient_pubkey, text):
    """
    Send NIP-17 DM (gift wrap → seal → rumor)
    """

    relay_manager = get_relay_manager()

    # ------------------------
    # Step 1 — rumor (kind 14)
    # ------------------------

    rumor = {
        "kind": 14,
        "pubkey": PUBLIC_KEY,
        "created_at": int(time.time()),
        "tags": [["p", recipient_pubkey]],
        "content": text
    }

    rumor_json = json.dumps(rumor)

    # ------------------------
    # Step 2 — seal (kind 13)
    # ------------------------

    conv_key = get_conversation_key(PRIVATE_KEY, recipient_pubkey)

    encrypted_rumor = nip44_encrypt(rumor_json, conv_key)

    seal_event = Event(
        kind=13,
        content=encrypted_rumor,
        pubkey=PUBLIC_KEY
    )

    seal_event.sign(PRIVATE_KEY.hex())

    seal_json = json.dumps(seal_event.to_dict())

    # ------------------------
    # Step 3 — gift wrap (1059)
    # ------------------------

    ephemeral = PrivateKey()

    wrap_key = get_conversation_key(ephemeral, recipient_pubkey)

    encrypted_seal = nip44_encrypt(seal_json, wrap_key)

    gift = Event(
        kind=1059,
        content=encrypted_seal,
        pubkey=ephemeral.public_key.hex()
    )

    gift.tags.append(["p", recipient_pubkey])

    gift.sign(ephemeral.hex())

    # ------------------------
    # publish
    # ------------------------

    relay_manager.publish_event(gift)
    
    relay_manager.run_sync()

    print("NIP17 DM SENT →", recipient_pubkey)