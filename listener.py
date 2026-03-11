import json
import os
import websocket
import time
import sqlite3
import uuid
import threading
import queue
from config import PRIVATE_KEY, PUBLIC_KEY
from llm import ask_llm
from nostr.publisher import send_dm, send_note, send_note_tagged
from pynostr.encrypted_dm import EncryptedDirectMessage
from nostr.nip44 import get_conversation_key, decrypt as nip44_decrypt

RELAY = "ws://127.0.0.1:7777"

# Reconnect delay after WebSocket drops (seconds)
RECONNECT_DELAY = 5

# NIP-17 subscription window: 2 days back (covers randomized timestamps)
NIP17_SINCE_WINDOW = 172800

# Deduplication DB prune interval and max age
PRUNE_INTERVAL = 3600       # check every hour
PRUNE_MAX_AGE_DAYS = 7      # delete records older than 7 days

# Allowed senders — only these pubkeys can command Gerald.
# Must match the whitelist in strfry policy.py.
ALLOWED_PUBKEYS = {
    "d83b5ef189df7e884627294b752969547814c3cfe38995cf207c040e03bbe7a4",
    "699af55b12ba03620cda782766ea5555b78f2b94ff36f1855c69cd4126f3b545",
}

# Path to the contacts JSON file (populated by fetch_contacts.py)
CONTACTS_FILE = "contacts.json"


# -------------------
# Seen events storage
# -------------------

