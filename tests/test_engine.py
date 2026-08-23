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
# WalletAuthManager
# ---------------------------------------------------------------------------


class TestWalletAuthManager:
    def _make_manager(self):
        from web3.wallet_auth import WalletAuthManager
        return WalletAuthManager()

    def test_create_challenge_returns_string(self):
        mgr = self._make_manager()
        challenge = mgr.create_challenge("0xABC123")
        assert isinstance(challenge, str)
        assert "0xabc123" in challenge

    def test_verify_login_success(self):
        mgr = self._make_manager()
        address = "0xDEADBEEF"
        challenge = mgr.create_challenge(address)
        sig = mgr.sign_challenge(challenge)
        session = mgr.verify_login(address, sig)
        assert session is not None
        assert session.address == address.lower()
        assert session.is_valid()

    def test_verify_login_bad_signature(self):
        mgr = self._make_manager()
        address = "0xBAD"
        mgr.create_challenge(address)
        session = mgr.verify_login(address, "wrong_signature")
        assert session is None

    def test_verify_login_no_challenge(self):
        mgr = self._make_manager()
        session = mgr.verify_login("0xNOCHALLENGE", "any_sig")
        assert session is None

    def test_get_session_after_login(self):
        mgr = self._make_manager()
        address = "0xSESSION"
        challenge = mgr.create_challenge(address)
        sig = mgr.sign_challenge(challenge)
        mgr.verify_login(address, sig)
        session = mgr.get_session(address)
        assert session is not None

    def test_revoke_session(self):
        mgr = self._make_manager()
        address = "0xREVOKE"
        challenge = mgr.create_challenge(address)
        sig = mgr.sign_challenge(challenge)
        mgr.verify_login(address, sig)
        mgr.revoke_session(address)
        assert mgr.get_session(address) is None

    def test_grant_has_revoke_role(self):
        mgr = self._make_manager()
        address = "0xROLE"
        mgr.grant_role(address, "instructor")
        assert mgr.has_role(address, "instructor")
        mgr.revoke_role(address, "instructor")
        assert not mgr.has_role(address, "instructor")

    def test_list_roles(self):
        mgr = self._make_manager()
        address = "0xROLES"
        mgr.grant_role(address, "participant")
        mgr.grant_role(address, "admin")
        roles = mgr.list_roles(address)
        assert sorted(roles) == ["admin", "participant"]


# ---------------------------------------------------------------------------
# TokenRegistry
# ---------------------------------------------------------------------------


class TestTokenRegistry:
    def _make_registry(self):
        from web3.wallet_auth import TokenRegistry
        return TokenRegistry()

    def test_mint_increases_balance(self):
        reg = self._make_registry()
        new_bal = reg.mint("0xADDR", "workshop_completion")
        assert new_bal == 1
        assert reg.balance("0xADDR", "workshop_completion") == 1

    def test_mint_multiple(self):
        reg = self._make_registry()
        reg.mint("0xADDR", "streak_bonus", 5)
        assert reg.balance("0xADDR", "streak_bonus") == 5

    def test_burn_decreases_balance(self):
        reg = self._make_registry()
        reg.mint("0xADDR", "assignment_pass", 3)
        new_bal = reg.burn("0xADDR", "assignment_pass", 2)
        assert new_bal == 1

    def test_burn_insufficient_raises(self):
        reg = self._make_registry()
        reg.mint("0xADDR", "peer_review", 1)
        with pytest.raises(ValueError, match="Insufficient balance"):
            reg.burn("0xADDR", "peer_review", 5)

    def test_mint_invalid_amount_raises(self):
        reg = self._make_registry()
        with pytest.raises(ValueError):
            reg.mint("0xADDR", "tok", 0)

    def test_portfolio(self):
        reg = self._make_registry()
        reg.mint("0xADDR", "tok_a", 2)
        reg.mint("0xADDR", "tok_b", 3)
        portfolio = reg.portfolio("0xADDR")
        assert portfolio == {"tok_a": 2, "tok_b": 3}

    def test_transfer(self):
        reg = self._make_registry()
        reg.mint("0xSENDER", "workshop_completion", 5)
        reg.transfer("0xSENDER", "0xRECEIVER", "workshop_completion", 2)
        assert reg.balance("0xSENDER", "workshop_completion") == 3
        assert reg.balance("0xRECEIVER", "workshop_completion") == 2

    def test_callback_invoked(self):
        events = []
        from web3.wallet_auth import TokenRegistry
        reg = TokenRegistry(on_chain_callback=lambda a, t, d: events.append((a, t, d)))
        reg.mint("0xA", "tok", 1)
        assert len(events) == 1
        assert events[0] == ("0xa", "tok", 1)


