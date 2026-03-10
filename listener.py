import json
import websocket
import time
import sqlite3
import uuid
from config import PRIVATE_KEY, PUBLIC_KEY
from llm import ask_llm
from nostr_client import send_dm
from pynostr.encrypted_dm import EncryptedDirectMessage
from nip44 import get_conversation_key, decrypt as nip44_decrypt

RELAY = "ws://127.0.0.1:7777"

# Allowed senders — only these pubkeys can command Gerald.
# Must match the whitelist in strfry policy.py.
ALLOWED_PUBKEYS = {
    "d83b5ef189df7e884627294b752969547814c3cfe38995cf207c040e03bbe7a4",
    "699af55b12ba03620cda782766ea5555b78f2b94ff36f1855c69cd4126f3b545",
}

# -------------------
# Seen events storage
# -------------------

conn = sqlite3.connect("seen_events.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS seen (
    id TEXT PRIMARY KEY
)
""")

conn.commit()

def already_seen(event_id):
    cur.execute("SELECT 1 FROM seen WHERE id=?", (event_id,))
    return cur.fetchone() is not None

def mark_seen(event_id):
    cur.execute("INSERT OR IGNORE INTO seen VALUES (?)", (event_id,))
    conn.commit()


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
    since = int(time.time())

    # Subscription 1: NIP-04 legacy DMs (kind 4) — use since filter
    sub_id_dm = f"gerald-dm-{uuid.uuid4().hex[:8]}"
    req_dm = [
        "REQ",
        sub_id_dm,
        {
            "kinds": [4],
            "#p": [PUBLIC_KEY],
            "since": since
        }
    ]
    ws.send(json.dumps(req_dm))
    print(f"NIP-04 subscription sent: {sub_id_dm}")

    # Subscription 2: NIP-17 gift wraps (kind 1059) — NO since filter
    # because gift wrap created_at is randomized up to 2 days in the past.
    # Deduplication is handled by seen_events.db.
    sub_id_gw = f"gerald-gw-{uuid.uuid4().hex[:8]}"
    req_gw = [
        "REQ",
        sub_id_gw,
        {
            "kinds": [1059],
            "#p": [PUBLIC_KEY]
        }
    ]
    ws.send(json.dumps(req_gw))
    print(f"NIP-17 subscription sent: {sub_id_gw}")


def on_message(ws, message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("Invalid JSON from relay:", message[:200])
        return

    # Only process EVENT messages
    if not isinstance(data, list) or len(data) < 3 or data[0] != "EVENT":
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
        process_command(sender, plaintext)
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
        process_command(sender, plaintext)
    except Exception as e:
        print(f"NIP-17 unwrap failed: {e}")


def process_command(sender_pubkey, plaintext):
    """Route a decrypted message through the LLM and reply."""
    try:
        reply = ask_llm(plaintext)
        print(f"Gerald reply: {reply}")
        send_dm(sender_pubkey, reply)
        print("Reply sent")
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
    ws = websocket.WebSocketApp(
        RELAY,
        on_open=on_open,
        on_message=on_message,
    )
    ws.run_forever()


if __name__ == "__main__":
    start()
