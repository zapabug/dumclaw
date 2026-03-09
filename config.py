import os
from dotenv import load_dotenv
from pynostr.key import PrivateKey

load_dotenv()

secret = os.getenv("NOSTR_SECRET")

if not secret:
    raise RuntimeError("Missing NOSTR_SECRET")

PRIVATE_KEY = PrivateKey.from_nsec(secret)
PUBLIC_KEY = PRIVATE_KEY.public_key.hex()