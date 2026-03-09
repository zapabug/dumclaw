from nostr.publisher import send_note

def publish(text):
    send_note(text)
    return "Note published."