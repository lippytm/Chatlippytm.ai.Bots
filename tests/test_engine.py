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
