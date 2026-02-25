"""
IssueTriageAgent – automatically labels, prioritises, and assigns
newly opened GitHub issues using AI classification.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert project manager triaging GitHub issues for
an AI DevOps platform. Given an issue title and body, respond with a JSON object
(no markdown fences) that has exactly these keys:

{
  "priority": "critical" | "high" | "medium" | "low",
  "labels": ["<label1>", ...],
  "summary": "<one-sentence summary>",
  "suggested_assignee_role": "<role>",
  "needs_more_info": true | false,
  "triage_comment": "<friendly Markdown comment to post on the issue>"
}

Possible labels: bug, enhancement, documentation, question, security,
performance, ci-cd, dependencies, good-first-issue, duplicate.
"""


class IssueTriageAgent(BaseAgent):
    """Classifies and prioritises GitHub issues with AI triage."""

    name = "IssueTriageAgent"
    description = "Auto-triages GitHub issues with AI classification"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name.
        issue_number : int
            Issue number.
        title : str
            Issue title.
        body : str
            Issue body text.
        """
        repo = context.get("repo", "unknown/repo")
        issue_number = context.get("issue_number", 0)
        title = context.get("title", "")
        body = context.get("body", "")

        if not title:
            return self._base_result("error", message="No issue title provided")

        logger.info("[%s] Triaging issue #%s in %s …", self.name, issue_number, repo)

        user_message = (
            f"Repository: {repo}\n"
            f"Issue #{issue_number}\n"
            f"Title: {title}\n\n"
            f"Body:\n{body[:3000]}"
        )

        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            triage = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON if the model wrapped it in fences
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            triage = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            repo=repo,
            issue_number=issue_number,
            triage=triage,
        )
