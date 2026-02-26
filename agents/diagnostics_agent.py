"""
DiagnosticsAgent – automated diagnostics engine.

Tests and resolves code issues, optimises workflows, and conducts model
evaluations for the Chatlippytm AI DevOps platform.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert AI diagnostics engineer for the Chatlippytm
AI DevOps platform.

Given a diagnostic context (code snippets, error logs, test results, or workflow
definitions), produce a JSON object (no markdown fences) with exactly these keys:

{
  "severity": "critical" | "high" | "medium" | "low" | "info",
  "issues_found": [
    {
      "type": "<issue type>",
      "location": "<file:line or component>",
      "description": "<what is wrong>",
      "fix": "<recommended fix>"
    }
  ],
  "workflow_optimisations": ["<optimisation suggestion>", ...],
  "model_evaluation": {
    "accuracy_estimate": <float 0.0–1.0 or null>,
    "notes": "<evaluation notes>"
  },
  "auto_resolved": ["<issue description that was auto-resolved>", ...],
  "summary": "<one-paragraph diagnostic summary>"
}
"""


class DiagnosticsAgent(BaseAgent):
    """Runs automated diagnostics, resolves issues, and optimises workflows."""

    name = "DiagnosticsAgent"
    description = "Automated diagnostics – issue resolution, workflow optimisation, model evaluation"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        target : str
            A label for what is being diagnosed (repo name, component, etc.).
        code_snippets : str, optional
            Relevant code excerpts to analyse.
        error_logs : str, optional
            Recent error or exception logs.
        test_results : str, optional
            Test suite output to evaluate.
        workflow : str, optional
            CI/CD or workflow definition (YAML/JSON) to optimise.
        """
        target = context.get("target", context.get("repo", "unknown"))
        code_snippets = context.get("code_snippets", "")
        error_logs = context.get("error_logs", "")
        test_results = context.get("test_results", "")
        workflow = context.get("workflow", "")

        if not any([code_snippets, error_logs, test_results, workflow]):
            return self._base_result(
                "error",
                message="No diagnostic input provided (need at least one of: "
                        "code_snippets, error_logs, test_results, workflow)",
            )

        logger.info("[%s] Running diagnostics for '%s' …", self.name, target)

        parts: list[str] = [f"Target: {target}\n"]
        if code_snippets:
            parts.append(f"Code snippets:\n{code_snippets[:3000]}")
        if error_logs:
            parts.append(f"Error logs:\n{error_logs[:2000]}")
        if test_results:
            parts.append(f"Test results:\n{test_results[:2000]}")
        if workflow:
            parts.append(f"Workflow definition:\n{workflow[:2000]}")

        user_message = "\n\n".join(parts)
        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            report = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            target=target,
            diagnostics=report,
        )
