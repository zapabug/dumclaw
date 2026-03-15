import json
import os
from nostr.publisher import send_dm
from config import PRIVATE_KEY, PUBLIC_KEY

def execute(contact, message_hint):
    """
    Send a direct message to a contact.
    
    Parameters:
    - contact: str - name of the contact to message
    - message_hint: str - hint about what to say
    
    Returns a string response.
    """
    # Load contacts from the standard location
    contacts_file = "nostr/tools/contacts.json"
    
    if not os.path.exists(contacts_file):
        return f"Contacts file not found at {contacts_file}"
    
    try:
        with open(contacts_file, "r") as f:
            contacts = json.load(f)
    except Exception as e:
        return f"Failed to load contacts: {str(e)}"
    
    # Look up the contact (case-insensitive)
    contact_lower = contact.lower().strip()
    contact_pubkey = None
    
    # Exact match first
    for contact_name, pubkey in contacts.items():
        if contact_name.lower() == contact_lower:
            contact_pubkey = pubkey
            break
    
    # Partial match fallback
    if not contact_pubkey:
        for contact_name, pubkey in contacts.items():
            if contact_lower in contact_name.lower():
                contact_pubkey = pubkey
                break
    
    if not contact_pubkey:
        return f"Contact '{contact}' not found in contacts.json"
    
    try:
        # Send the DM using the publisher
        send_dm(contact_pubkey, f"[Gerald] {message_hint}")
        return f"DM sent to {contact}"
    except Exception as e:
        return f"Failed to send DM to {contact}: {str(e)}"