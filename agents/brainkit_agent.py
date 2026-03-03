"""
BrainKitAgent – distributes the Chatlippytm AI swarm capabilities to any
GitHub repository by installing a curated set of GitHub Actions workflows
and a BrainKit configuration file.

Each "BrainKit" is a portable bundle of AI-powered DevOps workflows (code
review, security scan, issue triage, health report, and auto-training) that
any repository can adopt with a single agent invocation.

Context keys
------------
repos : list[str]
    Target repositories in ``owner/repo`` format.
workflows : list[str], optional
    Subset of workflow names to install.  Defaults to all five core
    workflows.  Valid names:
    ``"ai-pr-review"``, ``"ai-security-scan"``, ``"ai-issue-triage"``,
    ``"ai-repo-health"``, ``"auto-train"``.
branch : str, optional
    Branch to commit the workflow files to (default ``"main"``).
commit_message : str, optional
    Custom commit message (a sensible default is used if omitted).
dry_run : bool, optional
    When ``True``, report what *would* be installed without making any
    GitHub API calls (default ``False``).
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any

from github import Github, GithubException

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compact, self-contained BrainKit workflow templates
# ---------------------------------------------------------------------------
# Each workflow installs the engine on-the-fly from the public repo and
# delegates work to the corresponding agent so target repos need no local
# copy of the engine.

_ENGINE_REPO = "lippytm/Chatlippytm.ai.Bots"

_INSTALL_STEP = f"""\
      - name: Install Chatlippytm AI Engine
        run: |
          pip install --quiet PyGithub openai tenacity python-dotenv rich PyYAML
          git clone --depth 1 https://github.com/{_ENGINE_REPO}.git /tmp/ai_engine
          pip install --quiet -r /tmp/ai_engine/requirements.txt
          echo "PYTHONPATH=/tmp/ai_engine" >> "$GITHUB_ENV"
"""

_WORKFLOWS: dict[str, str] = {
    "ai-pr-review": f"""\
