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
| **AI BrainKit distribution** | `BrainKitAgent` | On demand / workflow dispatch |

All workflows run automatically through **GitHub Actions**. No manual steps required once the secrets are configured.

---

## Architecture

```
Chatlippytm.ai.Bots/
│
├── agents/                   # Specialist AI agents
│   ├── base_agent.py         # Abstract base (OpenAI client, retry logic)
│   ├── brainkit_agent.py     # BrainKit workflow distributor
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
│   └── config.yaml           # Swarm, agent & pipeline configuration
│
├── .github/workflows/
│   ├── auto-train.yml        # Auto-training pipeline (push + weekly)
│   ├── ai-pr-review.yml      # AI code review on every PR
│   ├── ai-issue-triage.yml   # AI issue triage on every new issue
│   ├── ai-security-scan.yml  # Daily security scan
│   └── ai-repo-health.yml    # Weekly health report
│
├── main.py                   # CLI entry point
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

## AI BrainKit – Distribute to All Repositories

The `BrainKitAgent` packages the five core AI workflows into a portable
**BrainKit** and installs them into any GitHub repository with a single
command.  Each target repo gets:

| File installed | Purpose |
|---|---|
| `.github/workflows/ai-pr-review.yml` | AI code review on every PR |
| `.github/workflows/ai-security-scan.yml` | Daily + push security scan |
| `.github/workflows/ai-issue-triage.yml` | Auto-triage every new issue |
| `.github/workflows/ai-repo-health.yml` | Weekly health report |
| `.github/workflows/auto-train.yml` | Push-triggered training pipeline |
| `.github/brainkit.yaml` | BrainKit configuration |

### Install BrainKit via CLI

```bash
# Install all five workflows into two repositories
python main.py brainkit \
  --repos lippytm/repo-one,lippytm/repo-two

# Install only the code-review and security workflows
python main.py brainkit \
  --repos lippytm/repo-one \
  --workflows ai-pr-review,ai-security-scan

# Preview what would be installed (no GitHub API calls)
python main.py brainkit \
  --repos lippytm/repo-one \
  --dry-run
```

### Install BrainKit via Python API

```python
from agents import BrainKitAgent

agent = BrainKitAgent()
result = agent.run({
    "repos": ["lippytm/repo-one", "lippytm/repo-two"],
    "branch": "main",
})
print(result)
```

### Configure Target Repositories

Edit `config/config.yaml` and add repositories to the `brainkit.targets`
list, then run the swarm or the `brainkit` CLI command:

```yaml
brainkit:
  targets:
    - lippytm/repo-one
    - lippytm/repo-two
  default_branch: main
  workflows:
    - ai-pr-review
    - ai-security-scan
    - ai-issue-triage
    - ai-repo-health
    - auto-train
```

> **Required secrets** – each target repository must have `OPENAI_API_KEY`
> configured in its **Settings → Secrets and variables → Actions** for the
> installed workflows to run.

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
