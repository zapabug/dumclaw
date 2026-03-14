import time
import threading
import json

EVENT_LOG = []
LOCK = threading.Lock()
MAX_EVENTS = 300


def log_event(event_type, data):
    event = {
        "time": int(time.time()),
        "type": event_type,
        "data": data
    }

    with LOCK:
        EVENT_LOG.append(event)
        if len(EVENT_LOG) > MAX_EVENTS:
            EVENT_LOG.pop(0)


def get_events():
    with LOCK:
        return list(EVENT_LOG)


def get_realtime_events():
    """Get events for realtime monitoring with formatted timestamps."""
    with LOCK:
        events = []
        for event in EVENT_LOG:
            event_copy = event.copy()
            event_copy["time"] = time.strftime("%H:%M:%S", time.localtime(event["time"]))
            events.append(event_copy)
        return events


def get_tool_decisions():
    """Get only tool decision events for monitoring."""
    with LOCK:
        return [e for e in EVENT_LOG if e["type"] in ["tool_decision", "action_decision"]]


def get_recent_events(limit=50):
    """Get most recent events."""
    with LOCK:
        return list(EVENT_LOG[-limit:])