#!/usr/bin/env python3
"""
Chatlippytm.ai.Bots – Main CLI Entry Point

Full Stack AI DevOps Synthetic Intelligence Engine
Powered by OpenAI GPT-4o + GitHub API

Usage
-----
::

    # Run the full swarm against one or more repositories
    python main.py swarm --repos lippytm/Chatlippytm.ai.Bots

    # Run only the auto-training pipeline
    python main.py train --repos lippytm/Chatlippytm.ai.Bots

    # Scan a single repo for security issues
    python main.py scan --repo lippytm/Chatlippytm.ai.Bots

    # Triage an issue
    python main.py triage --repo lippytm/Chatlippytm.ai.Bots --issue 42
"""

from __future__ import annotations

import json
import logging
import sys

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

console = Console()

# ---------------------------------------------------------------------------
# CLI root
# ---------------------------------------------------------------------------


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
def cli(verbose: bool) -> None:
    """Chatlippytm.ai.Bots – AI DevOps Synthetic Intelligence Engine."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )


# ---------------------------------------------------------------------------
# swarm command
# ---------------------------------------------------------------------------


@cli.command("swarm")
@click.option(
    "--repos",
    required=True,
    help="Comma-separated list of owner/repo targets.",
)
@click.option(
    "--agents",
    default="CodeReviewAgent,SecurityAgent,RepoScannerAgent,IssueTriageAgent",
    show_default=True,
    help="Comma-separated agent names to include in the swarm.",
)
@click.option("--workers", default=4, show_default=True, help="Swarm concurrency.")
@click.option("--output", default=None, help="Write JSON results to this file.")
def swarm_cmd(repos: str, agents: str, workers: int, output: str | None) -> None:
    """Launch the AI agent swarm across target repositories."""
    from agents import (
        CodeReviewAgent,
        DiagnosticsAgent,
        FullStackDebuggerAgent,
        IssueTriageAgent,
        PythonDebuggerAgent,
        RepoScannerAgent,
        SecurityAgent,
        TrainerAgent,
        TransparencyAgent,
    )
    from swarm import Swarm

    agent_map = {
        "CodeReviewAgent": CodeReviewAgent,
        "SecurityAgent": SecurityAgent,
        "RepoScannerAgent": RepoScannerAgent,
        "IssueTriageAgent": IssueTriageAgent,
        "TrainerAgent": TrainerAgent,
        "PythonDebuggerAgent": PythonDebuggerAgent,
        "FullStackDebuggerAgent": FullStackDebuggerAgent,
        "DiagnosticsAgent": DiagnosticsAgent,
        "TransparencyAgent": TransparencyAgent,
    }

    selected = [a.strip() for a in agents.split(",") if a.strip()]
    repo_list = [r.strip() for r in repos.split(",") if r.strip()]

    console.print(
        Panel.fit(
            f"[bold cyan]Chatlippytm.ai.Bots Swarm[/bold cyan]\n"
            f"Agents : {', '.join(selected)}\n"
            f"Repos  : {', '.join(repo_list)}\n"
            f"Workers: {workers}",
            title="🤖 AI DevOps Engine",
        )
    )

    s = Swarm(max_workers=workers)
    for name in selected:
        cls = agent_map.get(name)
        if cls is None:
            console.print(f"[yellow]Unknown agent '{name}' – skipping.[/yellow]")
            continue
        s.register(cls())

    results = s.run_all(repos=repo_list)

    _print_results_table(results)

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2)
        console.print(f"[green]Results written to {output}[/green]")


# ---------------------------------------------------------------------------
# train command
# ---------------------------------------------------------------------------


@cli.command("train")
@click.option(
    "--repos",
    required=True,
    help="Comma-separated list of owner/repo targets.",
)
@click.option(
    "--submit",
    is_flag=True,
    default=False,
    help="Submit a fine-tuning job to OpenAI when enough data is collected.",
)
@click.option(
    "--threshold",
    default=100,
    show_default=True,
    help="Minimum training examples before submitting a fine-tune job.",
)
def train_cmd(repos: str, submit: bool, threshold: int) -> None:
    """Run the auto-training pipeline across target repositories."""
    from training import TrainingPipeline

    repo_list = [r.strip() for r in repos.split(",") if r.strip()]

    console.print(
        Panel.fit(
            f"[bold magenta]Auto-Training Pipeline[/bold magenta]\n"
            f"Repos     : {', '.join(repo_list)}\n"
            f"Submit FT : {submit}\n"
            f"Threshold : {threshold} examples",
            title="🧠 Training Engine",
        )
    )

    pipeline = TrainingPipeline(
        repos=repo_list,
        fine_tune_threshold=threshold,
        submit_fine_tune=submit,
    )
    summary = pipeline.run()

    console.print(
        f"\n[bold green]✓ Training complete[/bold green]\n"
        f"  Repos processed : {summary['repos_processed']}\n"
        f"  Total examples  : {summary['total_examples']}\n"
        f"  Merged file     : {summary['merged_file'] or 'N/A'}\n"
    )

    if summary.get("fine_tune_job"):
        ft = summary["fine_tune_job"]
        console.print(
            f"  Fine-tune job   : {ft.get('job_id', 'N/A')} "
            f"(status={ft.get('status', 'N/A')})"
        )


# ---------------------------------------------------------------------------
# scan command
# ---------------------------------------------------------------------------


@cli.command("scan")
@click.option("--repo", required=True, help="owner/repo to scan.")
@click.option("--max-files", default=30, show_default=True)
def scan_cmd(repo: str, max_files: int) -> None:
    """Run the SecurityAgent against a repository."""
    from agents import SecurityAgent

    console.print(f"[bold red]🔒 Security scan:[/bold red] {repo}")
    agent = SecurityAgent()
    result = agent.run({"repo": repo, "max_files": max_files})

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    console.print(result.get("report", "No report generated."))


# ---------------------------------------------------------------------------
# triage command
# ---------------------------------------------------------------------------


@cli.command("triage")
@click.option("--repo", required=True, help="owner/repo.")
@click.option("--issue", required=True, type=int, help="Issue number.")
def triage_cmd(repo: str, issue: int) -> None:
    """Triage a GitHub issue with AI classification."""
    import os

    from agents import IssueTriageAgent
    from github import Github

    token = os.getenv("GITHUB_TOKEN")
    gh = Github(token) if token else Github()

    try:
        gh_repo = gh.get_repo(repo)
        gh_issue = gh_repo.get_issue(issue)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to fetch issue: {exc}[/red]")
        sys.exit(1)

    agent = IssueTriageAgent()
    result = agent.run(
        {
            "repo": repo,
            "issue_number": issue,
            "title": gh_issue.title,
            "body": gh_issue.body or "",
        }
    )

    triage = result.get("triage", {})
    console.print(
        Panel(
            f"Priority : [bold]{triage.get('priority', 'N/A')}[/bold]\n"
            f"Labels   : {triage.get('labels', [])}\n"
            f"Summary  : {triage.get('summary', 'N/A')}\n\n"
            f"{triage.get('triage_comment', '')}",
            title=f"🏷️  Issue #{issue} Triage",
        )
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_results_table(results: list[dict]) -> None:
    table = Table(title="Swarm Results", show_lines=True)
    table.add_column("Task ID", style="dim")
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Repo / Detail")

    for r in results:
        status = r.get("status", "?")
        color = {"ok": "green", "error": "red", "warning": "yellow"}.get(status, "white")
        detail = r.get("result", {}).get("repo", r.get("error", ""))
        table.add_row(
            r.get("task_id", ""),
            r.get("agent", ""),
            f"[{color}]{status}[/{color}]",
            detail,
        )

    console.print(table)


if __name__ == "__main__":
    cli()