name: AI BrainKit – Pull Request Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
    name: AI Code Review
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
{_INSTALL_STEP}
      - name: Fetch PR diff
        env:
          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: gh pr diff ${{{{ github.event.pull_request.number }}}} > /tmp/pr.diff
      - name: Run AI code review
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          python - <<'EOF'
          import sys, os
          from agents import CodeReviewAgent
          with open("/tmp/pr.diff") as f:
              diff = f.read()
          agent = CodeReviewAgent()
          result = agent.run({{
              "repo": "${{{{ github.repository }}}}",
              "pr_number": ${{{{ github.event.pull_request.number }}}},
              "diff": diff,
              "title": "${{{{ github.event.pull_request.title }}}}",
          }})
          with open("/tmp/review.md", "w") as f:
              f.write(result.get("review", ""))
          if result.get("status") != "ok":
              sys.exit(1)
          EOF
      - name: Post review comment
        env:
          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          BODY=$(cat /tmp/review.md)
          gh pr comment ${{{{ github.event.pull_request.number }}}} \\
            --body "## 🤖 AI Code Review (BrainKit)

          ${{BODY}}

          ---
          *Powered by [{_ENGINE_REPO}](https://github.com/{_ENGINE_REPO}) AI BrainKit*"
""",

    "ai-security-scan": f"""\
name: AI BrainKit – Security Scan

on:
  push:
    branches: [main, master]
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

jobs:
  security-scan:
    name: AI Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
{_INSTALL_STEP}
      - name: Run AI security scan
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          python - <<'EOF'
          from agents import SecurityAgent
          agent = SecurityAgent()
          result = agent.run({{"repo": "${{{{ github.repository }}}}", "max_files": 50}})
          report = result.get("report", "No security issues found.")
          with open("/tmp/security_report.md", "w") as f:
              f.write(report)
          print(report)
          EOF
      - name: Upload security report
        uses: actions/upload-artifact@v4
        with:
          name: security-report-${{{{ github.run_number }}}}
          path: /tmp/security_report.md
          retention-days: 30
      - name: Open issue on critical findings
        env:
          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          REPORT=$(cat /tmp/security_report.md)
          if echo "$REPORT" | grep -qi "CRITICAL\\|HIGH"; then
            gh issue create \\
              --title "🔒 AI Security Scan: Critical/High findings (run #${{{{ github.run_number }}}})" \\
              --body "${{REPORT}}" \\
              --label "security" || true
          fi
""",

    "ai-issue-triage": f"""\
name: AI BrainKit – Issue Triage

on:
  issues:
    types: [opened]

jobs:
  triage:
    name: AI Issue Triage
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
{_INSTALL_STEP}
      - name: Run AI triage
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          python - <<'EOF'
          import json
          from agents import IssueTriageAgent
          agent = IssueTriageAgent()
          result = agent.run({{
              "repo": "${{{{ github.repository }}}}",
              "issue_number": ${{{{ github.event.issue.number }}}},
              "title": "${{{{ github.event.issue.title }}}}",
              "body": '${{{{ github.event.issue.body }}}}',
          }})
          with open("/tmp/triage.json", "w") as f:
              json.dump(result.get("triage", {{}}), f)
          EOF
      - name: Apply labels
        env:
          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          LABELS=$(python -c "
          import json
          with open('/tmp/triage.json') as f:
              t = json.load(f)
          print(','.join(t.get('labels', [])))
          ")
          [ -n "$LABELS" ] && gh issue edit ${{{{ github.event.issue.number }}}} \\
            --add-label "$LABELS" || true
      - name: Post triage comment
        env:
          GH_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          COMMENT=$(python -c "
          import json
          with open('/tmp/triage.json') as f: t=json.load(f)
          print(t.get('triage_comment',''))
          ")
          gh issue comment ${{{{ github.event.issue.number }}}} \\
            --body "## 🤖 AI Triage (BrainKit)

          ${{COMMENT}}

          ---
          *Powered by [{_ENGINE_REPO}](https://github.com/{_ENGINE_REPO}) AI BrainKit*"
""",

    "ai-repo-health": f"""\
name: AI BrainKit – Repository Health

on:
  schedule:
    - cron: "0 8 * * 1"
  workflow_dispatch:

jobs:
  health-report:
    name: AI Repo Health Report
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
{_INSTALL_STEP}
      - name: Run health scan
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          python - <<'EOF'
          from agents import RepoScannerAgent
          agent = RepoScannerAgent()
          result = agent.run({{"repo": "${{{{ github.repository }}}}"}})
          report = result.get("report", "")
          with open("/tmp/health_report.md", "w") as f:
              f.write(report)
          print(report)
          EOF
      - name: Upload health report
        uses: actions/upload-artifact@v4
        with:
          name: health-report-${{{{ github.run_number }}}}
          path: /tmp/health_report.md
          retention-days: 30
""",

    "auto-train": f"""\
name: AI BrainKit – Auto Training

on:
  push:
    branches: [main, master]
  schedule:
    - cron: "0 3 * * 0"
  workflow_dispatch:

jobs:
  auto-train:
    name: Auto-Training Pipeline
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
{_INSTALL_STEP}
      - name: Run training pipeline
        env:
          OPENAI_API_KEY: ${{{{ secrets.OPENAI_API_KEY }}}}
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
        run: |
          cd /tmp/ai_engine
          python main.py train --repos "${{{{ github.repository }}}}"
""",
}

_ALL_WORKFLOWS = list(_WORKFLOWS.keys())

_BRAINKIT_CONFIG = """\
# Chatlippytm AI BrainKit configuration
# Installed by BrainKitAgent – edit to customise behaviour.

brainkit:
  engine: {engine_repo}
  version: "1.0"

agents:
  default_model: gpt-4o
  temperature: 0.2
  max_tokens: 4096

training:
  auto_train_on_push: true
  fine_tune_threshold: 100
"""


class BrainKitAgent(BaseAgent):
    """Deploys Chatlippytm AI BrainKit workflows to one or more GitHub repos."""

    name = "BrainKitAgent"
    description = (
        "Installs AI BrainKit (code-review, security-scan, issue-triage, "
        "health-report, auto-training workflows) into target GitHub repositories"
    )

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repos : list[str]
            Target repositories, e.g. ``["owner/repo1", "owner/repo2"]``.
        workflows : list[str], optional
            Workflow names to install.  Defaults to all five.
        branch : str, optional
            Branch to commit to (default ``"main"``).
        commit_message : str, optional
            Commit message override.
        dry_run : bool, optional
            Report planned changes without calling the GitHub API.
        """
        repos: list[str] = context.get("repos", [])
        if not repos:
            return self._base_result("error", message="repos list is required")

        requested = context.get("workflows", _ALL_WORKFLOWS)
        unknown = [w for w in requested if w not in _WORKFLOWS]
        if unknown:
            return self._base_result(
                "error",
                message=(
                    f"Unknown workflow(s): {unknown}. "
                    f"Valid names: {_ALL_WORKFLOWS}"
                ),
            )

        branch: str = context.get("branch", "main")
        dry_run: bool = bool(context.get("dry_run", False))
        commit_message: str = context.get(
            "commit_message",
            "chore: install Chatlippytm AI BrainKit workflows",
        )

        token = os.getenv("GITHUB_TOKEN")
        gh = Github(token) if token else Github()

        results: list[dict[str, Any]] = []

        for repo_name in repos:
            repo_result = self._install_brainkit(
                gh=gh,
                repo_name=repo_name,
                workflow_names=requested,
                branch=branch,
                commit_message=commit_message,
                dry_run=dry_run,
            )
            results.append(repo_result)
            status_label = repo_result.get("status", "?")
            logger.info(
                "[%s] %s → %s", self.name, repo_name, status_label
            )

        installed_count = sum(1 for r in results if r.get("status") == "ok")
        return self._base_result(
            repos_processed=len(repos),
            repos_installed=installed_count,
            dry_run=dry_run,
            results=results,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _install_brainkit(
        self,
        gh: Github,
        repo_name: str,
        workflow_names: list[str],
        branch: str,
        commit_message: str,
        dry_run: bool,
    ) -> dict[str, Any]:
        """Install BrainKit workflow files into a single repository."""
        files_to_write: dict[str, str] = {}

        for name in workflow_names:
            path = f".github/workflows/{name}.yml"
            files_to_write[path] = _WORKFLOWS[name]

        # Also install the brainkit config file
        files_to_write[".github/brainkit.yaml"] = _BRAINKIT_CONFIG.format(
            engine_repo=_ENGINE_REPO
        )

        if dry_run:
            return {
                "repo": repo_name,
                "status": "ok",
                "dry_run": True,
                "files": list(files_to_write.keys()),
            }

        try:
            repo = gh.get_repo(repo_name)
        except GithubException as exc:
            return {"repo": repo_name, "status": "error", "message": str(exc)}

        installed: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []

        for file_path, content in files_to_write.items():
            try:
                try:
                    existing = repo.get_contents(file_path, ref=branch)
                    # File exists – only update when content has changed
                    existing_sha = existing.sha  # type: ignore[union-attr]
                    existing_content = base64.b64decode(
                        existing.content  # type: ignore[union-attr]
                    ).decode()
                    if existing_content.strip() == content.strip():
                        skipped.append(file_path)
                        continue
                    repo.update_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        sha=existing_sha,
                        branch=branch,
                    )
                except GithubException:
                    # File does not exist yet – create it
                    repo.create_file(
                        path=file_path,
                        message=commit_message,
                        content=content,
                        branch=branch,
                    )
                installed.append(file_path)
            except GithubException as exc:
                errors.append(f"{file_path}: {exc}")

        status = "error" if errors and not installed else "ok"
        return {
            "repo": repo_name,
            "status": status,
            "installed": installed,
            "skipped": skipped,
            "errors": errors,
        }

    @staticmethod
    def available_workflows() -> list[str]:
        """Return the names of all installable BrainKit workflows."""
        return list(_WORKFLOWS.keys())
