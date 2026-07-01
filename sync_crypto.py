"""Cifrado para sincronización LiBooks (AES-GCM + PBKDF2)."""

import base64
import hashlib
import json
import os
from typing import Any, Dict, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SYNC_VERSION = 1
SALT_BYTES = 16
NONCE_BYTES = 12
KDF_ITERATIONS = 480_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def make_verifier(passphrase: str, salt: bytes) -> str:
    digest = hashlib.sha256(_derive_key(passphrase, salt)).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def verify_passphrase(passphrase: str, salt_b64: str, verifier: str) -> bool:
    try:
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        return make_verifier(passphrase, salt) == verifier
    except (ValueError, TypeError):
        return False


def encrypt_payload(data: Dict[str, Any], passphrase: str, salt: bytes) -> bytes:
    key = _derive_key(passphrase, salt)
    nonce = os.urandom(NONCE_BYTES)
    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return salt + nonce + ciphertext


def decrypt_payload(blob: bytes, passphrase: str) -> Dict[str, Any]:
    if len(blob) < SALT_BYTES + NONCE_BYTES + 1:
        raise ValueError("Archivo de sync inválido")
    salt = blob[:SALT_BYTES]
    nonce = blob[SALT_BYTES:SALT_BYTES + NONCE_BYTES]
    ciphertext = blob[SALT_BYTES + NONCE_BYTES:]
    key = _derive_key(passphrase, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    data = json.loads(plaintext.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Payload de sync inválido")
    return data


def new_salt_b64() -> str:
    return base64.urlsafe_b64encode(os.urandom(SALT_BYTES)).decode("ascii")
