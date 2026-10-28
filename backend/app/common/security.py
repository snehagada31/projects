"""
Cryptographic and security utilities for password hashing and session tokens.
Simplified implementation using hashlib to avoid external bcrypt dependency.
"""

import asyncio
import hashlib
import secrets
import hmac

# Dummy hash for timing attack mitigation using the same scheme as real hashes.
# Format: "salt$hash"
_DUMMY_SALT = "dummysalt"
_DUMMY_HASH = hashlib.pbkdf2_hmac(
    "sha256", b"dummy_timing_probe", _DUMMY_SALT.encode(), 100_000
).hex()
DUMMY_PASSWORD_HASH = f"{_DUMMY_SALT}${_DUMMY_HASH}"


def _sync_hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256.

    Returns a string ``salt$hash`` where ``salt`` is a random hex string.
    """
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode(), 100_000
    ).hex()
    return f"{salt}${pwd_hash}"


def _sync_verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a password against a stored ``salt$hash`` value.

    Uses constant‑time comparison to prevent timing attacks.
    """
    try:
        salt, hash_val = stored_hash.split("$")
    except ValueError:
        return False
    calc_hash = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode(), 100_000
    ).hex()
    return hmac.compare_digest(calc_hash, hash_val)


async def hash_password(password: str) -> str:
    """Hash a plaintext password asynchronously in a worker thread."""
    return await asyncio.to_thread(_sync_hash_password, password)


async def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a password asynchronously.

    If ``hashed_password`` is ``None`` (e.g., user not found), performs a dummy
    verification to keep timing consistent.
    """
    if hashed_password is None:
        # Run dummy verification to mitigate timing attacks.
        await asyncio.to_thread(_sync_verify_password, plain_password, DUMMY_PASSWORD_HASH)
        return False
    return await asyncio.to_thread(_sync_verify_password, plain_password, hashed_password)


def generate_session_token() -> str:
    """Generates a cryptographically strong 32-byte URL‑safe bearer token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hashes an opaque session token via SHA‑256 for secure DB persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
