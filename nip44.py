"""
NIP-44 v2 decryption for Dumclaw / Gerald.

Implements:
  - secp256k1 ECDH  (via pynostr / coincurve)
  - HKDF-SHA256     (extract via hmac, expand via cryptography)
  - ChaCha20        (via cryptography)
  - HMAC-SHA256     (via hmac + hashlib)
  - NIP-44 padding

Only *decryption* is implemented — Gerald only needs to read
incoming messages, not encrypt outgoing ones (replies use NIP-04).
"""

import base64
import hashlib
import hmac
import math
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand
from cryptography.hazmat.primitives import hashes


# ---------------------------------------------------------------------------
# Conversation key  (long-term, same for a given key pair)
# ---------------------------------------------------------------------------

def get_conversation_key(private_key, public_key_hex: str) -> bytes:
    """
    Derive the NIP-44 conversation key.

    Parameters
    ----------
    private_key : pynostr.key.PrivateKey
        Gerald's private key object (must expose .ecdh()).
    public_key_hex : str
        The *other* party's 32-byte hex pubkey (x-only).

    Returns
    -------
    bytes  – 32-byte conversation key.
    """
    # pynostr's ecdh already returns the raw (unhashed) shared x coordinate
    shared_x = private_key.ecdh(public_key_hex)

    # HKDF-Extract only: HMAC-SHA256(salt, IKM)
    # NIP-44 spec: hkdf_extract(IKM=shared_x, salt=utf8_encode('nip44-v2'))
    return hmac.new(b"nip44-v2", shared_x, hashlib.sha256).digest()


# ---------------------------------------------------------------------------
# Per-message keys
# ---------------------------------------------------------------------------

def get_message_keys(conversation_key: bytes, nonce: bytes):
    """Return (chacha_key, chacha_nonce, hmac_key) from conversation_key + nonce."""
    assert len(conversation_key) == 32, "conversation_key must be 32 bytes"
    assert len(nonce) == 32, "nonce must be 32 bytes"

    hkdf = HKDFExpand(algorithm=hashes.SHA256(), length=76, info=nonce)
    keys = hkdf.derive(conversation_key)

    chacha_key   = keys[0:32]
    chacha_nonce = keys[32:44]
    hmac_key     = keys[44:76]
    return chacha_key, chacha_nonce, hmac_key


# ---------------------------------------------------------------------------
# HMAC with AAD
# ---------------------------------------------------------------------------

def hmac_aad(key: bytes, message: bytes, aad: bytes) -> bytes:
    """HMAC-SHA256 over concat(aad, message)."""
    assert len(aad) == 32, "AAD must be 32 bytes"
    return hmac.new(key, aad + message, hashlib.sha256).digest()


# ---------------------------------------------------------------------------
# Padding helpers
# ---------------------------------------------------------------------------

def _calc_padded_len(unpadded_len: int) -> int:
    if unpadded_len <= 32:
        return 32
    next_power = 1 << (math.floor(math.log2(unpadded_len - 1)) + 1)
    chunk = 32 if next_power <= 256 else next_power // 8
    return chunk * (math.floor((unpadded_len - 1) / chunk) + 1)


def _unpad(padded: bytes) -> str:
    unpadded_len = struct.unpack(">H", padded[0:2])[0]
    if unpadded_len == 0:
        raise ValueError("invalid padding: zero length")
    unpadded = padded[2 : 2 + unpadded_len]
    if len(unpadded) != unpadded_len:
        raise ValueError("invalid padding: length mismatch")
    expected_padded_len = 2 + _calc_padded_len(unpadded_len)
    if len(padded) != expected_padded_len:
        raise ValueError(
            f"invalid padding: expected {expected_padded_len}, got {len(padded)}"
        )
    return unpadded.decode("utf-8")


# ---------------------------------------------------------------------------
# Decode base64 payload
# ---------------------------------------------------------------------------

def _decode_payload(payload: str):
    """Decode a NIP-44 base64 payload into (nonce, ciphertext, mac)."""
    if not payload or payload[0] == "#":
        raise ValueError("unknown version or unsupported encoding")

    plen = len(payload)
    if plen < 132 or plen > 87472:
        raise ValueError(f"invalid payload size: {plen}")

    data = base64.b64decode(payload)
    dlen = len(data)
    if dlen < 99 or dlen > 65603:
        raise ValueError(f"invalid data size: {dlen}")

    version = data[0]
    if version != 2:
        raise ValueError(f"unknown version: {version}")

    nonce      = data[1:33]
    ciphertext = data[33 : dlen - 32]
    mac        = data[dlen - 32 : dlen]
    return nonce, ciphertext, mac


# ---------------------------------------------------------------------------
# ChaCha20 (counter = 0)
# ---------------------------------------------------------------------------

def _chacha20(key: bytes, nonce: bytes, data: bytes) -> bytes:
    """ChaCha20 with initial counter = 0."""
    algorithm = algorithms.ChaCha20(key, b"\x00\x00\x00\x00" + nonce)
    cipher = Cipher(algorithm, mode=None)
    decryptor = cipher.decryptor()
    return decryptor.update(data) + decryptor.finalize()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def decrypt(payload: str, conversation_key: bytes) -> str:
    """
    Decrypt a NIP-44 v2 payload.

    Parameters
    ----------
    payload : str
        Base64-encoded NIP-44 ciphertext.
    conversation_key : bytes
        32-byte conversation key from get_conversation_key().

    Returns
    -------
    str – the decrypted plaintext.
    """
    nonce, ciphertext, mac = _decode_payload(payload)
    chacha_key, chacha_nonce, hmac_key = get_message_keys(conversation_key, nonce)

    # Verify MAC
    calculated_mac = hmac_aad(hmac_key, ciphertext, nonce)
    if not hmac.compare_digest(calculated_mac, mac):
        raise ValueError("invalid MAC — message tampered or wrong key")

    # Decrypt
    padded = _chacha20(chacha_key, chacha_nonce, ciphertext)
    return _unpad(padded)
