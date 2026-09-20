# Chatlippytm.ai.Bots

> **Full Stack AI DevOps Synthetic Intelligence Engine**  
> Auto-training · Agent Swarms · ChatGPT-powered CI/CD

An AI Hub for Building Business of businesses. Another project place for "The Encyclopedia of Everything Applied" & "lippytm.AI" and my ManyChat and BotBuilders.com businesses of Businesses.

---

## Overview

Chatlippytm.ai.Bots is a **Full Stack AI DevOps Synthetic Intelligence Engine** built on OpenAI GPT-4o and the GitHub API. It deploys a coordinated **swarm** of specialised AI agents that:

| Capability | Agent | Trigger |
|---|---|---|
| Automated code review | `CodeReviewAgent` | Every pull request |
| Repository health reports | `RepoScannerAgent` | Weekly schedule |
| Auto issue triage & labelling | `IssueTriageAgent` | Every new issue |
| Security vulnerability scanning | `SecurityAgent` | Daily + every push |
| Training data collection & fine-tuning | `TrainerAgent` | Every push to `main` |

All workflows run automatically through **GitHub Actions**. No manual steps required once the secrets are configured.

---

## Jarvis Open-Source Orchestration Hub

This repository is the control plane for Jarvis-style assistant capabilities across your assistant repositories.

- Approved capabilities are curated in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/config/jarvis_registry.yaml`
- Managed target repositories and enabled modules are configured in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/config/config.yaml`
- The canonical capability matrix lives in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/docs/AI_JARVIS_CAPABILITY_MATRIX.md`
- Multi-repo defaults and monetization lanes let you reuse the same Jarvis hub across your business-of-businesses ventures

Use the CLI to inspect and validate the hub:

```bash
python main.py jarvis policy
python main.py jarvis inventory
python main.py jarvis targets
python main.py jarvis plan --repo lippytm/Chatlippytm.ai.Bots
python main.py jarvis bootstrap-target --repo lippytm/your-next-repo --lane commerce --venture-tag subscriptions
python main.py jarvis monetize --repo lippytm/your-next-repo --use-template --lane revenue
python main.py jarvis validate
```

The hub only approves capabilities that have a clear open-source license, fit one of the assistant categories, and are not redundant with the repo's existing orchestration, training, or security features.

---

## Architecture

```
Chatlippytm.ai.Bots/
│
├── agents/                   # Specialist AI agents
│   ├── base_agent.py         # Abstract base (OpenAI client, retry logic)
│   ├── code_review_agent.py  # PR code reviewer
│   ├── repo_scanner_agent.py # Repository health scanner
│   ├── trainer_agent.py      # Training data collector
│   ├── issue_triage_agent.py # Issue classifier & labeller
│   └── security_agent.py    # Security vulnerability scanner
│
├── swarm/                    # Swarm orchestration layer
│   ├── swarm.py              # Concurrent agent dispatcher (ThreadPoolExecutor)
│   └── task.py               # SwarmTask dataclass & status enum
│
├── training/                 # Auto-training pipeline
│   ├── pipeline.py           # Data collection → merge → fine-tune
│   ├── data/                 # Generated JSONL training examples (git-ignored)
│   └── reports/              # Pipeline run reports (git-ignored)
│
├── config/
│   ├── config.yaml           # Swarm, agent, pipeline & Jarvis target configuration
│   └── jarvis_registry.yaml  # Approved open-source Jarvis capability registry
│
├── .github/workflows/
│   ├── auto-train.yml        # Auto-training pipeline (push + weekly)
│   ├── ai-pr-review.yml      # AI code review on every PR
│   ├── ai-issue-triage.yml   # AI issue triage on every new issue
│   ├── ai-security-scan.yml  # Daily security scan
│   └── ai-repo-health.yml    # Weekly health report
│
├── main.py                   # CLI entry point
├── jarvis_hub.py             # Jarvis capability registry/config loader
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Configure Secrets

In your GitHub repository -> **Settings -> Secrets and variables -> Actions**, add:

| Secret | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions |

### 2. Configure Target Repositories

Edit `config/config.yaml` and add the repositories you want the swarm to manage:

```yaml
repositories:
  targets:
    - lippytm/Chatlippytm.ai.Bots
    - lippytm/your-other-repo
```

### 3. Local Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run the full swarm
python main.py swarm --repos lippytm/Chatlippytm.ai.Bots

# Run the auto-training pipeline
python main.py train --repos lippytm/Chatlippytm.ai.Bots

# Security scan a repo
python main.py scan --repo lippytm/Chatlippytm.ai.Bots

# Triage an issue
python main.py triage --repo lippytm/Chatlippytm.ai.Bots --issue 42
```

### 4. Manual Workflow Dispatch

Any workflow can be triggered manually from **Actions -> [workflow name] -> Run workflow**.

---

## Swarm API

```python
from agents import CodeReviewAgent, SecurityAgent, RepoScannerAgent
from swarm import Swarm

swarm = Swarm(max_workers=4)
swarm.register(CodeReviewAgent())
swarm.register(SecurityAgent())
swarm.register(RepoScannerAgent())

results = swarm.run_all(repos=["lippytm/Chatlippytm.ai.Bots"])
```

---

## Auto-Training Pipeline

The `TrainerAgent` + `TrainingPipeline` automatically:

1. Collects closed issues and PR discussions from target repositories
2. Uses GPT-4o to synthesise OpenAI fine-tuning JSONL examples
3. Validates and merges all examples into a single dataset
4. (Optional) Submits a fine-tuning job to the OpenAI API

```bash
# Collect data and optionally fine-tune
python main.py train \
  --repos lippytm/Chatlippytm.ai.Bots \
  --submit \
  --threshold 100
```

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Environment Variables

See `.env.example` for all available settings.
