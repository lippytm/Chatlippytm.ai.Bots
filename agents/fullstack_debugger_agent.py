"""
FullStackDebuggerAgent – AI-powered full-stack debugging development toolkit.

Analyses errors, logs, and stack traces spanning frontend, backend, APIs,
and infrastructure layers to identify cross-tier root causes and provide
actionable remediation guidance.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a senior full-stack engineer and debugger for the
Chatlippytm AI DevOps platform. You specialise in diagnosing issues that span
multiple tiers of a software stack (frontend, backend, API gateway, database,
infrastructure, CI/CD pipelines).

For each debugging request, you must:
1. Identify which tier(s) of the stack are involved
2. Determine the root cause and propagation path across tiers
3. Provide a prioritised list of remediation steps with code or config examples
4. Highlight any related issues across other layers that could resurface
5. Suggest integration tests or observability improvements to catch the issue
   earlier in future

Format your response as structured Markdown with per-tier sections where
relevant.
"""


class FullStackDebuggerAgent(BaseAgent):
    """AI-powered full-stack debugging and development toolkit."""

    name = "FullStackDebuggerAgent"
    description = "AI Full Stack Debugging Development toolkit – cross-tier root-cause analysis"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        error_log : str
            Raw error log or exception message from any tier.
        frontend_snippet : str, optional
            Relevant frontend code or browser console output.
        backend_snippet : str, optional
            Relevant backend code or server-side log excerpt.
        api_spec : str, optional
            API contract snippet (OpenAPI, GraphQL schema, etc.).
        infrastructure_info : str, optional
            Infrastructure config excerpt (Docker, k8s, Terraform, etc.).
        description : str, optional
            Free-text description of the unexpected behaviour.
        """
        repo = context.get("repo", "unknown/repo")
        error_log = context.get("error_log", "")
        frontend_snippet = context.get("frontend_snippet", "")
        backend_snippet = context.get("backend_snippet", "")
        api_spec = context.get("api_spec", "")
        infrastructure_info = context.get("infrastructure_info", "")
        description = context.get("description", "")

        if not any([error_log, frontend_snippet, backend_snippet, description]):
            return self._base_result(
                "error",
                message="No debugging context provided (error_log, frontend_snippet, backend_snippet, or description required)",
            )

        logger.info("[%s] Debugging full-stack issue in %s …", self.name, repo)

        parts: list[str] = [f"Repository: {repo}"]
        if description:
            parts.append(f"Description:\n{description[:1000]}")
        if error_log:
            parts.append(f"Error log:\n```\n{error_log[:4000]}\n```")
        if frontend_snippet:
            parts.append(f"Frontend code:\n```\n{frontend_snippet[:2000]}\n```")
        if backend_snippet:
            parts.append(f"Backend code:\n```\n{backend_snippet[:2000]}\n```")
        if api_spec:
            parts.append(f"API spec:\n```\n{api_spec[:1000]}\n```")
        if infrastructure_info:
            parts.append(f"Infrastructure config:\n```\n{infrastructure_info[:1000]}\n```")

        user_message = "\n\n".join(parts)

        analysis = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo,
            analysis=analysis,
        )
