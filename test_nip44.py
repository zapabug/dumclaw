#!/usr/bin/env python3
"""Quick smoke test for nip44.py using the official NIP-44 test vector."""

from nip44 import get_conversation_key, decrypt
from pynostr.key import PrivateKey

# NIP-44 test vector from the spec
sec1 = "0000000000000000000000000000000000000000000000000000000000000001"
sec2 = "0000000000000000000000000000000000000000000000000000000000000002"
expected_conv_key = "c41c775356fd92eadc63ff5a0dc1da211b268cbea22316767095b2871ea1412d"

pk1 = PrivateKey.from_hex(sec1)
pk2 = PrivateKey.from_hex(sec2)
pub2 = pk2.public_key.hex()

conv_key = get_conversation_key(pk1, pub2)
print(f"Conversation key: {conv_key.hex()}")
print(f"Expected:         {expected_conv_key}")
assert conv_key.hex() == expected_conv_key, "Conversation key mismatch!"
print("✓ Conversation key matches")

# Test decrypt with known payload
payload = "AgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABee0G5VSK0/9YypIObAtDKfYEAjD35uVkHyB0F4DwrcNaCXlCWZKaArsGrY6M9wnuTMxWfp1RTN9Xga8no+kF5Vsb"
plaintext = decrypt(payload, conv_key)
print(f"Decrypted: {repr(plaintext)}")
assert plaintext == "a", f"Decryption mismatch: got {repr(plaintext)}"
print("✓ Decryption matches")

print("\nAll NIP-44 tests passed!")
