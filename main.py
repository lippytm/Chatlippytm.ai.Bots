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
        IssueTriageAgent,
        MonetizationAgent,
        RepoScannerAgent,
        SecurityAgent,
        TrainerAgent,
        WorkshopAgent,
        SandboxAgent,
    )
    from swarm import Swarm

    agent_map = {
        "CodeReviewAgent": CodeReviewAgent,
        "SecurityAgent": SecurityAgent,
        "RepoScannerAgent": RepoScannerAgent,
        "IssueTriageAgent": IssueTriageAgent,
        "TrainerAgent": TrainerAgent,
        "WorkshopAgent": WorkshopAgent,
        "SandboxAgent": SandboxAgent,
        "MonetizationAgent": MonetizationAgent,
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
# workshop command
# ---------------------------------------------------------------------------


@cli.command("workshop")
@click.option(
    "--action",
    required=True,
    type=click.Choice(
        ["list-templates", "load-template", "grade", "assist", "task-guide"],
        case_sensitive=False,
    ),
    help="Workshop action to perform.",
)
@click.option("--template", default=None, help="Template name (for load-template).")
@click.option("--submission", default=None, help="Participant submission text (for grade).")
@click.option("--rubric", default=None, help="Grading rubric (for grade).")
@click.option("--question", default=None, help="Question or code snippet (for assist).")
@click.option("--topic", default=None, help="Topic for task guide generation.")
@click.option(
    "--skill-level",
    default="intermediate",
    show_default=True,
    type=click.Choice(["beginner", "intermediate", "advanced"], case_sensitive=False),
    help="Participant skill level.",
)
@click.option("--output", default=None, help="Write JSON result to this file.")
def workshop_cmd(
    action: str,
    template: str | None,
    submission: str | None,
    rubric: str | None,
    question: str | None,
    topic: str | None,
    skill_level: str,
    output: str | None,
) -> None:
    """Run AI-powered workshop actions (templates, grading, assistance)."""
    import json as _json

    from agents import WorkshopAgent

    agent = WorkshopAgent()

    # Normalise action (CLI uses hyphens; agent uses underscores)
    internal_action = action.replace("-", "_")

    context: dict = {"action": internal_action, "skill_level": skill_level}
    if template:
        context["template_name"] = template
    if submission:
        context["submission"] = submission
    if rubric:
        context["rubric"] = rubric
    if question:
        context["question"] = question
    if topic:
        context["topic"] = topic

    result = agent.run(context)

    if result.get("status") == "error":
        console.print(f"[red]Error: {result.get('message')}[/red]")
        sys.exit(1)

    console.print(Panel(
        _json.dumps(result, indent=2),
        title=f"🎓 Workshop – {action}",
    ))

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            _json.dump(result, fh, indent=2)
        console.print(f"[green]Result written to {output}[/green]")


# ---------------------------------------------------------------------------
# jarvis command group
# ---------------------------------------------------------------------------


@cli.group("jarvis")
def jarvis_group() -> None:
    """Inspect and validate the Jarvis open-source capability hub."""


@jarvis_group.command("policy")
def jarvis_policy_cmd() -> None:
    """Print the Jarvis open-source policy definition."""
    from jarvis_hub import load_hub_config

    hub = load_hub_config()
    policy = hub["registry"].get("policy", {})
    console.print(
            Panel.fit(
                f"{policy.get('definition', 'No policy definition found.')}\n\n"
                f"Allowed licenses: {', '.join(policy.get('allowed_licenses', []))}\n"
                f"Categories      : {', '.join(policy.get('categories', []))}\n"
                f"Excluded if     : {', '.join(policy.get('excluded_conditions', []))}",
                title="🧭 Jarvis Open-Source Policy",
            )
    )


@jarvis_group.command("inventory")
@click.option(
    "--category",
    default=None,
    help="Filter inventory by category.",
)
@click.option(
    "--phase",
    default=None,
    help="Filter inventory by rollout phase.",
)
@click.option(
    "--strategy",
    default=None,
    help="Filter inventory by integration strategy.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
@click.option("--output", default=None, help="Write inventory output to this file.")
def jarvis_inventory_cmd(
    category: str | None,
    phase: str | None,
    strategy: str | None,
    output_format: str,
    output: str | None,
) -> None:
    """List approved Jarvis capabilities from the registry."""
    from jarvis_hub import capabilities_from_registry, filter_capabilities, load_hub_config

    hub = load_hub_config()
    capabilities = filter_capabilities(
            capabilities_from_registry(hub["registry"]),
            category=category,
            phase=phase,
            strategy=strategy,
    )

    if output_format == "json":
            payload = [
                {
                    "id": cap.id,
                    "name": cap.name,
                    "category": cap.category,
                    "phase": cap.phase,
                    "license": cap.license,
                    "maturity": cap.maturity,
                    "integration_strategy": cap.integration_strategy,
                    "owner_repo": cap.owner_repo,
                }
                for cap in capabilities
            ]
            _emit_output(payload, output)
            return

    table = Table(title="Jarvis Capability Inventory", show_lines=True)
    table.add_column("ID", style="cyan")
    table.add_column("Category")
    table.add_column("Phase")
    table.add_column("License")
    table.add_column("Strategy")
    table.add_column("Owner Repo")
    for cap in capabilities:
            table.add_row(
                cap.id,
                cap.category,
                cap.phase,
                cap.license,
                cap.integration_strategy,
                cap.owner_repo,
            )
    console.print(table)
    if output:
            _emit_output(
                [
                    {
                        "id": cap.id,
                        "name": cap.name,
                        "category": cap.category,
                        "phase": cap.phase,
                        "license": cap.license,
                        "maturity": cap.maturity,
                        "integration_strategy": cap.integration_strategy,
                        "owner_repo": cap.owner_repo,
                    }
                    for cap in capabilities
                ],
                output,
            )


@jarvis_group.command("targets")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
def jarvis_targets_cmd(output_format: str) -> None:
    """List managed Jarvis target repositories and enabled modules."""
    from jarvis_hub import load_hub_config, targets_from_config

    hub = load_hub_config()
    targets = targets_from_config(hub["config"])

    if output_format == "json":
            console.print_json(
                json.dumps(
                    [
                        {
                            "repo": target.repo,
                            "role": target.role,
                            "monetization_lane": target.monetization_lane,
                            "monetization_maturity": target.monetization_maturity,
                            "venture_tags": target.venture_tags,
                            "enabled_modules": target.enabled_modules,
                            "planned_modules": target.planned_modules,
                            "phases": target.phases,
                        }
                        for target in targets
                    ]
                )
            )
            return

    table = Table(title="Jarvis Managed Targets", show_lines=True)
    table.add_column("Repo", style="cyan")
    table.add_column("Role")
    table.add_column("Lane")
    table.add_column("Enabled Modules")
    table.add_column("Planned Modules")
    for target in targets:
            table.add_row(
                target.repo,
                target.role,
                target.monetization_lane,
                ", ".join(target.enabled_modules) or "-",
                ", ".join(target.planned_modules) or "-",
            )
    console.print(table)


@jarvis_group.command("plan")
@click.option("--repo", required=True, help="Managed target repo to plan.")
@click.option("--phase", default=None, help="Optional phase filter.")
@click.option("--use-template", is_flag=True, default=False, help="Allow fallback to the default target template.")
@click.option("--lane", default=None, help="Override monetization lane when using the template.")
@click.option("--maturity", default=None, help="Override monetization maturity when using the template.")
@click.option(
    "--venture-tag",
    "venture_tags",
    multiple=True,
    help="Repeatable venture tag override when using the template.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
@click.option("--output", default=None, help="Write plan output to this file.")
def jarvis_plan_cmd(
    repo: str,
    phase: str | None,
    use_template: bool,
    lane: str | None,
    maturity: str | None,
    venture_tags: tuple[str, ...],
    output_format: str,
    output: str | None,
) -> None:
    """Build the approved Jarvis rollout plan for a managed repository."""
    from jarvis_hub import build_target_plan, load_hub_config

    try:
            plan = build_target_plan(
                load_hub_config(),
                repo=repo,
                phase=phase,
                use_template=use_template,
                lane=lane,
                maturity=maturity,
                venture_tags=list(venture_tags) if venture_tags else None,
            )
    except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            sys.exit(1)

    if output_format == "json":
            _emit_output(plan, output)
            return

    enabled = ", ".join(item["id"] for item in plan["enabled_modules"]) or "-"
    planned = ", ".join(item["id"] for item in plan["planned_modules"]) or "-"
    missing = ", ".join(plan["missing_categories"]) or "-"
    console.print(
            Panel.fit(
                f"Repo              : {plan['repo']}\n"
                f"Role              : {plan['role']}\n"
                f"Phase filter      : {plan['phase_filter'] or 'all'}\n"
                f"Monetization lane : {plan['monetization']['lane']}\n"
                f"Maturity          : {plan['monetization']['maturity']}\n"
                f"Venture tags      : {', '.join(plan['monetization']['venture_tags']) or '-'}\n"
                f"Enabled modules   : {enabled}\n"
                f"Planned modules   : {planned}\n"
                f"Covered categories: {', '.join(plan['covered_categories']) or '-'}\n"
                f"Missing categories: {missing}",
                title="🛠️ Jarvis Target Plan",
            )
    )
    if output:
            _emit_output(plan, output)


@jarvis_group.command("validate")
def jarvis_validate_cmd() -> None:
    """Validate the Jarvis registry and managed target config."""
    from jarvis_hub import load_hub_config, validate_hub_definition

    errors = validate_hub_definition(load_hub_config())
    if errors:
            for error in errors:
                console.print(f"[red]✗ {error}[/red]")
            sys.exit(1)

    console.print("[green]✓ Jarvis capability registry is valid.[/green]")


@jarvis_group.command("bootstrap-target")
@click.option("--repo", required=True, help="Repository to bootstrap.")
@click.option("--lane", default="hub", show_default=True, help="Monetization lane.")
@click.option("--maturity", default="prototype", show_default=True, help="Monetization maturity.")
@click.option(
    "--venture-tag",
    "venture_tags",
    multiple=True,
    help="Repeatable venture tag to include in the generated target entry.",
)
def jarvis_bootstrap_target_cmd(
    repo: str,
    lane: str,
    maturity: str,
    venture_tags: tuple[str, ...],
) -> None:
    """Generate a reusable managed-target template for any repository."""
    from jarvis_hub import build_target_template, load_hub_config

    payload = build_target_template(
        load_hub_config(),
        repo=repo,
        lane=lane,
        maturity=maturity,
        venture_tags=list(venture_tags) if venture_tags else None,
    )
    _emit_output(payload, None)


@jarvis_group.command("monetize")
@click.option("--repo", required=True, help="Repository to monetize.")
@click.option("--phase", default=None, help="Optional phase filter.")
@click.option("--use-template", is_flag=True, default=False, help="Allow fallback to the default target template.")
@click.option("--lane", default=None, help="Override monetization lane.")
@click.option("--maturity", default=None, help="Override monetization maturity.")
@click.option(
    "--venture-tag",
    "venture_tags",
    multiple=True,
    help="Repeatable venture tag override.",
)
def jarvis_monetize_cmd(
    repo: str,
    phase: str | None,
    use_template: bool,
    lane: str | None,
    maturity: str | None,
    venture_tags: tuple[str, ...],
) -> None:
    """Map a repository's Jarvis modules to monetization options."""
    from agents.monetization_agent import MonetizationAgent
    from jarvis_hub import build_target_plan, load_hub_config

    try:
        plan = build_target_plan(
            load_hub_config(),
            repo=repo,
            phase=phase,
            use_template=use_template,
            lane=lane,
            maturity=maturity,
            venture_tags=list(venture_tags) if venture_tags else None,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    capabilities = [item["id"] for item in plan["enabled_modules"] + plan["planned_modules"]]
    agent = MonetizationAgent()
    result = agent.run(
        {
            "repo": repo,
            "lane": plan["monetization"]["lane"],
            "maturity": plan["monetization"]["maturity"],
            "capabilities": capabilities,
            "venture_tags": plan["monetization"]["venture_tags"],
        }
    )
    if result.get("status") == "error":
        console.print(f"[red]{result.get('message', 'Monetization planning failed.')}[/red]")
        sys.exit(1)
    console.print_json(json.dumps(result))


@jarvis_group.command("monetize-portfolio")
@click.option("--phase", default=None, help="Optional phase filter.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    show_default=True,
    help="Output format.",
)
def jarvis_monetize_portfolio_cmd(phase: str | None, output_format: str) -> None:
    """Generate monetization plans for all managed repositories."""
    from agents.monetization_agent import MonetizationAgent
    from jarvis_hub import build_target_plan, load_hub_config, targets_from_config

    hub = load_hub_config()
    agent = MonetizationAgent()
    results: list[dict] = []
    for target in targets_from_config(hub["config"]):
        plan = build_target_plan(hub, repo=target.repo, phase=phase)
        results.append(
            agent.run(
                {
                    "repo": target.repo,
                    "lane": plan["monetization"]["lane"],
                    "maturity": plan["monetization"]["maturity"],
                    "capabilities": [
                        item["id"] for item in plan["enabled_modules"] + plan["planned_modules"]
                    ],
                    "venture_tags": plan["monetization"]["venture_tags"],
                }
            )
        )

    if output_format == "json":
        console.print_json(json.dumps(results))
        return

    table = Table(title="Jarvis Portfolio Monetization", show_lines=True)
    table.add_column("Repo", style="cyan")
    table.add_column("Lane")
    table.add_column("Maturity")
    table.add_column("Value Role")
    table.add_column("Recommended Models")
    for result in results:
        table.add_row(
            result.get("repo", ""),
            result.get("lane", ""),
            result.get("maturity", ""),
            result.get("value_role", ""),
            ", ".join(result.get("recommended_models", [])),
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit_output(payload: dict | list, output: str | None) -> None:
    rendered = json.dumps(payload, indent=2)
    if output:
            with open(output, "w", encoding="utf-8") as fh:
                fh.write(rendered)
            console.print(f"[green]Results written to {output}[/green]")
            return
    console.print_json(rendered)


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
