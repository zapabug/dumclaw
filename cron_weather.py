#!/usr/bin/env python3
"""
Daily morning weather check-in for Gerald.

Fetches the weather, generates a Gerald-persona commentary,
and publishes it as a kind 1 note (public post).

Run daily via cron:
  0 8 * * *  cd /home/tugajoe/develop/dumclaw && venv/bin/python3 cron_weather.py

This is Gerald's "morning status check-in" — a grumpy weather report
posted to nostr every day.
"""

import sys
import time

# Must be imported after path is set
from config import PRIVATE_KEY, PUBLIC_KEY
from tools import get_weather
from llm import gerald_reply

from pynostr.relay_manager import RelayManager
from pynostr.event import Event


# Relays to publish to
RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol",
    "wss://relay.snort.social",
    "ws://127.0.0.1:7777",
]


def publish_note(text):
    """Publish a kind 1 note to relays."""
    relay_manager = RelayManager()

    for relay in RELAYS:
        relay_manager.add_relay(relay)

    relay_manager.open_connections()
    time.sleep(3)

    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    PRIVATE_KEY.sign_event(event)
    relay_manager.publish_event(event)

    time.sleep(3)

    relay_manager.close_connections()

    print(f"NOTE PUBLISHED: {text}")


def main():
    print("Gerald morning weather check-in")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Fetch weather
    try:
        weather = get_weather()
        print(f"Weather: {weather}")
    except Exception as e:
        print(f"Failed to fetch weather: {e}")
        sys.exit(1)

    # Generate Gerald's commentary
    prompt = f"""
It's morning. You just woke up (reluctantly). The weather is: {weather}.

Write a short morning status update about the weather.
This will be posted as a public note on nostr.
Keep it 1-2 sentences. Be grumpy about it.
"""

    try:
        note_text = gerald_reply(prompt, max_tokens=80)
        print(f"Gerald says: {note_text}")
    except Exception as e:
        print(f"LLM failed: {e}")
        sys.exit(1)

    # Publish
    try:
        publish_note(note_text)
        print("Done!")
    except Exception as e:
        print(f"Publish failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
