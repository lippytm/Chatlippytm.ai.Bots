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
    help="Comma-separated agent names to include in the swarm. "
         "Available: CodeReviewAgent, SecurityAgent, RepoScannerAgent, "
         "IssueTriageAgent, TrainerAgent, TradingBotAgent, DiagnosticsAgent, "
         "SandboxAgent, DocAgent, DatabaseAgent, ApiLearningAgent.",
)
@click.option("--workers", default=4, show_default=True, help="Swarm concurrency.")
@click.option("--output", default=None, help="Write JSON results to this file.")
def swarm_cmd(repos: str, agents: str, workers: int, output: str | None) -> None:
    """Launch the AI agent swarm across target repositories."""
    from agents import (
        ApiLearningAgent,
        CodeReviewAgent,
        DatabaseAgent,
        DiagnosticsAgent,
        DocAgent,
        IssueTriageAgent,
        RepoScannerAgent,
        SandboxAgent,
        SecurityAgent,
        TradingBotAgent,
        TrainerAgent,
    )
    from swarm import Swarm

    agent_map = {
        "CodeReviewAgent": CodeReviewAgent,
        "SecurityAgent": SecurityAgent,
        "RepoScannerAgent": RepoScannerAgent,
        "IssueTriageAgent": IssueTriageAgent,
        "TrainerAgent": TrainerAgent,
        "TradingBotAgent": TradingBotAgent,
        "DiagnosticsAgent": DiagnosticsAgent,
        "SandboxAgent": SandboxAgent,
        "DocAgent": DocAgent,
        "DatabaseAgent": DatabaseAgent,
        "ApiLearningAgent": ApiLearningAgent,
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
# trade command
# ---------------------------------------------------------------------------


@cli.command("trade")
@click.option("--symbol", required=True, help="Trading symbol, e.g. BTC/USDT, AAPL, EUR/USD.")
@click.option(
    "--asset-class",
    default="crypto",
    show_default=True,
    type=click.Choice(["crypto", "stocks", "forex"], case_sensitive=False),
    help="Asset class.",
)
@click.option("--market-data", required=True, help="Market data summary or price action text.")
@click.option("--rl-history", default="", help="Reinforcement-learning performance history.")
@click.option(
    "--sandbox/--live",
    default=True,
    show_default=True,
    help="Run in sandbox mode (no live execution).",
)
def trade_cmd(
    symbol: str,
    asset_class: str,
    market_data: str,
    rl_history: str,
    sandbox: bool,
) -> None:
    """Run the TradingBotAgent to generate a trading decision."""
    from agents import TradingBotAgent

    console.print(
        f"[bold yellow]📈 TradingBotAgent:[/bold yellow] {symbol} ({asset_class}) "
        f"| sandbox={sandbox}"
    )
    agent = TradingBotAgent()
    result = agent.run(
        {
            "symbol": symbol,
            "asset_class": asset_class,
            "market_data": market_data,
            "rl_history": rl_history,
            "sandbox": sandbox,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    decision = result.get("decision", {})
    console.print(
        Panel(
            f"Action    : [bold]{decision.get('action', 'N/A')}[/bold]\n"
            f"Confidence: {decision.get('confidence', 'N/A')}\n"
            f"Strategy  : {decision.get('strategy', 'N/A')}\n"
            f"Risk      : {decision.get('risk_level', 'N/A')}\n"
            f"Rationale : {decision.get('rationale', 'N/A')}",
            title=f"💹 {symbol} Trading Decision",
        )
    )


# ---------------------------------------------------------------------------
# diagnose command
# ---------------------------------------------------------------------------


@cli.command("diagnose")
@click.option("--target", required=True, help="Target label (repo, component, etc.).")
@click.option("--error-logs", default="", help="Error or exception log text.")
@click.option("--code", default="", help="Code snippet to analyse.")
@click.option("--workflow", default="", help="CI/CD workflow definition.")
@click.option("--output", default=None, help="Write JSON results to this file.")
def diagnose_cmd(
    target: str, error_logs: str, code: str, workflow: str, output: str | None
) -> None:
    """Run the DiagnosticsAgent to analyse and resolve issues."""
    from agents import DiagnosticsAgent

    console.print(f"[bold red]🔍 DiagnosticsAgent:[/bold red] {target}")
    agent = DiagnosticsAgent()
    result = agent.run(
        {
            "target": target,
            "error_logs": error_logs,
            "code_snippets": code,
            "workflow": workflow,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    diagnostics = result.get("diagnostics", {})
    console.print(
        Panel(
            f"Severity : [bold]{diagnostics.get('severity', 'N/A')}[/bold]\n"
            f"Issues   : {len(diagnostics.get('issues_found', []))}\n"
            f"Summary  : {diagnostics.get('summary', 'N/A')}",
            title="🩺 Diagnostics Report",
        )
    )

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        console.print(f"[green]Results written to {output}[/green]")


# ---------------------------------------------------------------------------
# sandbox command
# ---------------------------------------------------------------------------


@cli.command("sandbox")
@click.option("--experiment", required=True, help="Description of the experiment or RL task.")
@click.option(
    "--type",
    "experiment_type",
    default="simulation",
    show_default=True,
    type=click.Choice(["rl_training", "simulation", "diagnostics", "api_test"]),
    help="Experiment type.",
)
@click.option("--real-world-data", default="", help="Real-world data samples for training.")
def sandbox_cmd(experiment: str, experiment_type: str, real_world_data: str) -> None:
    """Configure and launch a sandbox environment via SandboxAgent."""
    from agents import SandboxAgent

    console.print(f"[bold cyan]🧪 SandboxAgent:[/bold cyan] {experiment_type}")
    agent = SandboxAgent()
    result = agent.run(
        {
            "experiment": experiment,
            "experiment_type": experiment_type,
            "real_world_data": real_world_data,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    cfg = result.get("sandbox_config", {})
    console.print(
        Panel(
            f"Sandbox ID    : {cfg.get('sandbox_id', 'N/A')}\n"
            f"Experiment    : {cfg.get('experiment_type', 'N/A')}\n"
            f"RL Algorithm  : {cfg.get('training_plan', {}).get('algorithm', 'N/A')}\n"
            f"Status        : {cfg.get('status', 'N/A')}",
            title="🧪 Sandbox Configuration",
        )
    )


# ---------------------------------------------------------------------------
# docs command
# ---------------------------------------------------------------------------


@cli.command("docs")
@click.option("--repo", required=True, help="owner/repo to document.")
@click.option("--max-files", default=20, show_default=True)
@click.option(
    "--no-transparency-log",
    is_flag=True,
    default=False,
    help="Omit the transparency log section.",
)
@click.option("--output", default=None, help="Write Markdown docs to this file.")
def docs_cmd(repo: str, max_files: int, no_transparency_log: bool, output: str | None) -> None:
    """Generate project documentation using the DocAgent."""
    from agents import DocAgent

    console.print(f"[bold green]📄 DocAgent:[/bold green] {repo}")
    agent = DocAgent()
    result = agent.run(
        {
            "repo": repo,
            "max_files": max_files,
            "include_transparency_log": not no_transparency_log,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    doc = result.get("documentation", "")
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(doc)
        console.print(f"[green]Documentation written to {output}[/green]")
    else:
        console.print(doc)


# ---------------------------------------------------------------------------
# db command
# ---------------------------------------------------------------------------


@cli.command("db")
@click.option("--db-type", required=True, help="Database type, e.g. PostgreSQL, MongoDB.")
@click.option("--schema", default="", help="Schema definition or data model description.")
@click.option("--query-logs", default="", help="Slow query log or problematic queries.")
@click.option("--metrics", default="", help="Performance metrics text.")
@click.option("--output", default=None, help="Write JSON report to this file.")
def db_cmd(
    db_type: str, schema: str, query_logs: str, metrics: str, output: str | None
) -> None:
    """Analyse and optimise a database using the DatabaseAgent."""
    from agents import DatabaseAgent

    console.print(f"[bold magenta]🗄️  DatabaseAgent:[/bold magenta] {db_type}")
    agent = DatabaseAgent()
    result = agent.run(
        {
            "db_type": db_type,
            "schema": schema,
            "query_logs": query_logs,
            "metrics": metrics,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    report = result.get("db_report", {})
    console.print(
        Panel(
            f"Health Score : [bold]{report.get('health_score', 'N/A')}[/bold] / 100\n"
            f"Optimisations: {len(report.get('optimisations', []))}\n"
            f"Scaling      : {report.get('scaling_recommendation', {}).get('action', 'N/A')}\n"
            f"Summary      : {report.get('summary', 'N/A')}",
            title=f"🗄️  {db_type} Database Report",
        )
    )

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        console.print(f"[green]Results written to {output}[/green]")


# ---------------------------------------------------------------------------
# api-learn command
# ---------------------------------------------------------------------------


@cli.command("api-learn")
@click.option("--api-spec", required=True, help="API specification text or file path.")
@click.option("--api-name", default="unknown-api", show_default=True, help="API name.")
@click.option(
    "--target-bots",
    default="",
    help="Comma-separated list of bot agents to receive training examples.",
)
@click.option(
    "--no-lifecycle",
    is_flag=True,
    default=False,
    help="Skip lifecycle simulation.",
)
@click.option("--output", default=None, help="Write JSON learning data to this file.")
def api_learn_cmd(
    api_spec: str,
    api_name: str,
    target_bots: str,
    no_lifecycle: bool,
    output: str | None,
) -> None:
    """Run the ApiLearningAgent to teach bots API functionalities."""
    import os as _os

    from agents import ApiLearningAgent

    # Allow passing a file path instead of inline spec
    if _os.path.isfile(api_spec):
        with open(api_spec, encoding="utf-8") as fh:
            api_spec = fh.read()

    bots = [b.strip() for b in target_bots.split(",") if b.strip()]

    console.print(f"[bold blue]🔌 ApiLearningAgent:[/bold blue] {api_name}")
    agent = ApiLearningAgent()
    result = agent.run(
        {
            "api_spec": api_spec,
            "api_name": api_name,
            "target_bots": bots,
            "simulate_lifecycle": not no_lifecycle,
        }
    )

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    learning = result.get("learning_data", {})
    console.print(
        Panel(
            f"API           : {learning.get('api_name', api_name)}\n"
            f"Endpoints     : {len(learning.get('endpoints_discovered', []))}\n"
            f"Simulations   : {len(learning.get('lifecycle_simulations', []))}\n"
            f"Training exs  : {len(learning.get('training_examples', []))}\n"
            f"Teaching notes: {learning.get('bot_teaching_notes', 'N/A')[:120]}",
            title="🔌 API Learning Report",
        )
    )

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        console.print(f"[green]Results written to {output}[/green]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_results_table(results: list[dict]) -> None:def _print_results_table(results: list[dict]) -> None:
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
