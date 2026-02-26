"""
SwarmTask – data class that wraps a single unit of work dispatched to an agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class SwarmTask:
    """Represents one agent task within a swarm run."""

    agent_name: str
    context: dict[str, Any]
    task_id: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def mark_running(self) -> None:
        self.status = TaskStatus.RUNNING

    def mark_done(self, result: dict[str, Any]) -> None:
        self.status = TaskStatus.DONE
        self.result = result

    def mark_error(self, error: str) -> None:
        self.status = TaskStatus.ERROR
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent": self.agent_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
        }
