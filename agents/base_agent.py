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
from functools import lru_cache
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _build_anthropic_session(api_key: str, version: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "x-api-key": api_key,
            "anthropic-version": version,
            "content-type": "application/json",
        }
    )
    return session


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
        provider: str | None = None,
        verbose: bool = False,
    ) -> None:
        self.model = model or os.getenv("AGENT_MODEL", "gpt-4o")
        self.temperature = temperature if temperature is not None else float(
            os.getenv("TRAINING_TEMPERATURE", "0.2")
        )
        self.max_tokens = max_tokens or int(os.getenv("TRAINING_MAX_TOKENS", "4096"))
        self.provider = self._resolve_provider(provider, self.model)
        self._anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.verbose = verbose or os.getenv("AGENT_VERBOSE", "false").lower() == "true"

        self._validate_provider_model()
        self._client = self._build_client()
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
        """Call the configured model provider with automatic retry on transient errors."""
        if self.provider == "anthropic":
            return self._chat_with_anthropic(system_prompt, user_message)
        return self._chat_with_openai(system_prompt, user_message)

    def _resolve_provider(self, provider: str | None, model: str) -> str:
        if provider:
            return provider.strip().lower()

        env_provider = os.getenv("AGENT_PROVIDER")
        if env_provider:
            return env_provider.strip().lower()

        if model.lower().startswith("claude"):
            return "anthropic"
        return "openai"

    def _build_client(self) -> Any:
        if self.provider == "openai":
            return OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                organization=os.getenv("OPENAI_ORG_ID"),
                base_url=os.getenv("OPENAI_BASE_URL"),
            )
        if self.provider == "anthropic":
            return _build_anthropic_session(
                self._anthropic_api_key,
                os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
            )
        raise ValueError(f"Unsupported provider '{self.provider}'")

    def _validate_provider_model(self) -> None:
        model_name = self.model.lower()
        if self.provider == "anthropic" and not model_name.startswith("claude"):
            raise ValueError(
                f"Anthropic provider requires a Claude model, got '{self.model}'"
            )
        if self.provider == "openai" and model_name.startswith("claude"):
            raise ValueError(
                f"OpenAI provider does not support Claude model '{self.model}'"
            )

    def _chat_with_openai(self, system_prompt: str, user_message: str) -> str:
        """Call the OpenAI Chat Completions API."""
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

    def _chat_with_anthropic(self, system_prompt: str, user_message: str) -> str:
        """Call the Anthropic Messages API for Claude models."""
        api_root = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        endpoint = f"{api_root}/v1/messages"

        if not self._anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic provider")

        logger.debug("[%s] Sending Anthropic request …", self.name)
        response = self._client.post(
            endpoint,
            json={
                "model": self.model,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        content_blocks = payload.get("content", [])
        content_parts: list[str] = []

        if isinstance(content_blocks, str):
            content_parts.append(content_blocks)
        elif isinstance(content_blocks, list):
            for block in content_blocks:
                if isinstance(block, str):
                    content_parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text") or block.get("content")
                    if isinstance(text, str):
                        content_parts.append(text)

        content = "".join(content_parts)
        if not content:
            raise ValueError("Anthropic response did not contain any text content")
        logger.debug("[%s] Received Anthropic response (%d chars)", self.name, len(content))
        return content

    def _base_result(self, status: str = "ok", **extra: Any) -> dict[str, Any]:
        """Build a standard result envelope."""
        return {"status": status, "agent": self.name, **extra}
