import websocket
import threading
import queue
import json
import time

from config import PRIVATE_KEY, PUBLIC_KEY

from pynostr.event import Event
from pynostr.key import PrivateKey

from nostr.nip44 import get_conversation_key, encrypt as nip44_encrypt

RELAY_PUBLIC = "wss://relay.snort.social"

publish_queue = queue.Queue()
publisher_ws = None
publisher_connected = False
connected_event = threading.Event()


def on_open(ws):
    global publisher_connected
    print("Publisher connected")
    publisher_connected = True
    connected_event.set()


def on_close(ws, close_status_code, close_msg):
    global publisher_connected
    print(f"Publisher disconnected: {close_status_code} - {close_msg}")
    publisher_connected = False
    connected_event.clear()


def on_error(ws, error):
    print(f"Publisher error: {error}")


def on_message(ws, message):
    print(f"Publisher received: {message[:60]}...")


def publisher_loop():
    global publisher_ws, publisher_connected

    while True:
        try:
            print(f"Publisher connecting → {RELAY_PUBLIC}")
            
            # Create WebSocketApp with keepalive
            publisher_ws = websocket.WebSocketApp(
                RELAY_PUBLIC,
                on_open=on_open,
                on_close=on_close,
                on_error=on_error,
                on_message=on_message
            )
            
            # Start the WebSocketApp with ping_interval for keepalive
            publisher_ws.run_forever(
                ping_interval=30,  # Send ping every 30 seconds to prevent idle timeout
                ping_timeout=10
            )
            
        except Exception as e:
            print("Publisher error:", e)
            publisher_connected = False
            connected_event.clear()
            
            try:
                if publisher_ws:
                    publisher_ws.close()
            except:
                pass
                
            time.sleep(3)


def queue_consumer():
    """Thread that consumes the publish_queue and sends events to the WebSocket."""
    while True:
        try:
            # Wait for an event to be available
            event = publish_queue.get()
            
            if not publisher_connected:
                # If not connected, put the event back and wait
                publish_queue.put(event)
                time.sleep(1)
                continue
            
            # Convert event to JSON format expected by the relay
            msg = json.dumps(["EVENT", event])
            
            try:
                # Send the message
                publisher_ws.send(msg)
                print("EVENT SENT:", event["id"][:16])
                publish_queue.task_done()
                
            except Exception as send_error:
                print("Send failed, requeueing:", send_error)
                
                # Put event back so it isn't lost
                publish_queue.put(event)
                
                # Close the WebSocket to trigger reconnect
                try:
                    publisher_ws.close()
                except:
                    pass
                
        except Exception as e:
            print("Queue consumer error:", e)
            time.sleep(1)


def start_publisher():
    # Start the publisher loop thread
    publisher_thread = threading.Thread(
        target=publisher_loop,
        daemon=True
    )
    publisher_thread.start()
    
    # Start the queue consumer thread
    consumer_thread = threading.Thread(
        target=queue_consumer,
        daemon=True
    )
    consumer_thread.start()


def publish_event(event_dict):
    publish_queue.put(event_dict)
    
    # Wait until connected before returning
    connected_event.wait(timeout=5)


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
    
    print("NIP17 DM SENT →", recipient_pubkey)