def get_db():
    """Get a thread-local SQLite connection."""
    conn = sqlite3.connect("seen_events.db")
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS seen (
        id TEXT PRIMARY KEY,
        ts INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    conn.commit()
    return conn, cur


# Main thread DB connection
conn, cur = get_db()


def already_seen(event_id):
    cur.execute("SELECT 1 FROM seen WHERE id=?", (event_id,))
    return cur.fetchone() is not None


def mark_seen(event_id):
    cur.execute("INSERT OR IGNORE INTO seen(id) VALUES (?)", (event_id,))
    conn.commit()


def prune_seen_events():
    """Delete seen records older than PRUNE_MAX_AGE_DAYS."""
    cutoff = int(time.time()) - (PRUNE_MAX_AGE_DAYS * 86400)
    cur.execute("DELETE FROM seen WHERE ts < ?", (cutoff,))
    deleted = cur.rowcount
    conn.commit()
    if deleted > 0:
        print(f"PRUNE: deleted {deleted} old seen_events records")


def prune_loop():
    """Background thread that periodically prunes the seen_events DB."""
    while True:
        time.sleep(PRUNE_INTERVAL)
        try:
            prune_seen_events()
        except Exception as e:
            print(f"PRUNE error: {e}")


# -------------------
# Command queue (decouples listener from LLM)
# -------------------

command_queue = queue.Queue()


def command_worker():
    """
    Background worker that processes commands from the queue.
    This isolates the LLM call from the WebSocket receive loop.
    """
    # Worker needs its own DB connection for thread safety
    w_conn, w_cur = get_db()

    while True:
        try:
            sender_pubkey, plaintext = command_queue.get()
            print(f"WORKER: processing command from {sender_pubkey[:16]}...")
            process_command(sender_pubkey, plaintext)
        except Exception as e:
            print(f"WORKER error: {e}")
        finally:
            command_queue.task_done()


# -------------------
# Contacts lookup
# -------------------

def load_contacts():
    """Load the contacts JSON file. Returns dict of {name: pubkey}."""
    if not os.path.exists(CONTACTS_FILE):
        print(f"No contacts file found at {CONTACTS_FILE}")
        return {}
    try:
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load contacts: {e}")
        return {}


def lookup_contact(name):
    """Look up a contact by name (case-insensitive). Returns pubkey or None."""
    contacts = load_contacts()
    name_lower = name.lower().strip()
    for contact_name, pubkey in contacts.items():
        if contact_name.lower() == name_lower:
            return pubkey
    # Partial match fallback
    for contact_name, pubkey in contacts.items():
        if name_lower in contact_name.lower():
            return pubkey
    return None


# -------------------
# NIP-17 gift wrap unwrapping
# -------------------

def unwrap_gift_wrap(event):
    """
    Decrypt a kind 1059 gift wrap → kind 13 seal → kind 14 rumor.

    Returns (sender_pubkey, plaintext) or raises on failure.

    Flow:
      1. Gift wrap (kind 1059) is encrypted by an ephemeral key to Gerald.
         Decrypt with Gerald's privkey + gift wrap's pubkey (ephemeral).
      2. Inside is a kind 13 seal, signed by the real sender.
         Decrypt with Gerald's privkey + seal's pubkey (real sender).
      3. Inside is a kind 14 rumor (unsigned) with the plaintext content.
         Verify seal.pubkey == rumor.pubkey to prevent impersonation.
    """
    # Step 1: Decrypt the gift wrap → get the seal
    wrapper_pubkey = event["pubkey"]  # ephemeral random key
    conv_key_wrap = get_conversation_key(PRIVATE_KEY, wrapper_pubkey)
    seal_json = nip44_decrypt(event["content"], conv_key_wrap)
    seal = json.loads(seal_json)

    if seal.get("kind") != 13:
        raise ValueError(f"expected kind 13 seal, got kind {seal.get('kind')}")

    # Step 2: Decrypt the seal → get the rumor
    sender_pubkey = seal["pubkey"]  # real sender's pubkey
    conv_key_seal = get_conversation_key(PRIVATE_KEY, sender_pubkey)
    rumor_json = nip44_decrypt(seal["content"], conv_key_seal)
    rumor = json.loads(rumor_json)

    # Step 3: Verify sender consistency (anti-impersonation)
    if rumor.get("pubkey") != sender_pubkey:
        raise ValueError(
            f"sender mismatch: seal pubkey {sender_pubkey} != rumor pubkey {rumor.get('pubkey')}"
        )

    if rumor.get("kind") not in (14, 15):
        raise ValueError(f"expected kind 14/15 rumor, got kind {rumor.get('kind')}")

    return sender_pubkey, rumor.get("content", "")


# -------------------
# Websocket handlers
# -------------------

def on_open(ws):
    print("Connected to relay")

    # NIP-04 DMs: use current timestamp as since
    since_dm = int(time.time())

    # NIP-17 gift wraps: use 2-day window (covers randomized timestamps)
    since_gw = int(time.time()) - NIP17_SINCE_WINDOW

    # Subscription 1: NIP-04 legacy DMs (kind 4)
    sub_id_dm = f"gerald-dm-{uuid.uuid4().hex[:8]}"
    req_dm = [
        "REQ",
        sub_id_dm,
        {
            "kinds": [4],
            "#p": [PUBLIC_KEY],
            "since": since_dm
        }
    ]
    ws.send(json.dumps(req_dm))
    print(f"NIP-04 subscription sent: {sub_id_dm} (since={since_dm})")

    # Subscription 2: NIP-17 gift wraps (kind 1059) with bounded window
    sub_id_gw = f"gerald-gw-{uuid.uuid4().hex[:8]}"
    req_gw = [
        "REQ",
        sub_id_gw,
        {
            "kinds": [1059],
            "#p": [PUBLIC_KEY],
            "since": since_gw
        }
    ]
    ws.send(json.dumps(req_gw))
    print(f"NIP-17 subscription sent: {sub_id_gw} (since={since_gw})")


def on_message(ws, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print(f"RELAY RAW (invalid JSON): {message[:200]}")
        return

    if not isinstance(data, list) or len(data) < 2:
        print(f"RELAY RAW: {message[:200]}")
        return

    msg_type = data[0]

    # --- Log all non-EVENT relay messages for debug visibility ---
    if msg_type == "EOSE":
        sub_id = data[1] if len(data) > 1 else "?"
        print(f"RELAY EOSE: subscription {sub_id} — initial scan complete")
        return

    if msg_type == "NOTICE":
        notice_text = data[1] if len(data) > 1 else ""
        print(f"RELAY NOTICE: {notice_text}")
        return

    if msg_type == "CLOSED":
        sub_id = data[1] if len(data) > 1 else "?"
        reason = data[2] if len(data) > 2 else ""
        print(f"RELAY CLOSED: subscription {sub_id} reason={reason}")
        return

    if msg_type == "OK":
        event_id = data[1] if len(data) > 1 else "?"
        accepted = data[2] if len(data) > 2 else "?"
        reason = data[3] if len(data) > 3 else ""
        print(f"RELAY OK: event {event_id[:16]}... accepted={accepted} {reason}")
        return

    if msg_type != "EVENT":
        print(f"RELAY {msg_type}: {message[:200]}")
        return

    # --- Process EVENT messages ---
    if len(data) < 3:
        print(f"RELAY EVENT: malformed (len={len(data)})")
        return

    event = data[2]
    event_id = event.get("id", "")
    kind = event.get("kind")

    # Ignore own messages
    if event.get("pubkey") == PUBLIC_KEY:
        return

    # Ignore duplicates
    if already_seen(event_id):
        return
    mark_seen(event_id)

    print(f"EVENT RECEIVED: kind={kind} id={event_id[:16]}...")

    if kind == 4:
        handle_nip04(event)
    elif kind == 1059:
        handle_nip17(event)
    else:
        print(f"Ignoring unexpected kind {kind}")


def on_error(ws, error):
    print(f"WS ERROR: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"WS CLOSED: status={close_status_code} msg={close_msg}")


def handle_nip04(event):
    """Handle a legacy NIP-04 encrypted DM (kind 4)."""
    sender = event["pubkey"]

    if sender not in ALLOWED_PUBKEYS:
        print(f"NIP-04 DM from unauthorized pubkey {sender[:16]}... — ignored")
        return

    try:
        print("Decrypting NIP-04 DM...")
        dm = EncryptedDirectMessage.from_event_dict(event)
        plaintext = dm.decrypt(PRIVATE_KEY)
        print(f"DM from {sender[:16]}...: {plaintext}")
        # Enqueue instead of blocking
        command_queue.put((sender, plaintext))
    except Exception as e:
        print(f"NIP-04 decrypt failed: {e}")


def handle_nip17(event):
    """Handle a NIP-17 gift wrap (kind 1059)."""
    try:
        print("Unwrapping NIP-17 gift wrap...")
        sender, plaintext = unwrap_gift_wrap(event)

        # Authenticate sender AFTER decryption (can't check at relay level)
        if sender not in ALLOWED_PUBKEYS:
            print(f"NIP-17 DM from unauthorized pubkey {sender[:16]}... — ignored")
            return

        print(f"DM from {sender[:16]}...: {plaintext}")
        # Enqueue instead of blocking
        command_queue.put((sender, plaintext))
    except Exception as e:
        print(f"NIP-17 unwrap failed: {e}")


# -------------------
# Command routing
# -------------------

def process_command(sender_pubkey, plaintext):
    """
    Route a decrypted message through the LLM and execute the decided action.

    Actions:
      reply         — send DM back to sender
      note          — publish kind 1 note + send "note sent" DM to sender
      weather_reply — fetch weather, reply via DM
      dm_contact    — send DM to a named contact + confirm to sender
    """
    try:
        action, reply_text, extra = ask_llm(plaintext)
        print(f"Action: {action} | Gerald: {reply_text}")

        if action == "reply" or action == "weather_reply":
            # Simple DM reply
            send_dm(sender_pubkey, reply_text)
            print("DM reply sent")

        elif action == "note":
            # Publish kind 1 note, then confirm via DM
            send_note(reply_text)
            send_dm(sender_pubkey, f"note sent: {reply_text[:80]}...")
            print("Note published + confirmation DM sent")

        elif action == "dm_contact":
            contact_name = extra.get("contact", "")
            contact_pubkey = lookup_contact(contact_name)

            if contact_pubkey:
                send_dm(contact_pubkey, reply_text)
                send_dm(sender_pubkey, f"DM sent to {contact_name}")
                print(f"DM sent to contact '{contact_name}' ({contact_pubkey[:16]}...)")
            else:
                send_dm(sender_pubkey, f"I don't know anyone called '{contact_name}'. Check contacts.json.")
                print(f"Contact '{contact_name}' not found")

        else:
            # Fallback: DM reply
            send_dm(sender_pubkey, reply_text)
            print("Fallback DM reply sent")

    except Exception as e:
        print(f"Command processing failed: {e}")


# -------------------
# Entry point
# -------------------

def start():
    print("Gerald listener starting")
    print(f"Pubkey: {PUBLIC_KEY}")
    print(f"Relay:  {RELAY}")
    print(f"Allowed senders: {len(ALLOWED_PUBKEYS)}")

    contacts = load_contacts()
    print(f"Contacts loaded: {len(contacts)} entries")

    # Start background command worker (isolates LLM from WS loop)
    worker = threading.Thread(target=command_worker, daemon=True)
    worker.start()
    print("Command worker started")

    # Start background prune thread
    pruner = threading.Thread(target=prune_loop, daemon=True)
    pruner.start()
    print("DB prune thread started")

    # --- Reconnect loop ---
    while True:
        ws = websocket.WebSocketApp(
            RELAY,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        print(f"Connecting to {RELAY}...")
        ws.run_forever(ping_interval=30, ping_timeout=10)

        # If we reach here, the WebSocket has disconnected
        print(f"WebSocket disconnected. Reconnecting in {RECONNECT_DELAY}s...")
        time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    start()
