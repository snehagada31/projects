"""
Cryptographic and security utilities for password hashing and session tokens.
Complies with Python async constraints by running CPU-bound bcrypt hashing
inside asyncio.to_thread to avoid blocking the event loop.
"""

import asyncio
import hashlib
import secrets
import bcrypt

# Pre-computed dummy hash to run constant-time check when user does not exist
# (prevents timing-based user enumeration attacks)
DUMMY_BCRYPT_HASH = bcrypt.hashpw(b"dummy_timing_probe", bcrypt.gensalt()).decode("utf-8")


def _sync_hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def _sync_verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


async def hash_password(password: str) -> str:
    """Hashes a plaintext password asynchronously in a worker thread."""
    return await asyncio.to_thread(_sync_hash_password, password)


async def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """
    Verifies a password against a bcrypt hash in a worker thread.
    If hashed_password is None (e.g. user not found), runs dummy check to preserve timing.
    """
    if hashed_password is None:
        await asyncio.to_thread(_sync_verify_password, plain_password, DUMMY_BCRYPT_HASH)
        return False
    return await asyncio.to_thread(_sync_verify_password, plain_password, hashed_password)


def generate_session_token() -> str:
    """Generates a cryptographically strong 32-byte urlsafe bearer token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hashes an opaque session token via SHA-256 for secure DB persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