# ---------------------------------------------------------------------------
# SandboxAgent
# ---------------------------------------------------------------------------


class TestSandboxAgent:
    def _make_agent(self):
        from agents.sandbox_agent import SandboxAgent
        with patch("agents.base_agent.OpenAI"):
            return SandboxAgent()

    def test_provision_success(self):
        agent = self._make_agent()
        result = agent.run({
            "action": "provision",
            "owner_address": "0xPARTICIPANT",
            "modules": ["coding", "ai_experimentation"],
        })
        assert result["status"] == "ok"
        assert result["sandbox"]["status"] == "running"
        assert "coding" in result["sandbox"]["modules"]

    def test_provision_missing_address(self):
        agent = self._make_agent()
        result = agent.run({"action": "provision"})
        assert result["status"] == "error"

    def test_terminate_success(self):
        agent = self._make_agent()
        prov = agent.run({
            "action": "provision",
            "owner_address": "0xUSER",
        })
        sid = prov["sandbox"]["sandbox_id"]
        result = agent.run({"action": "terminate", "sandbox_id": sid})
        assert result["status"] == "ok"
        assert agent.get_sandbox(sid) is None

    def test_terminate_unknown_sandbox(self):
        agent = self._make_agent()
        result = agent.run({"action": "terminate", "sandbox_id": "nonexistent"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_assist_returns_answer(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Here is the answer"))]
        )
        from agents.sandbox_agent import SandboxAgent
        agent = SandboxAgent()
        result = agent.run({
            "action": "assist",
            "sandbox_id": "sb001",
            "question": "How do I train a neural net?",
        })
        assert result["status"] == "ok"
        assert "answer" in result
        assert "Here is the answer" in result["answer"]

    def test_assist_missing_question(self):
        agent = self._make_agent()
        result = agent.run({"action": "assist", "sandbox_id": "sb001"})
        assert result["status"] == "error"

    def test_unknown_action(self):
        agent = self._make_agent()
        result = agent.run({"action": "fly_to_moon"})
        assert result["status"] == "error"

    def test_list_sandboxes(self):
        agent = self._make_agent()
        agent.run({"action": "provision", "owner_address": "0xA"})
        agent.run({"action": "provision", "owner_address": "0xB"})
        sandboxes = agent.list_sandboxes()
        assert len(sandboxes) == 2


# ---------------------------------------------------------------------------
# WorkshopAgent
# ---------------------------------------------------------------------------


class TestWorkshopAgent:
    def _make_agent(self):
        from agents.workshop_agent import WorkshopAgent
        with patch("agents.base_agent.OpenAI"):
            return WorkshopAgent()

    def test_list_templates(self):
        agent = self._make_agent()
        result = agent.run({"action": "list_templates"})
        assert result["status"] == "ok"
        assert result["count"] >= 4
        names = [t["name"] for t in result["templates"]]
        assert "intro-to-ai" in names
        assert "blockchain-dev" in names

    def test_load_template_success(self):
        agent = self._make_agent()
        result = agent.run({
            "action": "load_template",
            "template_name": "intro-to-ai",
        })
        assert result["status"] == "ok"
        assert result["template"]["difficulty"] == "beginner"

    def test_load_template_not_found(self):
        agent = self._make_agent()
        result = agent.run({
            "action": "load_template",
            "template_name": "nonexistent",
        })
        assert result["status"] == "error"

    def test_load_template_missing_name(self):
        agent = self._make_agent()
        result = agent.run({"action": "load_template"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_grade_success(self, mock_openai_cls):
        import json as _json
        grading_payload = {
            "score": 85,
            "grade": "B",
            "strengths": ["Clean code"],
            "improvements": ["Add docstrings"],
            "feedback": "Good job overall.",
            "copilot_hint": "Consider using list comprehensions.",
        }
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=_json.dumps(grading_payload)))]
        )
        from agents.workshop_agent import WorkshopAgent
        agent = WorkshopAgent()
        result = agent.run({
            "action": "grade",
            "submission": "def add(a, b): return a + b",
        })
        assert result["status"] == "ok"
        assert result["grading"]["score"] == 85
        assert result["grading"]["grade"] == "B"

    def test_grade_missing_submission(self):
        agent = self._make_agent()
        result = agent.run({"action": "grade"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_assist_success(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Use a for-loop."))]
        )
        from agents.workshop_agent import WorkshopAgent
        agent = WorkshopAgent()
        result = agent.run({
            "action": "assist",
            "question": "How do I iterate over a list?",
            "skill_level": "beginner",
        })
        assert result["status"] == "ok"
        assert "Use a for-loop." in result["answer"]

    def test_assist_missing_question(self):
        agent = self._make_agent()
        result = agent.run({"action": "assist"})
        assert result["status"] == "error"

    @patch("agents.base_agent.OpenAI")
    def test_task_guide_success(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="# Task Guide\n1. Step one"))]
        )
        from agents.workshop_agent import WorkshopAgent
        agent = WorkshopAgent()
        result = agent.run({
            "action": "task_guide",
            "topic": "smart contracts",
            "skill_level": "intermediate",
        })
        assert result["status"] == "ok"
        assert "guide" in result
        assert "Task Guide" in result["guide"]

    def test_task_guide_missing_topic(self):
        agent = self._make_agent()
        result = agent.run({"action": "task_guide"})
        assert result["status"] == "error"

    def test_unknown_action(self):
        agent = self._make_agent()
        result = agent.run({"action": "bake_cake"})
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# BrainKitAgent
# ---------------------------------------------------------------------------


