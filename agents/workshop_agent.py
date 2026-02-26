"""
WorkshopAgent – automates the full lifecycle of AI/Web3 workshops.

Responsibilities
----------------
1. **Template management** – list, load, and scaffold pre-built workshop
   templates (intro-to-AI, blockchain-dev, fine-tuning, etc.).
2. **Assignment grading** – evaluate participant submissions against
   a rubric and return structured feedback via the AI model.
3. **Real-time assistance** – operate as an always-on bot that answers
   workshop questions, provides GitHub Copilot-style code hints, and
   generates personalised task guides.
4. **Ecosystem connectivity** – surface workshop events to the broader
   AI Full Stack Synthetic Intelligence swarm so other agents can react
   (e.g. TrainerAgent can consume graded submissions as training data).

Context keys
------------
action : str
    One of ``"list_templates"``, ``"load_template"``, ``"grade"``,
    ``"assist"``, ``"task_guide"``.
template_name : str
    Name of the template to load (for ``load_template``).
submission : str
    Participant's code/answer text (for ``grade``).
rubric : str
    Grading criteria (for ``grade``).  Defaults to a general rubric.
question : str
    Free-text question (for ``assist``).
skill_level : str
    ``"beginner"`` | ``"intermediate"`` | ``"advanced"`` – personalises
    task guides and hints (default ``"intermediate"``).
topic : str
    Workshop topic for ``task_guide`` (e.g. ``"smart contracts"``).
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Built-in workshop templates
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, Any]] = {
    "intro-to-ai": {
        "title": "Introduction to AI & Machine Learning",
        "description": (
            "Hands-on workshop covering supervised learning, neural network "
            "fundamentals, and model evaluation using Python and scikit-learn."
        ),
        "modules": ["coding", "ai_experimentation"],
        "duration_hours": 3,
        "difficulty": "beginner",
        "prerequisites": ["Python basics"],
        "outline": [
            "1. What is AI? – concepts and terminology",
            "2. Data preparation and feature engineering",
            "3. Training your first classifier",
            "4. Evaluating and improving models",
            "5. Sandbox exercise: build a digit recogniser",
        ],
    },
    "blockchain-dev": {
        "title": "Blockchain Development with Solidity",
        "description": (
            "End-to-end workshop on writing, testing, and deploying Ethereum "
            "smart contracts using Hardhat and ethers.js."
        ),
        "modules": ["coding", "blockchain_dev"],
        "duration_hours": 4,
        "difficulty": "intermediate",
        "prerequisites": ["JavaScript", "Basic understanding of blockchain"],
        "outline": [
            "1. Ethereum architecture overview",
            "2. Solidity language fundamentals",
            "3. Writing an ERC-20 token contract",
            "4. Testing with Hardhat",
            "5. Deploying to a testnet via MetaMask",
        ],
    },
    "ai-fine-tuning": {
        "title": "Fine-Tuning LLMs for DevOps",
        "description": (
            "Advanced workshop on collecting training data from GitHub repos, "
            "fine-tuning OpenAI models, and deploying customised AI agents."
        ),
        "modules": ["ai_experimentation", "coding"],
        "duration_hours": 5,
        "difficulty": "advanced",
        "prerequisites": ["Python", "Basic ML knowledge", "GitHub API"],
        "outline": [
            "1. Training data collection and JSONL formatting",
            "2. OpenAI fine-tuning API walkthrough",
            "3. Evaluating fine-tuned vs base models",
            "4. Building a custom GitHub Copilot-style assistant",
            "5. Deploying to the Chatlippytm AI swarm",
        ],
    },
    "web3-ai-integration": {
        "title": "Web3 + AI Integration Workshop",
        "description": (
            "Build a decentralised AI application: combine wallet-based auth, "
            "tokenised learning incentives, and GPT-powered features."
        ),
        "modules": ["coding", "ai_experimentation", "blockchain_dev"],
        "duration_hours": 6,
        "difficulty": "advanced",
        "prerequisites": ["Solidity basics", "Python", "REST APIs"],
        "outline": [
            "1. Web3 authentication with MetaMask (EIP-191)",
            "2. Smart contracts for access control and token rewards",
            "3. Integrating OpenAI API into a dApp",
            "4. Building an AI task guide that adapts to user progress",
            "5. Deploying the full stack to IPFS + Vercel",
        ],
    },
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_GRADING_SYSTEM_PROMPT = """You are an expert AI workshop instructor.
Evaluate the participant's submission against the provided rubric.

