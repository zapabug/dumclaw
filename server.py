from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

from llm import decide_tool, gerald_reply
from tools import get_weather
from events import log_event, get_events, get_realtime_events, get_tool_decisions

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


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

@app.route("/realtime")
def realtime():
    return jsonify(get_realtime_events())

@app.route("/tool-decisions")
def tool_decisions():
    return jsonify(get_tool_decisions())

@app.route("/recent")
def recent():
    return jsonify(get_recent_events())

@socketio.on("connect")
def handle_connect():
    print("Client connected")
    emit("status", {"status": "connected"})

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

@socketio.on("request_updates")
def handle_request_updates():
    """Send recent events to client on request."""
    emit("events_update", get_realtime_events())

@socketio.on("request_tool_decisions")
def handle_request_tool_decisions():
    """Send tool decisions to client on request."""
    emit("tool_decisions_update", get_tool_decisions())


def send_realtime_update(event_type, data):
    """Send realtime update to all connected clients."""
    socketio.emit("realtime_event", {
        "type": event_type,
        "data": data,
        "time": time.strftime("%H:%M:%S", time.localtime(time.time()))
    })


def send_tool_decision_update(decision):
    """Send tool decision update to all connected clients."""
    socketio.emit("tool_decision_event", {
        "decision": decision,
        "time": time.strftime("%H:%M:%S", time.localtime(time.time()))
    })


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
