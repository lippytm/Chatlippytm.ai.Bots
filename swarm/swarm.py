"""
Swarm – orchestrator that spawns and manages a pool of AI agents running
concurrently across repositories.

Usage
-----
::

    from swarm import Swarm
    from agents import CodeReviewAgent, SecurityAgent

    swarm = Swarm(max_workers=4)
    swarm.register(CodeReviewAgent())
    swarm.register(SecurityAgent())

    results = swarm.run_all(repos=["lippytm/Chatlippytm.ai.Bots"])
"""

from __future__ import annotations

import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from agents.base_agent import BaseAgent
from .task import SwarmTask, TaskStatus

logger = logging.getLogger(__name__)


class Swarm:
    """Orchestrates multiple AI agents across one or more repositories."""

    def __init__(self, max_workers: int | None = None) -> None:
        self.max_workers = max_workers or int(os.getenv("SWARM_CONCURRENCY", "4"))
        self._agents: dict[str, BaseAgent] = {}

    # ------------------------------------------------------------------
    # Agent registry
    # ------------------------------------------------------------------

    def register(self, agent: BaseAgent) -> None:
        """Register an agent with the swarm."""
        self._agents[agent.name] = agent
        logger.info("[Swarm] Registered agent: %s", agent.name)

    def unregister(self, agent_name: str) -> None:
        """Remove a registered agent."""
        self._agents.pop(agent_name, None)

    @property
    def agents(self) -> list[BaseAgent]:
        return list(self._agents.values())

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_all(
        self,
        repos: list[str],
        extra_context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Run every registered agent against every repo concurrently.

        Parameters
        ----------
        repos:
            List of ``owner/repo`` strings.
        extra_context:
            Additional key-value pairs merged into each task's context.

        Returns
        -------
        list of result dicts, one per (agent, repo) pair.
        """
        if not self._agents:
            logger.warning("[Swarm] No agents registered – nothing to do.")
            return []

        tasks: list[SwarmTask] = []
        for repo in repos:
            for agent in self._agents.values():
                ctx = {"repo": repo, **(extra_context or {})}
                task = SwarmTask(
                    agent_name=agent.name,
                    context=ctx,
                    task_id=str(uuid.uuid4())[:8],
                )
                tasks.append(task)

        logger.info(
            "[Swarm] Dispatching %d tasks across %d workers …",
            len(tasks),
            self.max_workers,
        )

        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_to_task = {
                pool.submit(self._execute_task, task): task for task in tasks
            }
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    outcome = future.result()
                    task.mark_done(outcome)
                except Exception as exc:  # noqa: BLE001
                    task.mark_error(str(exc))
                    logger.error("[Swarm] Task %s failed: %s", task.task_id, exc)
                results.append(task.to_dict())

        self._log_summary(results)
        return results

    def run_agent(
        self,
        agent_name: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a single named agent with the provided context."""
        agent = self._agents.get(agent_name)
        if agent is None:
            return {"status": "error", "message": f"Agent '{agent_name}' not registered"}
        task = SwarmTask(
            agent_name=agent_name,
            context=context,
            task_id=str(uuid.uuid4())[:8],
        )
        try:
            result = self._execute_task(task)
            task.mark_done(result)
        except Exception as exc:  # noqa: BLE001
            task.mark_error(str(exc))
        return task.to_dict()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _execute_task(self, task: SwarmTask) -> dict[str, Any]:
        agent = self._agents[task.agent_name]
        task.mark_running()
        logger.debug(
            "[Swarm] Running %s | task=%s | repo=%s",
            task.agent_name,
            task.task_id,
            task.context.get("repo", "?"),
        )
        return agent.run(task.context)

    @staticmethod
    def _log_summary(results: list[dict[str, Any]]) -> None:
        ok = sum(1 for r in results if r.get("status") == "ok")
        errors = sum(1 for r in results if r.get("status") == "error")
        warnings = len(results) - ok - errors
        logger.info(
            "[Swarm] Completed – ok=%d  warnings=%d  errors=%d",
            ok,
            warnings,
            errors,
        )
