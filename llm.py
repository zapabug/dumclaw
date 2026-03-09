import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

TOOL_PROMPT = """
Decide which tool is needed.

Tools:
weather
none

Reply with ONE word only.

weather
none
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
• always include tool results in your commentary if provided
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


def decide_tool(user_prompt):

    decision = call_ollama(TOOL_PROMPT + "\nUser: " + user_prompt)

    return decision.strip().lower()


def gerald_reply(prompt):

    final_prompt = f"""
{GERALD_PROMPT}

{prompt}

Gerald:
"""

    return call_ollama(final_prompt)