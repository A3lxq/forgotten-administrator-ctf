#!/usr/bin/env python3
"""flagcrypto.py — encrypt/decrypt tool for The Forgotten Administrator.

Used both to build the challenge's encrypted flags (instructor side) and
by players to decrypt what they find (this exact file ships to players —
it contains no secrets itself, just the format logic).

Scheme (standard, documented primitives only, via the `cryptography`
library): scrypt for password-based key derivation, AES-256-GCM for
authenticated encryption. Nothing here is a homemade cipher.

File format (binary):
    b"SYNC1"            5-byte magic
    salt                16 bytes, for scrypt
    nonce               12 bytes, for AES-GCM
    ciphertext||tag      rest of the file

Usage:
    python3 flagcrypto.py encrypt <password> <in-file> <out-file.enc>
    python3 flagcrypto.py decrypt <password> <in-file.enc> <out-file>
    python3 flagcrypto.py decrypt <password> <in-file.enc> -   # print to stdout
"""
from __future__ import annotations

import sys

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"SYNC1"
SALT_LEN = 16
NONCE_LEN = 12
KEY_LEN = 32  # AES-256


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_LEN, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(password: str, plaintext: bytes) -> bytes:
    import os

    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return MAGIC + salt + nonce + ciphertext


def decrypt_bytes(password: str, blob: bytes) -> bytes:
    if not blob.startswith(MAGIC):
        raise ValueError("Not a recognized flagcrypto file (bad magic).")
    rest = blob[len(MAGIC):]
    salt, nonce, ciphertext = (
        rest[:SALT_LEN],
        rest[SALT_LEN:SALT_LEN + NONCE_LEN],
        rest[SALT_LEN + NONCE_LEN:],
    )
    key = _derive_key(password, salt)
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag as exc:
        raise ValueError(
            "Decryption failed: wrong password, or the file is corrupted."
        ) from exc


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[1] not in ("encrypt", "decrypt"):
        print(__doc__)
        return 2

    _, mode, password, in_path, out_path = argv

    with open(in_path, "rb") as f:
        data = f.read()

    if mode == "encrypt":
        result = encrypt_bytes(password, data)
    else:
        try:
            result = decrypt_bytes(password, data)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    if out_path == "-":
        sys.stdout.buffer.write(result)
    else:
        with open(out_path, "wb") as f:
            f.write(result)
        print(f"Wrote {len(result)} bytes to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
