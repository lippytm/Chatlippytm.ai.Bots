"""
Chatlippytm.ai.Bots – Swarm Orchestration Package

The swarm layer coordinates multiple AI agents running concurrently across
one or more repositories, collecting results and aggregating them into a
unified status report.
"""

from .swarm import Swarm
from .task import SwarmTask, TaskStatus

__all__ = ["Swarm", "SwarmTask", "TaskStatus"]
