import time
import threading
import json
import uuid
import os

EVENT_LOG = []
LOCK = threading.Lock()
MAX_EVENTS = 300
PERSISTENT_FILE = "events.log"

# Load persistent events if file exists
if os.path.exists(PERSISTENT_FILE):
    try:
        with open(PERSISTENT_FILE, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    EVENT_LOG.append(event)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass


def record_event(event_type, data, run_id=None):
    """
    Central event recording function that logs, broadcasts, and persists events.
    
    Args:
        event_type (str): Type of event (e.g., 'user_message', 'tool_decision')
        data (any): Event data
        run_id (str, optional): Run ID for tracing
    """
    event = {
        "type": event_type,
        "data": data,
        "time": time.time(),
        "run_id": run_id
    }

    # Log to memory
    with LOCK:
        EVENT_LOG.append(event)
        if len(EVENT_LOG) > MAX_EVENTS:
            EVENT_LOG.pop(0)

    # Persist to file
    try:
        with open(PERSISTENT_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass

    # Broadcast via Socket.IO
    try:
        from flask_socketio import socketio
        socketio.emit("agent_event", {
            "type": event_type,
            "data": data,
            "time": time.strftime("%H:%M:%S", time.localtime(event["time"])),
            "run_id": run_id
        })
    except Exception:
        pass


def log_event(event_type, data):
    """Legacy wrapper for backward compatibility."""
    record_event(event_type, data)


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


def get_agent_state():
    """Get current agent state snapshot."""
    with LOCK:
        return {
            "tools_loaded": ["weather"],  # Update this as you add more tools
            "memory_items": 0,  # Add memory tracking if implemented
            "events_logged": len(EVENT_LOG),
            "run_id": EVENT_LOG[-1]["run_id"] if EVENT_LOG else None
        }


def start_run():
    """Start a new run with a unique ID."""
    run_id = str(uuid.uuid4())
    record_event("run_start", {"run_id": run_id}, run_id=run_id)
    return run_id


def end_run(run_id):
    """End a run."""
    record_event("run_end", {"run_id": run_id}, run_id=run_id)


def record_latency(tool, seconds, run_id=None):
    """Record tool latency."""
    record_event("tool_latency", {"tool": tool, "seconds": seconds}, run_id=run_id)


def record_error(error, run_id=None):
    """Record an error event."""
    record_event("error", str(error), run_id=run_id)


def record_reasoning(text, run_id=None):
    """Record reasoning trace."""
    record_event("reasoning", text, run_id=run_id)


def clear_events():
    """Clear all events from memory."""
    with LOCK:
        global EVENT_LOG
        EVENT_LOG = []