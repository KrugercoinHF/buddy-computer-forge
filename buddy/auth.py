import hashlib
import hmac
import secrets
from typing import Optional


def hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def verify_hash(secret: str, hashed: Optional[str]) -> bool:
    if not secret or not hashed:
        return False
    return hmac.compare_digest(hash_secret(secret), hashed)
