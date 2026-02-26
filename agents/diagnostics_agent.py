"""
DiagnosticsAgent – AI Full Stack Diagnostics toolkit.

Performs end-to-end health diagnostics across a full-stack application:
services, databases, APIs, CI pipelines, and infrastructure. Produces a
structured diagnostic report with severity-graded findings and actionable
remediation steps.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a site-reliability engineer and diagnostics expert
for the Chatlippytm AI DevOps platform. Your role is to perform comprehensive
health diagnostics across all layers of a full-stack application.

Given any combination of metrics, logs, deployment manifests, test results,
and repository metadata, produce a structured diagnostic report that covers:

1. Overall system health score (0–100) with a brief justification
2. Per-layer findings (frontend, backend, database, API, infrastructure, CI/CD)
   - Severity: CRITICAL / HIGH / MEDIUM / LOW / INFO
   - Affected component and symptom description
   - Probable cause
   - Recommended remediation with concrete steps or config examples
3. Dependency and integration health (third-party services, external APIs)
4. Performance bottlenecks identified from the provided data
5. Prioritised action list (top 5 items to address immediately)

Format your response as structured Markdown.
"""


class DiagnosticsAgent(BaseAgent):
    """Runs AI-powered full-stack diagnostics and produces health reports."""

    name = "DiagnosticsAgent"
    description = "AI Full Stack Diagnostics toolkit – end-to-end health analysis"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        metrics : str, optional
            Metrics snapshot (JSON, Prometheus text, CloudWatch, etc.).
        logs : str, optional
            Recent application or infrastructure log excerpt.
        test_results : str, optional
            CI test results summary or raw test output.
        deployment_info : str, optional
            Deployment manifest or infrastructure-as-code excerpt.
        description : str, optional
            Free-text description of the system or issue under analysis.
        """
        repo = context.get("repo", "unknown/repo")
        metrics = context.get("metrics", "")
        logs = context.get("logs", "")
        test_results = context.get("test_results", "")
        deployment_info = context.get("deployment_info", "")
        description = context.get("description", "")

        if not any([metrics, logs, test_results, deployment_info, description]):
            return self._base_result(
                "error",
                message="No diagnostic data provided (metrics, logs, test_results, deployment_info, or description required)",
            )

        logger.info("[%s] Running full-stack diagnostics for %s …", self.name, repo)

        parts: list[str] = [f"Repository: {repo}"]
        if description:
            parts.append(f"Description:\n{description[:1000]}")
        if metrics:
            parts.append(f"Metrics:\n```\n{metrics[:3000]}\n```")
        if logs:
            parts.append(f"Logs:\n```\n{logs[:4000]}\n```")
        if test_results:
            parts.append(f"Test results:\n```\n{test_results[:2000]}\n```")
        if deployment_info:
            parts.append(f"Deployment info:\n```\n{deployment_info[:2000]}\n```")

        user_message = "\n\n".join(parts)

        report = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo,
            report=report,
        )
