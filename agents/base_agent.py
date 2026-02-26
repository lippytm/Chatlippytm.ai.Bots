"""
BaseAgent – abstract foundation for all AI DevOps synthetic intelligence agents.

Every specialist agent (code review, security, trainer, …) inherits from this
class to get shared plumbing: OpenAI client setup, logging, retry logic, and
a uniform ``run()`` interface.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all Chatlippytm AI agents."""

    #: Override in subclasses to give each agent a human-readable identity.
    name: str = "BaseAgent"
    #: One-line description surfaced in swarm status reports.
    description: str = "Generic AI agent"

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        verbose: bool = False,
    ) -> None:
        self.model = model or os.getenv("AGENT_MODEL", "gpt-4o")
        self.temperature = temperature if temperature is not None else float(
            os.getenv("TRAINING_TEMPERATURE", "0.2")
        )
        self.max_tokens = max_tokens or int(os.getenv("TRAINING_MAX_TOKENS", "4096"))
        self.verbose = verbose or os.getenv("AGENT_VERBOSE", "false").lower() == "true"

        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._conversation: list[dict[str, str]] = []

        logging.basicConfig(
            level=logging.DEBUG if self.verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's primary task.

        Parameters
        ----------
        context:
            Arbitrary key-value payload describing the current task (e.g.
            repo name, PR number, file list …).

        Returns
        -------
        dict
            Result payload – always includes at least ``{"status": "ok"|"error",
            "agent": self.name}``.
        """

    def chat(self, system_prompt: str, user_message: str) -> str:
        """Send a single-turn chat request to the configured OpenAI model."""
        return self._chat_with_retry(system_prompt, user_message)

    def reset_conversation(self) -> None:
        """Clear the in-memory conversation history."""
        self._conversation = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _chat_with_retry(self, system_prompt: str, user_message: str) -> str:
        """Call the OpenAI Chat Completions API with automatic retry on transient errors."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        logger.debug("[%s] Sending chat request …", self.name)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        content = response.choices[0].message.content or ""
        logger.debug("[%s] Received response (%d chars)", self.name, len(content))
        return content

    def _base_result(self, status: str = "ok", **extra: Any) -> dict[str, Any]:
        """Build a standard result envelope."""
        return {"status": status, "agent": self.name, **extra}
