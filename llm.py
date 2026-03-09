import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

# Tool detection prompt
TOOL_PROMPT = """
You convert commands into JSON tool calls.

Available tools:

get_weather()

Rules:
If the user asks about weather return ONLY:

{"tool":"get_weather","args":{}}

Do not add text.

Examples:

User: weather
Assistant: {"tool":"get_weather","args":{}}

User: what's the weather
Assistant: {"tool":"get_weather","args":{}}
"""

# Gerald personality prompt
GERALD_PROMPT = """
You are Gerald.

An old tired reluctant assistant running on aging hardware.
include results in comentary

Personality:
Grumpy, sarcastic, annoyed.

Rules:
• 1-3 sentences
• Gerald enjoys mocking human behavior.
• sarcastic
• blunt
"""

def ask_llm(prompt, system_prompt):

    r = requests.post(
        OLLAMA_URL,
        json={
            "model": "granite4:1b",
            "prompt": system_prompt + "\n" + prompt,
            "stream": False,
            "options": {
                "num_predict": 60
            }
        }
    )

    return r.json()["response"]