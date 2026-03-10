import time
import threading

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