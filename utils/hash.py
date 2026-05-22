import os
import sys

# Attempt to resolve the native Unix crypt library; fallback gracefully if on Windows
try:
    import crypt
    HAS_NATIVE_CRYPT = True
except ImportError:
    HAS_NATIVE_CRYPT = False
    try:
        from passlib.hash import sha512_crypt
    except ImportError:
        print("[!] Cross-Platform Warning: You are running this on a non-Linux machine.")
        print("    To compile secure SHA-512 server password hashes here, please run:")
        print("    `pip install passlib` or `python3 -m pip install passlib`")
        sys.exit(1)

def generate_sha512_hash(plaintext_password: str) -> str:
    """Generates an OS-compliant secure SHA-512 password crypt hash string ($6$)."""
    if HAS_NATIVE_CRYPT:
        # Native Linux crypt compilation using a random generated OS salt signature
        return crypt.crypt(plaintext_password, crypt.mksalt(crypt.METHOD_SHA512))
    else:
        # Cross-platform Windows fallback via Passlib library using explicit round compliance
        return sha512_crypt.using(rounds=5000).hash(plaintext_password)