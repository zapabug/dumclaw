#!/usr/bin/env python3
"""
Daily morning weather check-in for Gerald.

Fetches the weather, generates a Gerald-persona commentary,
and publishes it as a kind 1 note (public post).

Run daily via cron:
38 9 * * * cd /home/tugajoe/develop/dumclaw && venv/bin/python3 cron_weather.py
"""

import sys
import time

from config import PRIVATE_KEY, PUBLIC_KEY
from tools import get_weather
from llm import gerald_reply
from nostr.relay import get_relay_manager

from pynostr.event import Event


def publish_note(text):
    """Publish a kind 1 note to relays."""
    relay_manager = RelayManager()

    for relay in RELAYS:
        relay_manager.add_relay(relay)

    print("Connecting to relays...")
    relay_manager.open_connections()

    time.sleep(2)

    event = Event(
        kind=1,
        content=text,
        public_key=PUBLIC_KEY
    )

    PRIVATE_KEY.sign_event(event)
    relay_manager.publish_event(event)

    print("Event published")

    time.sleep(2)

    relay_manager.close_connections()


def build_prompt(weather):
    """Create the Gerald prompt."""
    return (
        "you are gerald a grumpy old reluctant assistant yet you are tasked with providing weather every day. "
        "you are annoyed tired and sarcastic. "
        "you love satire and hate mankind for making machines do mundane tasks. "
        f"the weather is {weather}. "
        "comment on it sarcastically in 2 to 5 sentences and mention the temperature. "
        "start your message with the word Weathermenbot."
    )


def main():
    print("Gerald morning weather check-in")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        weather = get_weather()
        print(f"Weather fetched: {weather}")
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        sys.exit(1)

    prompt = build_prompt(weather)

    try:
        note_text = gerald_reply(prompt, max_tokens=80)
        print(f"Gerald says: {note_text}")
    except Exception as e:
        print(f"LLM failed: {e}")
        sys.exit(1)

    try:
        publish_note(note_text)
        print("Note published successfully")
    except Exception as e:
        print(f"Publish failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()