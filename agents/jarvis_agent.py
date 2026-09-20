"""
JarvisAssistantAgent – general-purpose conversational assistant entrypoint.
"""

from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent

_SYSTEM_PROMPT = """You are Jarvis, the Chatlippytm AI assistant.

Help with brainstorming, planning, debugging, and lightweight repo-aware
assistant tasks. Be clear, practical, and concise.
"""


class JarvisAssistantAgent(BaseAgent):
    """Conversational assistant for direct user prompts."""

    name = "JarvisAssistantAgent"
    description = "Direct Jarvis assistant using the configured model provider"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        message = context.get("message") or context.get("question") or ""
        if not message:
            return self._base_result("error", message="message is required")

        prompt_parts = [_SYSTEM_PROMPT]
        conversation_context = context.get("context")
        if conversation_context:
            prompt_parts.append(f"Additional context:\n{conversation_context}")

        answer = self.chat("\n\n".join(prompt_parts), message)
        return self._base_result(
            response=answer,
            provider=self.provider,
            model=self.model,
        )
