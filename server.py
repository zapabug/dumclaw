from flask import Flask, render_template, request, jsonify
from llm import decide_tool, gerald_reply
from tools import get_weather

app = Flask(__name__)


@app.route("/chat", methods=["POST"])
def chat():

    message = request.json["message"]

    print("USER:", message)

    decision = decide_tool(message)

    print("TOOL DECISION:", decision)

    if decision == "weather":

        result = get_weather()

        print("WEATHER RESULT:", result)

        enriched = f"""
The weather right now is {result}.

User asked: {message}
"""

        reply = gerald_reply(enriched)

        return jsonify({"reply": reply})

    # no tool needed
    reply = gerald_reply(f"User: {message}")

    return jsonify({"reply": reply})