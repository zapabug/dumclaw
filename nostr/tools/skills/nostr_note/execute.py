import json
import time
from nostr.publisher import send_note
from config import PRIVATE_KEY, PUBLIC_KEY

def execute(note_content=""):
    """
    Post a public note.
    
    Parameters:
    - note_content: str - the content of the note to post
    
    Returns a string response.
    """
    # If no content provided, return a placeholder
    if not note_content:
        return "Would post a public note to Nostr (no content provided)"
    
    try:
        # Send the note using the publisher
        send_note(note_content)
        return f"Note posted: {note_content[:50]}{'...' if len(note_content) > 50 else ''}"
    except Exception as e:
        return f"Failed to post note: {str(e)}"