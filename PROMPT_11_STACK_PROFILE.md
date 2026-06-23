# Prompt #11 Stack Profile

This file tracks the known technology and learning stack for Chatlippytm.ai.Bots.

## Repository

`lippytm/Chatlippytm.ai.Bots`

## Current Stack Status

Known stack: reviewed from README and requirements evidence.

Chatlippytm.ai.Bots is a Python-based AI agent swarm and GitHub automation project with:

- Python CLI entry point through `main.py`
- specialist agent modules under `agents/`
- swarm orchestration under `swarm/`
- training pipeline under `training/`
- GitHub Actions automation workflows
- YAML configuration through `config/config.yaml`
- OpenAI and LangChain dependencies
- PyGithub integration
- dotenv-based environment configuration
- pytest validation path

## Evidence Notes

README evidence identifies:

- Full Stack AI DevOps Synthetic Intelligence Engine framing
- automated code review agent
- repository health scanner agent
- issue triage agent
- security scanning agent
- training data collection and fine-tuning agent
- GitHub Actions workflows for auto-training, PR review, issue triage, security scan, and repo health
- local CLI commands for swarm, training, scan, and triage

`requirements.txt` evidence identifies:

- `openai`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `PyGithub`
- `pydantic`
- `python-dotenv`
- `requests`
- `tenacity`
- `tiktoken`
- `aiohttp`
- `asyncio-throttle`
- `rich`
- `click`
- `PyYAML`

## Language Categories

Relevant categories:

- Python
- AI-assisted development
- agent workflow design
- chatbot and prompt workflow design
- GitHub automation
- GitHub Actions
- training pipeline design
- configuration management
- security scanning workflow design
- documentation
- CRM and support systems
- GitHub practice

## Validation Path

Suggested validation sequence:

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `python -m pytest tests/ -v`
3. Review configuration: `config/config.yaml`
4. Check environment template: `.env.example`
5. Test CLI help if available: `python main.py --help`
6. Review GitHub Actions workflow files before enabling or modifying automation.

## Safety and RiskGate Notes

This repo touches GitHub automation, OpenAI API calls, issue triage, repository scanning, and optional training/fine-tuning workflows. Treat all API keys, repo tokens, automated PR comments, issue labels, and fine-tuning submissions as RiskGate-reviewed actions before production use.

## Prompt #11 Review Questions

1. Are all documented agents present under `agents/`?
2. Do the GitHub Actions workflows match the README architecture?
3. Are secrets and environment variable requirements documented clearly?
4. Are automated comments, issue labels, and scans safe for target repos?
5. Is the training pipeline collecting only appropriate repo data?
6. What is the next useful improvement?

## Next Action

Move this repo to `needs-review`, then validate the CLI, tests, config, workflows, and automation safety boundaries.
