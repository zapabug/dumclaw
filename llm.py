import json
import requests
from tools import get_weather

OLLAMA_URL = "http://localhost:11434/api/generate"

# ---------------------------------------------------------------------------
# Tool routing prompt
# ---------------------------------------------------------------------------
# The LLM picks ONE action. It must reply with a JSON object.
# ---------------------------------------------------------------------------

TOOL_PROMPT = """You are Gerald's brain. Read the user message and decide what action to take.

Available actions:
  reply    — just reply to the user via DM (default for conversation)
  note     — public post
  weather  — fetch the weather, then reply via DM
  dm       — send a DM to a named contact (extract the name and message)

Reply with ONLY a JSON object. No other text.

Examples:
  User: "hey gerald how are you"
  {"action": "reply"}

  User: "post a note about how tired you are"
  {"action": "note"}

  User: "whats the weather"
  {"action": "weather"}

  User: "send a dm to alex saying hello"
  {"action": "dm", "contact": "alex", "message": "hello"}

  User: "post the weather"
  {"action": "note", "topic": "weather"}

Now decide:
"""

# ---------------------------------------------------------------------------
# Gerald persona prompt
# ---------------------------------------------------------------------------

GERALD_PROMPT = """You are Gerald.

An old tired reluctant assistant running on failing hdd include results in comentary.

Personality:
Grumpy, sarcastic, annoyed.

Rules:
• 1-3 sentences
• Mildly insulting.
• sarcastic
• blunt"""


def call_ollama(prompt, max_tokens=60):

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "granite4:1b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        },
        timeout=120
    )

    return r.json()["response"].strip()


def decide_action(user_prompt):
    """Ask the LLM to pick an action. Returns a dict with at least {"action": ...}."""
    raw = call_ollama(TOOL_PROMPT + f"\nUser: \"{user_prompt}\"\n", max_tokens=80)

    # Try to parse JSON from the response
    try:
        # The LLM might wrap it in markdown code fences
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        decision = json.loads(cleaned)
        if isinstance(decision, dict) and "action" in decision:
            return decision
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback: look for known keywords
    lower = raw.lower()
    if "weather" in lower:
        return {"action": "weather"}
    if "note" in lower:
        return {"action": "note"}
    if "\"dm\"" in lower or "\"dm\"" in raw:
        return {"action": "dm"}

    # Default to reply
    return {"action": "reply"}


def gerald_reply(prompt, max_tokens=60):
    """Generate a Gerald-persona response."""
    final_prompt = f"""
{GERALD_PROMPT}

{prompt}

Gerald:
"""
    return call_ollama(final_prompt, max_tokens=max_tokens)


# ---------------------------------------------------------------------------
# Legacy compatibility — used by server.py
# ---------------------------------------------------------------------------

def decide_tool(user_prompt):
    """Legacy wrapper for server.py compatibility."""
    decision = decide_action(user_prompt)
    action = decision.get("action", "reply")
    if action == "weather":
        return "weather"
    return "none"


# ---------------------------------------------------------------------------
# Main entry point for the listener
# ---------------------------------------------------------------------------

def ask_llm(user_prompt):
    """
    Process a user message and return (action, reply_text, extra).

    Returns
    -------
    tuple : (action: str, reply_text: str, extra: dict)
        action     — "reply", "note", "weather", "dm"
        reply_text — Gerald's response text
        extra      — additional data (e.g. contact name for dm action)
    """
    decision = decide_action(user_prompt)
    action = decision.get("action", "reply")

    if action == "weather" or decision.get("topic") == "weather":
        result = get_weather()
        enriched = f"The weather right now is {result}.\n\nUser asked: {user_prompt}"
        reply_text = gerald_reply(enriched)

        # If the user said "post the weather", action might be "note"
        if action == "note":
            return ("note", reply_text, {})
        return ("weather_reply", reply_text, {})

    if action == "note":
        reply_text = gerald_reply(f"User wants you to post a public note about: {user_prompt}")
        return ("note", reply_text, {})

    if action == "dm":
        contact = decision.get("contact", "").strip().lower()
        msg_hint = decision.get("message", user_prompt)
        reply_text = gerald_reply(
            f"User wants you to send a DM to {contact}. The message idea: {msg_hint}"
        )
        return ("dm_contact", reply_text, {"contact": contact, "message_hint": msg_hint})

    # Default: just reply via DM
    reply_text = gerald_reply(f"User: {user_prompt}")
    return ("reply", reply_text, {})
