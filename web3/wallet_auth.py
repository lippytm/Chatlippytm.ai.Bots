"""
WalletAuthManager – Web3 wallet-based authentication for workshop participants.

Provides:
- EIP-191 personal_sign challenge/verify flow (signature verification
  implemented with pure-Python cryptography so no web3.py runtime is
  required for the test suite; swap in ``eth_account`` for production).
- Role-based access control stored per wallet address.
- TokenRegistry for minting/burning ERC-20-style progress tokens.

Design
------
The module is intentionally transport-agnostic: callers create the
challenge, send it to the browser wallet (e.g. MetaMask), receive the
signature back, and then call ``verify_login`` to confirm identity.

    manager = WalletAuthManager()

    # Step 1 – frontend requests a challenge
    challenge = manager.create_challenge("0xABCDEF…")

    # Step 2 – user signs the challenge in their wallet and returns sig
    session = manager.verify_login("0xABCDEF…", signature)

    # Step 3 – check workshop access
    manager.grant_role("0xABCDEF…", "participant")
    ok = manager.has_role("0xABCDEF…", "participant")  # True
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session token helpers
# ---------------------------------------------------------------------------

_SESSION_TTL_SECONDS = int(os.getenv("WEB3_SESSION_TTL", "3600"))
_CHALLENGE_TTL_SECONDS = int(os.getenv("WEB3_CHALLENGE_TTL", "300"))
_SECRET_KEY = os.getenv("WEB3_SECRET_KEY", secrets.token_hex(32))


def _sign_token(payload: str) -> str:
    """HMAC-SHA256 MAC over payload using the server secret key."""
    return hmac.new(
        _SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class WalletSession:
    """Represents an active workshop session for a wallet holder."""

    address: str
    roles: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + _SESSION_TTL_SECONDS)
    token: str = ""

    def is_valid(self) -> bool:
        return time.time() < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "roles": self.roles,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "token": self.token,
        }


# ---------------------------------------------------------------------------
# WalletAuthManager
# ---------------------------------------------------------------------------


class WalletAuthManager:
    """Manages wallet-based logins and role assignments for workshop access."""

    def __init__(self) -> None:
        # pending challenges: address -> (challenge_str, expires_at)
        self._challenges: dict[str, tuple[str, float]] = {}
        # active sessions: address -> WalletSession
        self._sessions: dict[str, WalletSession] = {}
        # role assignments: address -> set of role strings
        self._roles: dict[str, set[str]] = {}

    # ------------------------------------------------------------------
    # Challenge / verify
    # ------------------------------------------------------------------

    def create_challenge(self, address: str) -> str:
        """Generate a one-time sign-in challenge for the given wallet address.

        The returned string should be presented to the user's wallet for
        signing via ``personal_sign`` (EIP-191).

        Parameters
        ----------
        address:
            Normalised (lowercase) Ethereum-style wallet address.

        Returns
        -------
        str
            Challenge message to be signed by the wallet.
        """
        address = address.lower()
        nonce = secrets.token_hex(16)
        expires_at = time.time() + _CHALLENGE_TTL_SECONDS
        challenge = (
            f"Sign in to Chatlippytm AI Workshop\n"
            f"Address: {address}\n"
            f"Nonce: {nonce}\n"
            f"Expires: {int(expires_at)}"
        )
        self._challenges[address] = (challenge, expires_at)
        logger.info("[WalletAuth] Challenge created for %s", address)
        return challenge

    def verify_login(self, address: str, signature: str) -> WalletSession | None:
        """Verify a signed challenge and open a workshop session.

        In a production deployment this method calls ``eth_account.messages``
        to recover the signing address and compare it with ``address``.
        Here we perform a server-side HMAC check so the module can run in
        environments without the ``eth_account`` package.

        Parameters
        ----------
        address:
            The wallet address claiming identity.
        signature:
            Hex-encoded signature returned by the wallet after signing the
            challenge string from :meth:`create_challenge`.

        Returns
        -------
        WalletSession or None
            A valid session if verification succeeds, ``None`` otherwise.
        """
        address = address.lower()
        entry = self._challenges.get(address)
        if entry is None:
            logger.warning("[WalletAuth] No pending challenge for %s", address)
            return None

        challenge, expires_at = entry
        if time.time() > expires_at:
            logger.warning("[WalletAuth] Challenge expired for %s", address)
            del self._challenges[address]
            return None

        # Verify: signature must equal HMAC(challenge) for test/dev mode.
        # In production replace this block with eth_account.Account.recover_message.
        expected = _sign_token(challenge)
        if not hmac.compare_digest(signature, expected):
            logger.warning("[WalletAuth] Invalid signature from %s", address)
            return None

        del self._challenges[address]

        session_token = _sign_token(f"{address}:{time.time()}")
        session = WalletSession(
            address=address,
            roles=list(self._roles.get(address, [])),
            token=session_token,
        )
        self._sessions[address] = session
        logger.info("[WalletAuth] Session opened for %s", address)
        return session

    def get_session(self, address: str) -> WalletSession | None:
        """Return the active session for *address*, or ``None`` if expired."""
        address = address.lower()
        session = self._sessions.get(address)
        if session and not session.is_valid():
            del self._sessions[address]
            return None
        return session

    def revoke_session(self, address: str) -> None:
        """Terminate an active session."""
        self._sessions.pop(address.lower(), None)
        logger.info("[WalletAuth] Session revoked for %s", address)

    # ------------------------------------------------------------------
    # Role-based access control
    # ------------------------------------------------------------------

    def grant_role(self, address: str, role: str) -> None:
        """Assign *role* to *address*."""
        address = address.lower()
        self._roles.setdefault(address, set()).add(role)
        logger.info("[WalletAuth] Role '%s' granted to %s", role, address)

    def revoke_role(self, address: str, role: str) -> None:
        """Remove *role* from *address*."""
        address = address.lower()
        self._roles.get(address, set()).discard(role)

    def has_role(self, address: str, role: str) -> bool:
        """Return ``True`` if *address* holds *role*."""
        return role in self._roles.get(address.lower(), set())

    def list_roles(self, address: str) -> list[str]:
        """Return all roles currently assigned to *address*."""
        return sorted(self._roles.get(address.lower(), set()))

    # ------------------------------------------------------------------
    # Helpers for generating the expected test signature
    # ------------------------------------------------------------------

    def sign_challenge(self, challenge: str) -> str:
        """Generate the expected HMAC signature for a challenge string.

        This is the server-side equivalent of what a wallet would produce
        in dev/test mode.  Do **not** expose this in production APIs.
        """
        return _sign_token(challenge)


# ---------------------------------------------------------------------------
# TokenRegistry  –  ERC-20-style progress tokenisation
# ---------------------------------------------------------------------------


class TokenRegistry:
    """Lightweight in-process ledger for tokenised learning progress.

    Each participant's learning milestones can be rewarded with named
    tokens.  The registry records balances and provides mint/burn helpers
    that can be mirrored to an on-chain contract via an event hook.

    Parameters
    ----------
    on_chain_callback:
        Optional callable invoked with ``(address, token_name, delta)``
        whenever the ledger changes.  Use this to forward events to a
        blockchain bridge in production.
    """

    def __init__(
        self,
        on_chain_callback: Any | None = None,
    ) -> None:
        # ledger: address -> {token_name: balance}
        self._ledger: dict[str, dict[str, int]] = {}
        self._callback = on_chain_callback

    def mint(self, address: str, token_name: str, amount: int = 1) -> int:
        """Award *amount* tokens to *address*; returns the new balance."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        address = address.lower()
        bucket = self._ledger.setdefault(address, {})
        bucket[token_name] = bucket.get(token_name, 0) + amount
        new_balance = bucket[token_name]
        logger.info(
            "[TokenRegistry] Minted %d %s for %s (balance=%d)",
            amount, token_name, address, new_balance,
        )
        if self._callback:
            self._callback(address, token_name, amount)
        return new_balance

    def burn(self, address: str, token_name: str, amount: int = 1) -> int:
        """Remove *amount* tokens from *address*; returns the new balance."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        address = address.lower()
        bucket = self._ledger.get(address, {})
        current = bucket.get(token_name, 0)
        if amount > current:
            raise ValueError(
                f"Insufficient balance: have {current}, want to burn {amount}"
            )
        bucket[token_name] = current - amount
        new_balance = bucket[token_name]
        logger.info(
            "[TokenRegistry] Burned %d %s from %s (balance=%d)",
            amount, token_name, address, new_balance,
        )
        if self._callback:
            self._callback(address, token_name, -amount)
        return new_balance

    def balance(self, address: str, token_name: str) -> int:
        """Return current token balance for *address*."""
        return self._ledger.get(address.lower(), {}).get(token_name, 0)

    def portfolio(self, address: str) -> dict[str, int]:
        """Return all token balances for *address*."""
        return dict(self._ledger.get(address.lower(), {}))

    def transfer(
        self,
        from_address: str,
        to_address: str,
        token_name: str,
        amount: int = 1,
    ) -> None:
        """Transfer *amount* tokens between two addresses."""
        self.burn(from_address, token_name, amount)
        self.mint(to_address, token_name, amount)
