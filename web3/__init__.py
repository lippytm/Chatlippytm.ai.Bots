"""
Chatlippytm.ai.Bots – Web3 Integration Package

Provides wallet-based authentication, blockchain access management,
and tokenized learning-progress utilities for AI workshop platforms.
"""

from .wallet_auth import WalletAuthManager, TokenRegistry

__all__ = [
    "WalletAuthManager",
    "TokenRegistry",
]
