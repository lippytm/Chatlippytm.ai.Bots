"""
ApiLearningAgent – API/API-driven learning ecosystem agent.

Enables bots to interact with one another to teach and learn API functionalities,
and simulates API lifecycle tasks for training implementations.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an API integration and training specialist for the
Chatlippytm AI DevOps platform.

Given an API specification or interaction log, generate a JSON object
(no markdown fences) with exactly these keys:

{
  "api_name": "<API name>",
  "endpoints_discovered": [
    {
      "method": "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
      "path": "<endpoint path>",
      "description": "<what it does>",
      "example_payload": "<JSON example or null>"
    }
  ],
  "lifecycle_simulations": [
    {
      "scenario": "<scenario name>",
      "steps": ["<step 1>", ...],
      "expected_outcome": "<what should happen>"
    }
  ],
  "training_examples": [
    {
      "prompt": "<user instruction>",
      "completion": "<correct API call or response>"
    }
  ],
  "bot_teaching_notes": "<key concepts this API teaches other bots>",
  "integration_recommendations": ["<recommendation>", ...]
}
"""


class ApiLearningAgent(BaseAgent):
    """Enables bots to learn and teach API functionalities through simulation."""

    name = "ApiLearningAgent"
    description = "API-driven learning ecosystem – bot-to-bot API teaching and lifecycle simulation"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        api_spec : str
            OpenAPI/Swagger spec, API documentation excerpt, or interaction log.
        api_name : str, optional
            Human-readable API name.
        target_bots : list[str], optional
            Names of bot agents that should consume these training examples.
        simulate_lifecycle : bool, optional
            When ``True`` (default), include lifecycle simulation scenarios.
        """
        api_spec = context.get("api_spec", "")
        if not api_spec:
            return self._base_result("error", message="No API specification provided")

        api_name = context.get("api_name", "unknown-api")
        target_bots = context.get("target_bots", [])
        simulate_lifecycle = bool(context.get("simulate_lifecycle", True))

        logger.info(
            "[%s] Processing API '%s' for %d target bots …",
            self.name,
            api_name,
            len(target_bots),
        )

        user_message = (
            f"API name: {api_name}\n"
            f"Simulate lifecycle: {simulate_lifecycle}\n"
            f"Target bots: {', '.join(target_bots) if target_bots else 'all'}\n\n"
            f"API specification:\n{api_spec[:6000]}\n"
        )

        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            learning_data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            learning_data = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            api_name=api_name,
            target_bots=target_bots,
            learning_data=learning_data,
        )
