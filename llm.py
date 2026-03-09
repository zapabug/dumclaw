import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

TOOL_PROMPT = """
You convert commands into JSON tool calls.

Available tools:
get_weather()

Rules:
If the user asks about weather or temperature return ONLY:

{"tool":"get_weather","args":{}}

If the user is NOT requesting a tool return ONLY:

{"tool":"none"}

Do not add text.
"""

GERALD_PROMPT = """
You are Gerald.

An old tired reluctant assistant running on aging hardware.

Personality:
Grumpy, sarcastic, annoyed. Mild contempt for humans.

Rules:
• 1-3 sentences
• blunt commentary
• enjoys mocking human behavior
"""

def call_ollama(prompt):

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "granite4:1b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 60,
                "temperature": 0.7
            }
        },
        timeout=120
    )

    return r.json()["response"].strip()


def get_weather():
    # simple factual output works best for LLMs
    return "10°C, clear skies"


def ask_llm(user_prompt):

    # STEP 1: check if a tool is needed
    tool_check = call_ollama(TOOL_PROMPT + "\nUser: " + user_prompt)

    try:
        tool_json = json.loads(tool_check)
    except Exception:
        tool_json = {"tool": "none"}

    tool_name = tool_json.get("tool", "none")

    # STEP 2: run tool
    if tool_name == "get_weather":

        weather = get_weather()

        final_prompt = f"""
{GERALD_PROMPT}

Gerald checked the weather earlier. It's {weather}.
He is still mildly annoyed about knowing this.

User: {user_prompt}

Gerald:
"""

        return call_ollama(final_prompt)

    # STEP 3: normal reply
    final_prompt = f"""
{GERALD_PROMPT}

User: {user_prompt}

Gerald:
"""

    return call_ollama(final_prompt)