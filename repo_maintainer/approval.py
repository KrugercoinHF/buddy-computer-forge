import base64
import binascii
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .models import VerifiedApproval


class ApprovalNonceStore(Protocol):
    def consume(self, token_id: str, expires_at: datetime) -> bool:
        """Atomically consume a token ID once, returning False for a replay."""
        ...


class SQLiteApprovalNonceStore:
    """Durable, transactional one-time-token store for a single trusted runtime."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser()
        if self.database_path.is_symlink():
            raise PermissionError("approval replay database must not be a symlink")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS consumed_approvals (
                    token_id TEXT PRIMARY KEY,
                    expires_at TEXT NOT NULL
                )
                """
            )
        if os.name == "posix":
            os.chmod(self.database_path, 0o600)

    def consume(self, token_id: str, expires_at: datetime) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        expiry = expires_at.astimezone(timezone.utc).isoformat()
        connection = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM consumed_approvals WHERE expires_at <= ?", (now,))
            connection.execute(
                "INSERT INTO consumed_approvals(token_id, expires_at) VALUES (?, ?)",
                (token_id, expiry),
            )
            connection.execute("COMMIT")
            return True
        except sqlite3.IntegrityError:
            connection.execute("ROLLBACK")
            return False
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()


class Ed25519ApprovalGateway:
    """Verify owner-signed, proposal-scoped approval tokens using a public key only."""

    def __init__(
        self,
        public_key: Ed25519PublicKey | bytes | str | Path,
        *,
        issuer: str,
        audience: str,
        repository: str,
        nonce_store: ApprovalNonceStore,
    ):
        if isinstance(public_key, Ed25519PublicKey):
            self.public_key = public_key
        else:
            key_bytes = Path(public_key).read_bytes() if isinstance(public_key, (str, Path)) else public_key
            if key_bytes.startswith(b"-----BEGIN"):
                loaded = serialization.load_pem_public_key(key_bytes)
                if not isinstance(loaded, Ed25519PublicKey):
                    raise TypeError("approval public key must be Ed25519")
                self.public_key = loaded
            else:
                self.public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
        if not issuer or not audience or not repository:
            raise ValueError("issuer, audience and repository are required")
        self.issuer = issuer
        self.audience = audience
        self.repository = repository
        self.nonce_store = nonce_store

    @staticmethod
    def _decode_segment(segment: str) -> bytes:
        padded = segment + ("=" * (-len(segment) % 4))
        return base64.b64decode(padded, altchars=b"-_", validate=True)

    def verify_approval(
        self,
        approval_token: str,
        proposal_digest: str,
        approved_scope: tuple[str, ...],
    ) -> VerifiedApproval | None:
        try:
            parts = approval_token.split(".")
            if len(parts) != 2 or not all(parts):
                return None
            payload_bytes = self._decode_segment(parts[0])
            signature = self._decode_segment(parts[1])
            self.public_key.verify(signature, payload_bytes)

            claims = json.loads(payload_bytes.decode("utf-8"))
            if not isinstance(claims, dict):
                return None
            canonical = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if canonical != payload_bytes:
                return None

            audience_claim = claims.get("aud")
            audience_matches = (
                audience_claim == self.audience
                or isinstance(audience_claim, list) and self.audience in audience_claim
            )
            scope_claim = claims.get("approved_scope")
            if (
                claims.get("iss") != self.issuer
                or not audience_matches
                or claims.get("repository") != self.repository
                or claims.get("proposal_digest") != proposal_digest
                or not isinstance(claims.get("sub"), str)
                or not claims["sub"].strip()
                or not isinstance(claims.get("jti"), str)
                or not claims["jti"].strip()
                or not isinstance(claims.get("exp"), int)
                or isinstance(claims.get("exp"), bool)
                or not isinstance(scope_claim, list)
                or not all(isinstance(item, str) and item for item in scope_claim)
                or len(scope_claim) != len(set(scope_claim))
                or sorted(scope_claim) != sorted(approved_scope)
            ):
                return None

            expiry = datetime.fromtimestamp(claims["exp"], timezone.utc)
            if expiry <= datetime.now(timezone.utc):
                return None
            if not self.nonce_store.consume(claims["jti"], expiry):
                return None

            return VerifiedApproval(
                subject=claims["sub"],
                proposal_digest=proposal_digest,
                approved_scope=tuple(scope_claim),
                token_id=claims["jti"],
                expires_at=expiry.isoformat(),
                verifier=f"ed25519:{self.issuer}",
            )
        except (
            InvalidSignature,
            ValueError,
            TypeError,
            KeyError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            binascii.Error,
            OverflowError,
        ):
            return None
