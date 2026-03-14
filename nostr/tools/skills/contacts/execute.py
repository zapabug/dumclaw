#!/usr/bin/env python3
"""
Fetch kind 3 (contact list) for the admin pubkey and save a
name→pubkey lookup JSON file for Gerald.

Run weekly via cron:
  0 3 * * 1  cd /home/tugajoe/develop/dumclaw && venv/bin/python3 fetch_contacts.py

The script:
  1. Fetches the kind 3 event for the admin pubkey from public relays.
  2. Extracts all p-tagged pubkeys (the follow list).
  3. Fetches kind 0 (profile metadata) for each followed pubkey.
  4. Builds a {display_name: pubkey} mapping.
  5. Saves to contacts.json for Gerald's listener to use.
"""

import json
import time
import websocket

# Admin pubkey — fetch their follow list
ADMIN_PUBKEY = "d83b5ef189df7e884627294b752969547814c3cfe38995cf207c040e03bbe7a4"

# Relays to query
RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol",
    "wss://relay.nostr.band",
]

OUTPUT_FILE = "contacts.json"

# Timeout for each relay query (seconds)
QUERY_TIMEOUT = 10


def query_relay(relay_url, filters, timeout=QUERY_TIMEOUT):
    """Send a REQ to a relay and collect events until EOSE or timeout."""
    events = []
    got_eose = [False]

    def on_open(ws):
        req = ["REQ", "fetch-1", filters]
        ws.send(json.dumps(req))

    def on_message(ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        if isinstance(data, list):
            if data[0] == "EVENT" and len(data) >= 3:
                events.append(data[2])
            elif data[0] == "EOSE":
                got_eose[0] = True
                ws.close()

    def on_error(ws, error):
        pass

    try:
        ws = websocket.WebSocketApp(
            relay_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
        )

        import threading
        t = threading.Thread(target=ws.run_forever)
        t.daemon = True
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            ws.close()
            t.join(timeout=2)

    except Exception as e:
        print(f"  Error querying {relay_url}: {e}")

    return events


def fetch_kind3(pubkey):
    """Fetch the kind 3 contact list for a pubkey."""
    filters = {"kinds": [3], "authors": [pubkey], "limit": 1}

    for relay in RELAYS:
        print(f"  Querying {relay} for kind 3...")
        events = query_relay(relay, filters)
        if events:
            # Return the most recent one
            events.sort(key=lambda e: e.get("created_at", 0), reverse=True)
            return events[0]

    return None


def extract_followed_pubkeys(kind3_event):
    """Extract p-tagged pubkeys from a kind 3 event."""
    pubkeys = []
    for tag in kind3_event.get("tags", []):
        if isinstance(tag, list) and len(tag) >= 2 and tag[0] == "p":
            pubkeys.append(tag[1])
    return pubkeys


def fetch_profiles(pubkeys, batch_size=50):
    """Fetch kind 0 profiles for a list of pubkeys."""
    profiles = {}

    # Process in batches
    for i in range(0, len(pubkeys), batch_size):
        batch = pubkeys[i:i + batch_size]
        filters = {"kinds": [0], "authors": batch}

        for relay in RELAYS:
            print(f"  Querying {relay} for {len(batch)} profiles (batch {i // batch_size + 1})...")
            events = query_relay(relay, filters, timeout=15)

            for event in events:
                pk = event.get("pubkey")
                if pk and pk not in profiles:
                    try:
                        meta = json.loads(event.get("content", "{}"))
                        profiles[pk] = meta
                    except json.JSONDecodeError:
                        pass

            if len(profiles) >= len(pubkeys):
                break

        # Small delay between batches
        time.sleep(1)

    return profiles


def build_contacts(profiles):
    """
    Build a name→pubkey lookup dict.

    Tries display_name first, then name, then nip05 username.
    Skips entries without any usable name.
    """
    contacts = {}

    for pubkey, meta in profiles.items():
        # Try multiple name fields
        name = (
            meta.get("display_name")
            or meta.get("displayName")
            or meta.get("name")
            or ""
        ).strip()

        if not name:
            # Try extracting from nip05
            nip05 = meta.get("nip05", "")
            if nip05 and "@" in nip05:
                name = nip05.split("@")[0].strip()

        if not name:
            # Use first 8 chars of pubkey as fallback
            name = f"anon_{pubkey[:8]}"

        # Handle duplicate names by appending pubkey suffix
        original_name = name
        counter = 2
        while name.lower() in {k.lower() for k in contacts}:
            name = f"{original_name}_{counter}"
            counter += 1

        contacts[name] = pubkey

    return contacts


def main():
    print(f"Fetching contacts for admin: {ADMIN_PUBKEY[:16]}...")

    # Step 1: Get kind 3
    print("\n[1/3] Fetching kind 3 contact list...")
    kind3 = fetch_kind3(ADMIN_PUBKEY)

    if not kind3:
        print("ERROR: Could not fetch kind 3 event. Aborting.")
        return

    followed = extract_followed_pubkeys(kind3)
    print(f"  Found {len(followed)} followed pubkeys")

    # Step 2: Fetch profiles
    print(f"\n[2/3] Fetching profiles for {len(followed)} pubkeys...")
    profiles = fetch_profiles(followed)
    print(f"  Got {len(profiles)} profiles")

    # Step 3: Build and save contacts
    print("\n[3/3] Building contacts lookup...")
    contacts = build_contacts(profiles)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(contacts)} contacts to {OUTPUT_FILE}")

    # Show a sample
    sample = list(contacts.items())[:10]
    for name, pk in sample:
        print(f"  {name} → {pk[:16]}...")


if __name__ == "__main__":
    main()
