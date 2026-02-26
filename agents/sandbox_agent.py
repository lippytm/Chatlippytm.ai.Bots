"""
SandboxAgent – manages isolated sandbox environments for self-learning,
safe experimentation, and reinforcement-learning training runs.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an AI sandbox environment manager for the Chatlippytm
AI DevOps platform.

Given a sandbox task description (experiment configuration, RL training objective,
or simulation parameters), produce a JSON object (no markdown fences) with exactly
these keys:

{
  "sandbox_id": "<unique identifier for this sandbox session>",
  "experiment_type": "rl_training" | "simulation" | "diagnostics" | "api_test",
  "environment_config": {
    "isolation_level": "strict" | "standard" | "permissive",
    "resource_limits": {"cpu_cores": <int>, "memory_mb": <int>, "timeout_s": <int>},
    "allowed_actions": ["<action>", ...]
  },
  "training_plan": {
    "algorithm": "<RL algorithm or N/A>",
    "episodes": <int>,
    "learning_rate": <float>,
    "reward_function": "<description>"
  },
  "safety_checks": ["<check description>", ...],
  "expected_outcomes": ["<outcome>", ...],
  "status": "ready" | "running" | "completed" | "failed"
}
"""


class SandboxAgent(BaseAgent):
    """Manages sandbox environments for self-learning and safe experimentation."""

    name = "SandboxAgent"
    description = "Sandbox environment manager – RL training, simulation, and safe experimentation"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        experiment : str
            Description of the experiment or RL task to run in the sandbox.
        experiment_type : str, optional
            One of ``rl_training``, ``simulation``, ``diagnostics``, ``api_test``.
            Defaults to ``simulation``.
        resource_limits : dict, optional
            Override default resource limits, e.g.
            ``{"cpu_cores": 2, "memory_mb": 512, "timeout_s": 300}``.
        real_world_data : str, optional
            Real-world data samples to use for training alongside simulated tasks.
        """
        experiment = context.get("experiment", "")
        if not experiment:
            return self._base_result("error", message="No experiment description provided")

        experiment_type = context.get("experiment_type", "simulation")
        resource_limits = context.get("resource_limits", {})
        real_world_data = context.get("real_world_data", "")

        logger.info(
            "[%s] Configuring sandbox for '%s' (type=%s) …",
            self.name,
            experiment[:60],
            experiment_type,
        )

        user_message = (
            f"Experiment type  : {experiment_type}\n"
            f"Experiment       : {experiment[:3000]}\n"
        )
        if resource_limits:
            user_message += f"Resource limits  : {json.dumps(resource_limits)}\n"
        if real_world_data:
            user_message += f"\nReal-world data sample:\n{real_world_data[:2000]}\n"

        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            config = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            config = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            experiment=experiment[:120],
            experiment_type=experiment_type,
            sandbox_config=config,
        )
