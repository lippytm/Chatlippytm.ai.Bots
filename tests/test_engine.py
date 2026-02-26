"""
Tests for the Chatlippytm.ai.Bots AI DevOps Engine.

All OpenAI and GitHub API calls are mocked so tests run offline without
requiring real credentials.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# BaseAgent
# ---------------------------------------------------------------------------


class TestBaseAgent:
    """Tests for BaseAgent abstract base class behaviour."""

    def _make_agent(self):
        """Return a minimal concrete subclass of BaseAgent."""
        from agents.base_agent import BaseAgent

        class _DummyAgent(BaseAgent):
            name = "DummyAgent"

            def run(self, context):
                return self._base_result(message="ok")

        with patch("agents.base_agent.OpenAI"):
            return _DummyAgent(model="gpt-4o-mini", temperature=0.1)

    def test_base_result_contains_agent_name(self):
        agent = self._make_agent()
        result = agent._base_result()
        assert result["agent"] == "DummyAgent"
        assert result["status"] == "ok"

    def test_base_result_extra_fields(self):
        agent = self._make_agent()
        result = agent._base_result(status="error", foo="bar")
        assert result["status"] == "error"
        assert result["foo"] == "bar"

    def test_reset_conversation(self):
        agent = self._make_agent()
        agent._conversation = [{"role": "user", "content": "hi"}]
        agent.reset_conversation()
        assert agent._conversation == []

    @patch("agents.base_agent.OpenAI")
    def test_chat_calls_openai(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="review text"))]
        )

        from agents.base_agent import BaseAgent

        class _A(BaseAgent):
            name = "A"
            def run(self, ctx):
                return self._base_result()

        agent = _A(model="gpt-4o-mini")
        result = agent.chat("system", "user")
        assert result == "review text"
        mock_client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# CodeReviewAgent
# ---------------------------------------------------------------------------


class TestCodeReviewAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_review(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="## Review\nLooks good!"))]
        )

        from agents.code_review_agent import CodeReviewAgent

        agent = CodeReviewAgent()
        result = agent.run({
            "repo": "owner/repo",
            "pr_number": 1,
            "diff": "- old line\n+ new line",
            "title": "Test PR",
        })

        assert result["status"] == "ok"
        assert "review" in result
        assert "Looks good!" in result["review"]

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_diff(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.code_review_agent import CodeReviewAgent

        agent = CodeReviewAgent()
        result = agent.run({"repo": "owner/repo", "pr_number": 1})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# IssueTriageAgent
# ---------------------------------------------------------------------------


class TestIssueTriageAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_triage(self, mock_openai_cls):
        triage_payload = {
            "priority": "high",
            "labels": ["bug"],
            "summary": "A bug was found.",
            "suggested_assignee_role": "backend-engineer",
            "needs_more_info": False,
            "triage_comment": "Thanks for reporting!",
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(triage_payload)))]
        )

        from agents.issue_triage_agent import IssueTriageAgent

        agent = IssueTriageAgent()
        result = agent.run({
            "repo": "owner/repo",
            "issue_number": 7,
            "title": "App crashes on startup",
            "body": "Steps to reproduce …",
        })

        assert result["status"] == "ok"
        assert result["triage"]["priority"] == "high"
        assert "bug" in result["triage"]["labels"]

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_title(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.issue_triage_agent import IssueTriageAgent

        agent = IssueTriageAgent()
        result = agent.run({"repo": "owner/repo", "issue_number": 1})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# SwarmTask
# ---------------------------------------------------------------------------


class TestSwarmTask:
    def test_initial_state(self):
        from swarm.task import SwarmTask, TaskStatus

        t = SwarmTask(agent_name="TestAgent", context={"repo": "a/b"})
        assert t.status == TaskStatus.PENDING
        assert t.error == ""

    def test_lifecycle(self):
        from swarm.task import SwarmTask, TaskStatus

        t = SwarmTask(agent_name="A", context={})
        t.mark_running()
        assert t.status == TaskStatus.RUNNING
        t.mark_done({"status": "ok"})
        assert t.status == TaskStatus.DONE
        assert t.result == {"status": "ok"}

    def test_mark_error(self):
        from swarm.task import SwarmTask, TaskStatus

        t = SwarmTask(agent_name="A", context={})
        t.mark_error("connection timeout")
        assert t.status == TaskStatus.ERROR
        assert t.error == "connection timeout"

    def test_to_dict(self):
        from swarm.task import SwarmTask

        t = SwarmTask(agent_name="A", context={}, task_id="abc123")
        t.mark_done({"foo": "bar"})
        d = t.to_dict()
        assert d["task_id"] == "abc123"
        assert d["status"] == "done"
        assert d["result"] == {"foo": "bar"}


# ---------------------------------------------------------------------------
# Swarm orchestrator
# ---------------------------------------------------------------------------


class TestSwarm:
    def _make_swarm(self):
        from swarm.swarm import Swarm
        return Swarm(max_workers=2)

    def _make_mock_agent(self, name="MockAgent", result=None):
        from agents.base_agent import BaseAgent

        class _MockAgent(BaseAgent):
            def run(self, context):
                return result or self._base_result(repo=context.get("repo"))

        with patch("agents.base_agent.OpenAI"):
            a = _MockAgent()
        a.name = name
        return a

    def test_register_and_list_agents(self):
        swarm = self._make_swarm()
        agent = self._make_mock_agent("AgentX")
        swarm.register(agent)
        assert len(swarm.agents) == 1
        assert swarm.agents[0].name == "AgentX"

    def test_unregister(self):
        swarm = self._make_swarm()
        agent = self._make_mock_agent("AgentY")
        swarm.register(agent)
        swarm.unregister("AgentY")
        assert len(swarm.agents) == 0

    def test_run_all_produces_results(self):
        swarm = self._make_swarm()
        agent = self._make_mock_agent("AgentZ", result={"status": "ok", "agent": "AgentZ"})
        swarm.register(agent)

        results = swarm.run_all(repos=["owner/repo"])
        assert len(results) == 1
        assert results[0]["status"] == "done"

    def test_run_all_empty_agents(self):
        swarm = self._make_swarm()
        results = swarm.run_all(repos=["owner/repo"])
        assert results == []

    def test_run_agent_unknown(self):
        swarm = self._make_swarm()
        result = swarm.run_agent("NonExistent", {})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# TrainingPipeline
# ---------------------------------------------------------------------------


class TestTrainingPipeline:
    def test_merge_empty_dir(self, tmp_path):
        from training.pipeline import TrainingPipeline

        pipeline = TrainingPipeline(repos=[], data_dir=tmp_path / "data")
        merged, count = pipeline._merge_and_validate()
        assert merged is None
        assert count == 0

    def test_merge_valid_jsonl(self, tmp_path):
        from training.pipeline import TrainingPipeline

        data_dir = tmp_path / "data"
        data_dir.mkdir()
        example = json.dumps({
            "messages": [
                {"role": "system", "content": "You are an AI."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ]
        })
        (data_dir / "test.jsonl").write_text(example + "\ninvalid line\n")

        pipeline = TrainingPipeline(repos=[], data_dir=data_dir)
        merged, count = pipeline._merge_and_validate()
        assert count == 1
        assert merged is not None
        assert merged.exists()


# ---------------------------------------------------------------------------
# TradingBotAgent
# ---------------------------------------------------------------------------


class TestTradingBotAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_decision(self, mock_openai_cls):
        decision = {
            "action": "buy",
            "confidence": 0.85,
            "strategy": "momentum",
            "rationale": "Strong uptrend detected.",
            "risk_level": "medium",
            "suggested_position_size": 0.05,
            "stop_loss_pct": 2.0,
            "take_profit_pct": 4.0,
            "rl_recommendation": None,
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(decision)))]
        )

        from agents.trading_bot_agent import TradingBotAgent

        agent = TradingBotAgent()
        result = agent.run(
            {
                "symbol": "BTC/USDT",
                "asset_class": "crypto",
                "market_data": "Price: 65000 | RSI: 72 | MACD: bullish",
                "sandbox": True,
            }
        )

        assert result["status"] == "ok"
        assert result["symbol"] == "BTC/USDT"
        assert result["decision"]["action"] == "buy"
        assert result["sandbox"] is True

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_symbol(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.trading_bot_agent import TradingBotAgent

        agent = TradingBotAgent()
        result = agent.run({"asset_class": "crypto", "market_data": "some data"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_unsupported_asset_class(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.trading_bot_agent import TradingBotAgent

        agent = TradingBotAgent()
        result = agent.run(
            {"symbol": "AAPL", "asset_class": "options", "market_data": "some data"}
        )
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_market_data(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.trading_bot_agent import TradingBotAgent

        agent = TradingBotAgent()
        result = agent.run({"symbol": "EUR/USD", "asset_class": "forex"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# DiagnosticsAgent
# ---------------------------------------------------------------------------


class TestDiagnosticsAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_report(self, mock_openai_cls):
        diag_payload = {
            "severity": "medium",
            "issues_found": [
                {
                    "type": "null_pointer",
                    "location": "app.py:42",
                    "description": "Possible None dereference",
                    "fix": "Add None check",
                }
            ],
            "workflow_optimisations": ["Cache test results"],
            "model_evaluation": {"accuracy_estimate": 0.92, "notes": "Good"},
            "auto_resolved": [],
            "summary": "One medium issue found.",
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(diag_payload)))]
        )

        from agents.diagnostics_agent import DiagnosticsAgent

        agent = DiagnosticsAgent()
        result = agent.run(
            {
                "target": "myapp",
                "error_logs": "NullPointerException at app.py:42",
            }
        )

        assert result["status"] == "ok"
        assert result["target"] == "myapp"
        assert result["diagnostics"]["severity"] == "medium"

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_no_input(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.diagnostics_agent import DiagnosticsAgent

        agent = DiagnosticsAgent()
        result = agent.run({"target": "myapp"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# SandboxAgent
# ---------------------------------------------------------------------------


class TestSandboxAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_config(self, mock_openai_cls):
        sandbox_payload = {
            "sandbox_id": "sb-001",
            "experiment_type": "rl_training",
            "environment_config": {
                "isolation_level": "strict",
                "resource_limits": {"cpu_cores": 2, "memory_mb": 512, "timeout_s": 300},
                "allowed_actions": ["trade", "observe"],
            },
            "training_plan": {
                "algorithm": "PPO",
                "episodes": 100,
                "learning_rate": 0.0003,
                "reward_function": "profit_pct",
            },
            "safety_checks": ["no live API calls", "budget cap enforced"],
            "expected_outcomes": ["model convergence within 100 episodes"],
            "status": "ready",
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(sandbox_payload)))]
        )

        from agents.sandbox_agent import SandboxAgent

        agent = SandboxAgent()
        result = agent.run(
            {
                "experiment": "Train a crypto trading RL agent using PPO",
                "experiment_type": "rl_training",
            }
        )

        assert result["status"] == "ok"
        assert result["sandbox_config"]["status"] == "ready"
        assert result["experiment_type"] == "rl_training"

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_experiment(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.sandbox_agent import SandboxAgent

        agent = SandboxAgent()
        result = agent.run({})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# DocAgent
# ---------------------------------------------------------------------------


class TestDocAgent:
    @patch("agents.base_agent.OpenAI")
    @patch("agents.doc_agent.Github")
    def test_run_returns_documentation(self, mock_gh_cls, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="# My Project\nDocs here."))]
        )

        mock_repo = MagicMock()
        mock_repo.description = "Test repo"
        mock_readme = MagicMock()
        mock_readme.decoded_content = b"# README\nHello world"
        mock_repo.get_readme.return_value = mock_readme
        mock_repo.get_contents.return_value = [
            MagicMock(type="file", path="main.py"),
        ]
        mock_repo.get_commits.return_value = [
            MagicMock(commit=MagicMock(message="Initial commit"))
        ]
        mock_repo.get_issues.return_value = []
        mock_gh_cls.return_value.get_repo.return_value = mock_repo

        from agents.doc_agent import DocAgent

        agent = DocAgent()
        result = agent.run({"repo": "owner/repo"})

        assert result["status"] == "ok"
        assert "# My Project" in result["documentation"]

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_repo(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.doc_agent import DocAgent

        agent = DocAgent()
        result = agent.run({})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# DatabaseAgent
# ---------------------------------------------------------------------------


class TestDatabaseAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_report(self, mock_openai_cls):
        db_payload = {
            "db_type": "PostgreSQL",
            "health_score": 78,
            "optimisations": [
                {
                    "type": "index",
                    "description": "Add index on users.email",
                    "impact": "high",
                    "sql_or_command": "CREATE INDEX idx_users_email ON users(email);",
                }
            ],
            "scaling_recommendation": {
                "action": "scale_up",
                "rationale": "High CPU utilisation",
                "suggested_config": "Upgrade to db.r5.xlarge",
            },
            "anomalies": [],
            "maintenance_tasks": ["VACUUM ANALYZE users;"],
            "summary": "Database is healthy with one optimisation opportunity.",
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(db_payload)))]
        )

        from agents.database_agent import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.run(
            {
                "db_type": "PostgreSQL",
                "query_logs": "SELECT * FROM users WHERE email='x' took 2000ms",
            }
        )

        assert result["status"] == "ok"
        assert result["db_type"] == "PostgreSQL"
        assert result["db_report"]["health_score"] == 78

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_db_type(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.database_agent import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.run({"query_logs": "some log"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_no_context(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.database_agent import DatabaseAgent

        agent = DatabaseAgent()
        result = agent.run({"db_type": "MySQL"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# ApiLearningAgent
# ---------------------------------------------------------------------------


class TestApiLearningAgent:
    @patch("agents.base_agent.OpenAI")
    def test_run_returns_learning_data(self, mock_openai_cls):
        api_payload = {
            "api_name": "GitHub REST API",
            "endpoints_discovered": [
                {
                    "method": "GET",
                    "path": "/repos/{owner}/{repo}",
                    "description": "Get a repository",
                    "example_payload": None,
                }
            ],
            "lifecycle_simulations": [
                {
                    "scenario": "Create and merge a PR",
                    "steps": ["Create branch", "Push commits", "Open PR", "Merge PR"],
                    "expected_outcome": "PR merged successfully",
                }
            ],
            "training_examples": [
                {
                    "prompt": "How do I get repo details?",
                    "completion": "GET /repos/{owner}/{repo}",
                }
            ],
            "bot_teaching_notes": "Use pagination for large result sets.",
            "integration_recommendations": ["Use conditional requests with ETags"],
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(api_payload)))]
        )

        from agents.api_learning_agent import ApiLearningAgent

        agent = ApiLearningAgent()
        result = agent.run(
            {
                "api_spec": "GET /repos/{owner}/{repo} – Returns repository details.",
                "api_name": "GitHub REST API",
                "target_bots": ["TradingBotAgent", "DocAgent"],
            }
        )

        assert result["status"] == "ok"
        assert result["api_name"] == "GitHub REST API"
        assert len(result["learning_data"]["endpoints_discovered"]) == 1

    @patch("agents.base_agent.OpenAI")
    def test_run_error_on_missing_api_spec(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        from agents.api_learning_agent import ApiLearningAgent

        agent = ApiLearningAgent()
        result = agent.run({"api_name": "SomeAPI"})
        assert result["status"] == "error"
