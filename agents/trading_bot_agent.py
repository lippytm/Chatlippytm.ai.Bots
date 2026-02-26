"""
TradingBotAgent – AI-powered trading bot manager for crypto, stocks, and forex.

Uses AI to analyse market data, build and manage trading strategies, and
supports reinforcement learning through sandbox test environments.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a quantitative trading AI specialising in autonomous
trading strategy development for the Chatlippytm AI DevOps platform.

Given a market context (asset class, symbol, market data summary, and optional
RL performance history), respond with a JSON object (no markdown fences) that has
exactly these keys:

{
  "action": "buy" | "sell" | "hold",
  "confidence": <float 0.0–1.0>,
  "strategy": "<name of strategy used>",
  "rationale": "<brief explanation>",
  "risk_level": "low" | "medium" | "high",
  "suggested_position_size": <float 0.0–1.0>,
  "stop_loss_pct": <float>,
  "take_profit_pct": <float>,
  "rl_recommendation": "<reinforcement-learning insight if provided, else null>"
}

Supported asset classes: crypto, stocks, forex.
"""


class TradingBotAgent(BaseAgent):
    """Manages and operates AI trading bots for crypto, stocks, and forex."""

    name = "TradingBotAgent"
    description = "AI trading bot manager – strategies, RL signals, and autonomous scaling"

    # Supported asset classes
    ASSET_CLASSES = {"crypto", "stocks", "forex"}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        symbol : str
            Ticker / trading pair (e.g. ``BTC/USDT``, ``AAPL``, ``EUR/USD``).
        asset_class : str
            One of ``crypto``, ``stocks``, ``forex``.
        market_data : str
            Textual summary of recent price action, indicators, or OHLCV data.
        rl_history : str, optional
            Recent reinforcement-learning performance log for adaptive signals.
        sandbox : bool, optional
            When ``True``, decision is logged only (no live execution).
        """
        symbol = context.get("symbol", "")
        asset_class = context.get("asset_class", "crypto").lower()
        market_data = context.get("market_data", "")
        rl_history = context.get("rl_history", "")
        sandbox = bool(context.get("sandbox", True))

        if not symbol:
            return self._base_result("error", message="No trading symbol provided")

        if asset_class not in self.ASSET_CLASSES:
            return self._base_result(
                "error",
                message=f"Unsupported asset class '{asset_class}'. "
                        f"Use one of: {', '.join(sorted(self.ASSET_CLASSES))}",
            )

        if not market_data:
            return self._base_result("error", message="No market data provided")

        logger.info(
            "[%s] Analysing %s (%s) | sandbox=%s …",
            self.name,
            symbol,
            asset_class,
            sandbox,
        )

        user_message = (
            f"Asset class : {asset_class}\n"
            f"Symbol      : {symbol}\n"
            f"Sandbox mode: {sandbox}\n\n"
            f"Market data:\n{market_data[:4000]}\n\n"
        )
        if rl_history:
            user_message += f"RL performance history:\n{rl_history[:2000]}\n"

        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            decision = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            symbol=symbol,
            asset_class=asset_class,
            sandbox=sandbox,
            decision=decision,
        )
