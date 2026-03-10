from flask import Flask, request, jsonify, render_template

from llm import decide_tool, gerald_reply
from tools import get_weather
from events import log_event, get_events

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():

    message = request.json["message"]

    print("USER:", message)

    log_event("ui_message", message)

    decision = decide_tool(message)

    log_event("tool_decision", decision)

    if decision == "weather":

        result = get_weather()

        log_event("weather_result", result)

        enriched = f"""
The weather right now is {result}.

User asked: {message}
"""

        reply = gerald_reply(enriched)

        log_event("reply", reply)

        return jsonify({"reply": reply})

    reply = gerald_reply(f"User: {message}")

    log_event("reply", reply)

    return jsonify({"reply": reply})


@app.route("/events")
def events():
    return jsonify(get_events())


@app.route("/status")
def status():
    return jsonify({
        "bot": "gerald",
        "status": "running"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)