Return a JSON object with the following structure:
{
  "score": <0-100 integer>,
  "grade": <"A"|"B"|"C"|"D"|"F">,
  "strengths": [<list of things done well>],
  "improvements": [<list of specific improvement suggestions>],
  "feedback": "<detailed narrative feedback>",
  "copilot_hint": "<one actionable GitHub Copilot-style code suggestion>"
}
"""

_ASSIST_SYSTEM_PROMPT = """You are an AI teaching assistant for Chatlippytm AI
Workshops, powered by GitHub Copilot-style intelligence.

Your capabilities:
- Provide context-aware code completions and explanations
- Debug code snippets with clear, educational explanations
- Answer conceptual questions about AI, machine learning, and blockchain
- Suggest best-practices and design patterns
- Guide participants through workshop exercises step by step

Always be encouraging and tailor your depth of explanation to the
participant's skill level.
"""

_TASK_GUIDE_SYSTEM_PROMPT = """You are a personalised AI learning guide for
Chatlippytm AI Workshops.

Generate a step-by-step task guide for the given topic and skill level.
The guide should:
1. Start with a brief motivation (why this matters)
2. List prerequisites the participant should already know
3. Provide 4-6 progressive tasks with clear acceptance criteria
4. Include a code skeleton or starter snippet for each task
5. Suggest 2-3 extension challenges for fast learners

Format the guide in Markdown.
"""


class WorkshopAgent(BaseAgent):
    """AI-powered agent for workshop automation and participant assistance."""

    name = "WorkshopAgent"
    description = (
        "Automates AI workshop lifecycle: templates, AI-graded assignments, "
        "real-time Copilot-style assistance, and personalised task guides"
    )

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        action = context.get("action", "")
        dispatch = {
            "list_templates": self._list_templates,
            "load_template": self._load_template,
            "grade": self._grade,
            "assist": self._assist,
            "task_guide": self._task_guide,
        }
        handler = dispatch.get(action)
        if handler is None:
            return self._base_result(
                "error",
                message=(
                    f"Unknown action '{action}'. "
                    "Valid actions: list_templates, load_template, "
                    "grade, assist, task_guide."
                ),
            )
        return handler(context)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _list_templates(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return a summary list of all available workshop templates."""
        summary = [
            {
                "name": name,
                "title": tmpl["title"],
                "difficulty": tmpl["difficulty"],
                "duration_hours": tmpl["duration_hours"],
                "modules": tmpl["modules"],
            }
            for name, tmpl in _TEMPLATES.items()
        ]
        return self._base_result(templates=summary, count=len(summary))

    def _load_template(self, context: dict[str, Any]) -> dict[str, Any]:
        """Load full details for a named workshop template."""
        name = context.get("template_name", "")
        if not name:
            return self._base_result("error", message="template_name is required")

        tmpl = _TEMPLATES.get(name)
        if tmpl is None:
            available = ", ".join(_TEMPLATES)
            return self._base_result(
                "error",
                message=f"Template '{name}' not found. Available: {available}",
            )

        return self._base_result(template_name=name, template=tmpl)

    def _grade(self, context: dict[str, Any]) -> dict[str, Any]:
        """Grade a participant's submission against a rubric."""
        submission = context.get("submission", "")
        if not submission:
            return self._base_result("error", message="submission is required")

        rubric = context.get(
            "rubric",
            "Correctness, code quality, clarity, best-practices adherence",
        )

        user_message = (
            f"Rubric: {rubric}\n\n"
            f"Submission:\n```\n{submission}\n```"
        )

        import json as _json

        raw = self.chat(_GRADING_SYSTEM_PROMPT, user_message)

        # Attempt to parse JSON; fall back to returning raw text
        try:
            grading = _json.loads(raw)
        except _json.JSONDecodeError:
            grading = {"raw_feedback": raw}

        return self._base_result(grading=grading)

    def _assist(self, context: dict[str, Any]) -> dict[str, Any]:
        """Answer a workshop question with Copilot-style assistance."""
        question = context.get("question", "")
        if not question:
            return self._base_result("error", message="question is required")

        skill_level = context.get("skill_level", "intermediate")
        system = (
            f"{_ASSIST_SYSTEM_PROMPT}\n\n"
            f"Participant skill level: {skill_level}"
        )
        answer = self.chat(system, question)
        return self._base_result(question=question, answer=answer)

    def _task_guide(self, context: dict[str, Any]) -> dict[str, Any]:
        """Generate a personalised task guide for a workshop topic."""
        topic = context.get("topic", "")
        if not topic:
            return self._base_result("error", message="topic is required")

        skill_level = context.get("skill_level", "intermediate")
        user_message = (
            f"Topic: {topic}\n"
            f"Skill level: {skill_level}"
        )
        guide = self.chat(_TASK_GUIDE_SYSTEM_PROMPT, user_message)
        return self._base_result(topic=topic, skill_level=skill_level, guide=guide)
