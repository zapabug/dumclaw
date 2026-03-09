from flask import Flask, render_template, request, jsonify
import json

from llm import ask_llm, TOOL_PROMPT, GERALD_PROMPT
from tools import get_weather

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    message = request.json["message"]

    print("USER:", message)

    tool_response = ask_llm(message, TOOL_PROMPT)

    print("TOOL RESPONSE:", tool_response)

    try:

        tool_call = json.loads(tool_response)

        if tool_call.get("tool") == "get_weather":

            result = get_weather()

            print("WEATHER RESULT:", result)

            enriched_message = f"""
The weather right now is {result}.

User asked: {message}
"""

            reply = ask_llm(enriched_message, GERALD_PROMPT)

            return jsonify({"reply": reply})

    except Exception as e:

        print("TOOL PARSE ERROR:", e)

    reply = ask_llm(message, GERALD_PROMPT)

    return jsonify({"reply": reply})


if __name__ == "__main__":

    print("Starting Gerald server...")

    app.run(host="0.0.0.0", port=5050, debug=True)
