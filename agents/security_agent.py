"""
SecurityAgent – scans repository code for common security vulnerabilities,
secrets accidentally committed, and insecure dependency patterns.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from github import Github, GithubException

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a cybersecurity expert performing a static security
analysis for the Chatlippytm AI DevOps platform. Analyse the provided repository
file listing and code snippets for:

1. Hard-coded secrets / credentials / API keys
2. Insecure dependency versions (known CVEs)
3. Injection vulnerabilities (SQLi, XSS, command injection)
4. Insecure configurations (open CORS, missing auth, debug mode in prod)
5. Sensitive data exposure risks

Return a structured Markdown report with:
- Severity (CRITICAL / HIGH / MEDIUM / LOW / INFO) per finding
- File + line reference where available
- Recommended remediation
"""


class SecurityAgent(BaseAgent):
    """Performs AI-powered security scanning on repository code."""

    name = "SecurityAgent"
    description = "Scans repositories for security vulnerabilities and secrets"

    # File extensions worth scanning
    _SCAN_EXTENSIONS = {
        ".py", ".js", ".ts", ".go", ".java", ".rb", ".php",
        ".yaml", ".yml", ".json", ".env", ".sh", ".tf",
    }

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        max_files : int, optional
            Maximum number of files to sample (default 30).
        """
        repo_name = context.get("repo", "")
        if not repo_name:
            return self._base_result("error", message="No repo name provided")

        max_files = int(context.get("max_files", 30))
        token = os.getenv("GITHUB_TOKEN")
        gh = Github(token) if token else Github()

        try:
            repo = gh.get_repo(repo_name)
        except GithubException as exc:
            return self._base_result("error", message=str(exc))

        snippets: list[str] = []
        file_count = 0

        try:
            contents = repo.get_contents("")
            queue = list(contents)
            while queue and file_count < max_files:
                item = queue.pop(0)
                if item.type == "dir":
                    try:
                        queue.extend(repo.get_contents(item.path))
                    except GithubException:
                        pass
                elif any(item.path.endswith(ext) for ext in self._SCAN_EXTENSIONS):
                    try:
                        code = item.decoded_content.decode("utf-8", errors="ignore")
                        snippets.append(
                            f"### {item.path}\n```\n{code[:2000]}\n```"
                        )
                        file_count += 1
                    except (GithubException, AttributeError):
                        pass
        except GithubException as exc:
            return self._base_result("error", message=str(exc))

        if not snippets:
            return self._base_result(
                "warning",
                repo=repo_name,
                message="No scannable files found",
            )

        logger.info("[%s] Scanning %d files in %s …", self.name, file_count, repo_name)

        user_message = (
            f"Repository: {repo_name}\n\n"
            + "\n\n".join(snippets)
        )

        report = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo_name,
            files_scanned=file_count,
            report=report,
        )
