"""
CodeReviewAgent – AI-powered pull request code reviewer.

Analyses changed files in a GitHub PR and posts structured review comments
with suggestions, bug flags, and best-practice notes.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert software engineer and code reviewer for the
Chatlippytm AI DevOps platform. Your job is to review code changes in pull requests
and provide actionable, constructive feedback.

For each file diff provided, identify:
1. Bugs or logical errors
2. Security vulnerabilities
3. Performance issues
4. Code style / readability concerns
5. Missing tests or documentation

Format your response as structured Markdown with a summary section followed by
per-file observations. Be specific: include line references where possible.
"""


class CodeReviewAgent(BaseAgent):
    """Reviews pull request diffs using GPT and returns structured feedback."""

    name = "CodeReviewAgent"
    description = "AI-powered pull request code reviewer"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        pr_number : int
            The pull-request number.
        diff : str
            Raw unified diff text of the PR.
        title : str, optional
            PR title for additional context.
        description : str, optional
            PR body for additional context.
        """
        repo = context.get("repo", "unknown/repo")
        pr_number = context.get("pr_number", 0)
        diff = context.get("diff", "")
        title = context.get("title", "")
        pr_description = context.get("description", "")

        if not diff:
            return self._base_result("error", message="No diff provided")

        logger.info("[%s] Reviewing PR #%s in %s …", self.name, pr_number, repo)

        user_message = (
            f"Repository: {repo}\n"
            f"PR #{pr_number}: {title}\n"
            f"Description: {pr_description}\n\n"
            f"Diff:\n```diff\n{diff[:12000]}\n```\n\n"
            "Please review this pull request."
        )

        review = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo,
            pr_number=pr_number,
            review=review,
        )
