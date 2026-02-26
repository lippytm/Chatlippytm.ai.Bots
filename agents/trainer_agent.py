"""
TrainerAgent – auto-training agent that collects repository artefacts
(code, issues, PRs, docs) and synthesises training examples for future
fine-tuning of the AI models powering the swarm.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from github import Github, GithubException

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a machine-learning data engineer specialising in
constructing high-quality fine-tuning datasets for OpenAI chat models.

Given a set of repository artefacts (code snippets, issue conversations,
pull-request discussions), generate JSONL training examples in OpenAI
fine-tuning format:

{"messages": [{"role": "system", "content": "..."}, {"role": "user",
"content": "..."}, {"role": "assistant", "content": "..."}]}

Focus on DevOps automation tasks: code review, issue triage, CI/CD advice,
and security scanning. Return only valid JSONL – one JSON object per line.
"""


class TrainerAgent(BaseAgent):
    """Collects repo artefacts and generates fine-tuning training data."""

    name = "TrainerAgent"
    description = "Auto-training agent – builds fine-tune datasets from repo artefacts"

    # Default output directory (relative to project root)
    DEFAULT_DATA_DIR = Path("training/data")

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        output_dir : str, optional
            Directory to write JSONL training data.  Defaults to
            ``training/data``.
        max_issues : int, optional
            Maximum number of issues to include (default 50).
        """
        repo_name = context.get("repo", "")
        if not repo_name:
            return self._base_result("error", message="No repo name provided")

        output_dir = Path(context.get("output_dir", self.DEFAULT_DATA_DIR))
        output_dir.mkdir(parents=True, exist_ok=True)
        max_issues = int(context.get("max_issues", 50))

        token = os.getenv("GITHUB_TOKEN")
        gh = Github(token) if token else Github()

        try:
            repo = gh.get_repo(repo_name)
        except GithubException as exc:
            return self._base_result("error", message=str(exc))

        artefacts: list[str] = []

        # Collect closed issues with comments as conversation examples
        try:
            for issue in list(repo.get_issues(state="closed"))[:max_issues]:
                body = issue.body or ""
                comments = [c.body for c in issue.get_comments()[:5]]
                artefacts.append(
                    f"ISSUE #{issue.number}: {issue.title}\n"
                    f"Body: {body[:500]}\n"
                    f"Comments: {comments}"
                )
        except GithubException as exc:
            logger.warning("[%s] Could not fetch issues: %s", self.name, exc)

        if not artefacts:
            return self._base_result(
                "warning",
                repo=repo_name,
                message="No artefacts collected – skipping training data generation",
            )

        logger.info(
            "[%s] Generating training examples from %d artefacts …",
            self.name,
            len(artefacts),
        )

        user_message = (
            f"Repository: {repo_name}\n\n"
            "Artefacts:\n"
            + "\n---\n".join(artefacts[:20])  # cap to avoid token limits
        )

        jsonl_output = self.chat(_SYSTEM_PROMPT, user_message)

        # Write output
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_repo = repo_name.replace("/", "_")
        out_file = output_dir / f"{safe_repo}_{timestamp}.jsonl"
        out_file.write_text(jsonl_output, encoding="utf-8")

        # Count valid lines
        valid_lines = sum(
            1
            for line in jsonl_output.splitlines()
            if line.strip() and _is_valid_json(line.strip())
        )

        logger.info("[%s] Wrote %d examples to %s", self.name, valid_lines, out_file)

        return self._base_result(
            repo=repo_name,
            output_file=str(out_file),
            examples_written=valid_lines,
            artefacts_processed=len(artefacts),
        )


def _is_valid_json(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        return False