class TestBrainKitAgent:
    def _make_agent(self):
        from agents.brainkit_agent import BrainKitAgent
        with patch("agents.base_agent.OpenAI"):
            return BrainKitAgent()

    def test_missing_repos_returns_error(self):
        agent = self._make_agent()
        result = agent.run({})
        assert result["status"] == "error"
        assert "repos" in result["message"]

    def test_unknown_workflow_returns_error(self):
        agent = self._make_agent()
        result = agent.run({
            "repos": ["owner/repo"],
            "workflows": ["nonexistent-workflow"],
        })
        assert result["status"] == "error"
        assert "nonexistent-workflow" in result["message"]

    def test_dry_run_reports_files_without_api_calls(self):
        agent = self._make_agent()
        result = agent.run({
            "repos": ["owner/repo1", "owner/repo2"],
            "dry_run": True,
        })
        assert result["status"] == "ok"
        assert result["dry_run"] is True
        assert result["repos_processed"] == 2
        assert len(result["results"]) == 2
        for r in result["results"]:
            assert r["status"] == "ok"
            assert r["dry_run"] is True
            # All five workflows + the brainkit config
            assert len(r["files"]) == 6

    def test_dry_run_subset_of_workflows(self):
        agent = self._make_agent()
        result = agent.run({
            "repos": ["owner/repo"],
            "workflows": ["ai-pr-review", "ai-security-scan"],
            "dry_run": True,
        })
        assert result["status"] == "ok"
        files = result["results"][0]["files"]
        assert ".github/workflows/ai-pr-review.yml" in files
        assert ".github/workflows/ai-security-scan.yml" in files
        # Brainkit config is always included
        assert ".github/brainkit.yaml" in files
        # Other workflows must not be present
        assert ".github/workflows/auto-train.yml" not in files

    def test_available_workflows_returns_all_five(self):
        from agents.brainkit_agent import BrainKitAgent
        workflows = BrainKitAgent.available_workflows()
        assert len(workflows) == 5
        assert "ai-pr-review" in workflows
        assert "ai-security-scan" in workflows
        assert "ai-issue-triage" in workflows
        assert "ai-repo-health" in workflows
        assert "auto-train" in workflows

    def test_github_api_error_reported_per_repo(self):
        """A GithubException on one repo is captured and does not abort others."""
        from agents.brainkit_agent import BrainKitAgent
        from github import GithubException

        with patch("agents.base_agent.OpenAI"):
            agent = BrainKitAgent()

        mock_gh = MagicMock()
        mock_gh.get_repo.side_effect = GithubException(404, "Not Found", {})

        with patch("agents.brainkit_agent.Github", return_value=mock_gh):
            result = agent.run({
                "repos": ["owner/missing-repo"],
                "dry_run": False,
            })

        assert result["repos_processed"] == 1
        assert result["results"][0]["status"] == "error"
        assert "Not Found" in result["results"][0]["message"]

    def test_install_creates_new_files(self):
        """Files that don't exist yet should be created via create_file."""
        from agents.brainkit_agent import BrainKitAgent
        from github import GithubException

        with patch("agents.base_agent.OpenAI"):
            agent = BrainKitAgent()

        mock_repo = MagicMock()
        # Simulate that get_contents raises (file doesn't exist) for every path
        mock_repo.get_contents.side_effect = GithubException(404, "Not Found", {})
        mock_repo.create_file.return_value = MagicMock()

        mock_gh = MagicMock()
        mock_gh.get_repo.return_value = mock_repo

        with patch("agents.brainkit_agent.Github", return_value=mock_gh):
            result = agent.run({
                "repos": ["owner/new-repo"],
                "workflows": ["ai-pr-review"],
                "dry_run": False,
            })

        assert result["status"] == "ok"
        r = result["results"][0]
        assert r["status"] == "ok"
        # ai-pr-review.yml + brainkit.yaml
        assert len(r["installed"]) == 2
        assert r["errors"] == []
