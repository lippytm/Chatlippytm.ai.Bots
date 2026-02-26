"""
DocAgent – autonomously generates and maintains project documentation from
GitHub repositories, and writes transparency logs.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from github import Github, GithubException

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a technical documentation expert for the Chatlippytm
AI DevOps platform. Given a repository summary (files, README, recent commits,
open issues), generate comprehensive, well-structured Markdown documentation.

Your output must include:

1. **Project Overview** – purpose, architecture, and key components
2. **Installation & Setup** – step-by-step instructions
3. **Usage Guide** – CLI commands, API endpoints, and configuration options
4. **Module Reference** – description of each significant module/file
5. **Contributing Guidelines** – how to add features, run tests, submit PRs
6. **Transparency Log** – summary of recent changes and open issues

Use clear Markdown headings, bullet points, and code blocks where appropriate.
"""


class DocAgent(BaseAgent):
    """Autonomously generates project documentation from repository contents."""

    name = "DocAgent"
    description = "Autonomous documentation generator – creates and maintains project docs"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        max_files : int, optional
            Maximum number of source files to sample (default 20).
        include_transparency_log : bool, optional
            When ``True`` (default), append a transparency log section.
        """
        repo_name = context.get("repo", "")
        if not repo_name:
            return self._base_result("error", message="No repo name provided")

        max_files = int(context.get("max_files", 20))
        include_log = bool(context.get("include_transparency_log", True))

        token = os.getenv("GITHUB_TOKEN")
        gh = Github(token) if token else Github()

        try:
            repo = gh.get_repo(repo_name)
        except GithubException as exc:
            return self._base_result("error", message=str(exc))

        # Collect README
        readme_content = ""
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode("utf-8", errors="ignore")[:3000]
        except GithubException:
            pass

        # Collect file listing
        file_paths: list[str] = []
        try:
            for item in repo.get_contents(""):
                if item.type == "file":
                    file_paths.append(item.path)
        except GithubException:
            pass

        # Collect recent commits for transparency log
        recent_commits: list[str] = []
        if include_log:
            try:
                for commit in repo.get_commits()[:15]:
                    recent_commits.append(commit.commit.message.splitlines()[0])
            except GithubException:
                pass

        # Collect open issues for transparency log
        open_issues: list[str] = []
        if include_log:
            try:
                for issue in list(repo.get_issues(state="open"))[:10]:
                    open_issues.append(f"#{issue.number}: {issue.title}")
            except GithubException:
                pass

        logger.info("[%s] Generating documentation for %s …", self.name, repo_name)

        user_message = (
            f"Repository: {repo_name}\n"
            f"Description: {repo.description or 'N/A'}\n\n"
            f"README (excerpt):\n{readme_content}\n\n"
            f"Root files ({len(file_paths[:max_files])}): {file_paths[:max_files]}\n\n"
        )
        if include_log:
            user_message += (
                f"Recent commits:\n"
                + "\n".join(f"  - {c}" for c in recent_commits)
                + f"\n\nOpen issues:\n"
                + "\n".join(f"  - {i}" for i in open_issues)
            )

        documentation = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo_name,
            documentation=documentation,
            files_sampled=len(file_paths[:max_files]),
            commits_logged=len(recent_commits),
            open_issues_logged=len(open_issues),
        )
