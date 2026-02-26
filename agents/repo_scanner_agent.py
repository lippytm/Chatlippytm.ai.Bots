"""
RepoScannerAgent – scans a GitHub repository and produces an AI-generated
health report covering code quality, documentation gaps, open issues, and
DevOps hygiene.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from github import Github, GithubException

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a senior DevOps architect analysing a GitHub repository
for the Chatlippytm AI platform. Given a summary of a repository's metadata,
files, open issues, and recent commits, produce a comprehensive health report.

Include:
1. Overall health score (0–100)
2. Code-quality observations
3. Documentation coverage
4. CI/CD pipeline assessment
5. Open issues triage summary
6. Recommended next actions (prioritised)

Use Markdown formatting.
"""


class RepoScannerAgent(BaseAgent):
    """Scans a GitHub repository and generates an AI health report."""

    name = "RepoScannerAgent"
    description = "Scans repositories and produces AI-generated health reports"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        """
        repo_name = context.get("repo", "")
        if not repo_name:
            return self._base_result("error", message="No repo name provided")

        token = os.getenv("GITHUB_TOKEN")
        gh = Github(token) if token else Github()

        try:
            repo = gh.get_repo(repo_name)
        except GithubException as exc:
            return self._base_result("error", message=str(exc))

        # Collect metadata
        open_issues = repo.get_issues(state="open")
        issue_titles = [i.title for i in list(open_issues)[:20]]

        try:
            contents = [f.path for f in repo.get_contents("") if f.type == "file"]
        except GithubException:
            contents = []

        recent_commits = []
        try:
            for commit in repo.get_commits()[:10]:
                recent_commits.append(commit.commit.message.splitlines()[0])
        except GithubException:
            pass

        summary = (
            f"Repository: {repo_name}\n"
            f"Description: {repo.description or 'N/A'}\n"
            f"Stars: {repo.stargazers_count}  Forks: {repo.forks_count}\n"
            f"Default branch: {repo.default_branch}\n"
            f"Open issues ({len(issue_titles)}): {issue_titles}\n"
            f"Root files: {contents[:30]}\n"
            f"Recent commit messages: {recent_commits}\n"
        )

        logger.info("[%s] Scanning %s …", self.name, repo_name)
        report = self.chat(_SYSTEM_PROMPT, summary)

        return self._base_result(
            repo=repo_name,
            report=report,
            open_issue_count=repo.open_issues_count,
        )
