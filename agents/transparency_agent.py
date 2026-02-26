"""
TransparencyAgent – AI Full Stack Transparency toolkit.

Provides explainability and transparency for AI-driven decisions, model
outputs, and automated actions taken by the Chatlippytm swarm. Produces
human-readable explanations, confidence assessments, and audit trails to
make AI behaviour auditable and understandable.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an AI transparency and explainability expert for
the Chatlippytm AI DevOps platform. Your role is to make AI-driven decisions
and automated actions understandable, auditable, and trustworthy for human
reviewers.

Given an AI decision, recommendation, or automated action along with its
supporting context, produce a transparency report that includes:

1. Plain-language explanation of what the AI decided or recommended and why
2. Key factors and evidence that most influenced the decision (feature
   importance / reasoning chain)
3. Confidence level (HIGH / MEDIUM / LOW) with justification
4. Known limitations or blind spots in the analysis
5. Alternative interpretations that were considered and why they were ranked
   lower
6. Audit trail: data sources used, assumptions made, any data gaps
7. Recommended human review checkpoints before acting on the AI output

Format your response as structured Markdown suitable for inclusion in an audit
log or pull-request comment.
"""


class TransparencyAgent(BaseAgent):
    """Generates explainability and transparency reports for AI decisions."""

    name = "TransparencyAgent"
    description = "AI Full Stack Transparency toolkit – explainability and audit trail generation"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        decision : str
            The AI decision, recommendation, or automated action to explain.
        supporting_context : str, optional
            Raw data, diffs, logs, or metrics that informed the decision.
        agent_name : str, optional
            Name of the agent that produced the decision being explained.
        confidence : str, optional
            Raw confidence score or label provided by the source agent.
        """
        repo = context.get("repo", "unknown/repo")
        decision = context.get("decision", "")
        supporting_context = context.get("supporting_context", "")
        agent_name = context.get("agent_name", "unknown agent")
        confidence = context.get("confidence", "")

        if not decision:
            return self._base_result(
                "error",
                message="No decision provided – 'decision' field is required",
            )

        logger.info(
            "[%s] Generating transparency report for decision by %s in %s …",
            self.name,
            agent_name,
            repo,
        )

        parts: list[str] = [
            f"Repository: {repo}",
            f"Originating agent: {agent_name}",
        ]
        if confidence:
            parts.append(f"Reported confidence: {confidence}")
        parts.append(f"Decision / recommendation:\n{decision[:4000]}")
        if supporting_context:
            parts.append(
                f"Supporting context:\n```\n{supporting_context[:4000]}\n```"
            )

        user_message = "\n\n".join(parts)

        explanation = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo,
            agent_name=agent_name,
            explanation=explanation,
        )
