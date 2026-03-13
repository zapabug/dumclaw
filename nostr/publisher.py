import websocket
import threading
import queue
import json
import time


from config import PRIVATE_KEY, PUBLIC_KEY

from pynostr.event import Event
from pynostr.key import PrivateKey

from nostr.nip44 import get_conversation_key, encrypt as nip44_encrypt

RELAY_PUBLIC = "ws://relay.snort.social"

publish_queue = queue.Queue()

publisher_ws = None
publisher_connected = False


def publisher_loop():

    global publisher_ws, publisher_connected

    while True:

        try:
            print(f"Publisher connecting → {RELAY_PUBLIC}")

            publisher_ws = websocket.create_connection(RELAY_PUBLIC)
            publisher_ws.settimeout(30)

            publisher_connected = True
            print("Publisher connected")

            while True:

                event = publish_queue.get()
                msg = json.dumps(["EVENT", event])

                try:
                    publisher_ws.send(msg)
                    print("EVENT SENT:", event["id"][:16])
                    publish_queue.task_done()

                except Exception as send_error:

                    print("Send failed, requeueing:", send_error)

                    # Put event back so it isn't lost
                    publish_queue.put(event)

                    try:
                        publisher_ws.close()
                    except:
                        pass

                    raise send_error

        except Exception as e:

            publisher_connected = False
            print("Publisher error:", e)

            try:
                publisher_ws.close()
            except:
                pass

            time.sleep(3)

def start_publisher():

    t = threading.Thread(
        target=publisher_loop,
        daemon=True
    )

    t.start()

def publish_event(event_dict):

    publish_queue.put(event_dict)
            
def send_note(text):

    
    event = Event(
        kind=1,
        content=text,
        pubkey=PUBLIC_KEY
    )

    event.sign(PRIVATE_KEY.hex())

    publish_event(event.to_dict())

    print("NOTE SENT:", text)


def send_note_tagged(text, tagged_pubkey):

    
    event = Event(
        kind=1,
        content=text,
        pubkey=PUBLIC_KEY
    )

    event.tags.append(["p", tagged_pubkey])

    event.sign(PRIVATE_KEY.hex())

    publish_event(event.to_dict())

    print("NOTE SENT (tagged):", text)


def send_dm(recipient_pubkey, text, reply_to=None):
    """
    Send NIP-17 DM (gift wrap → seal → rumor)
    """

    # ------------------------
    # Step 1 — rumor (kind 14)
    # ------------------------

    tags = [["p", recipient_pubkey]]

    if reply_to:
        tags.append(["e", reply_to])

    rumor = {
        "kind": 14,
        "pubkey": PUBLIC_KEY,
        "created_at": int(time.time()),
        "tags": tags,
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

    publish_event(gift.to_dict())
    
    # ------------------------
    # publish
    # ------------------------

    print("NIP17 DM SENT →", recipient_pubkey)