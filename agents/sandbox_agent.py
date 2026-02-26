"""
SandboxAgent – manages dynamic, isolated sandbox environments for workshop
participants to train, debug, and test AI systems and blockchain contracts.

Each sandbox is represented by a lightweight descriptor that tracks:
- participant wallet address (Web3 identity)
- available modules: ``coding``, ``ai_experimentation``, ``blockchain_dev``
- resource limits and current status

In a real deployment the agent would call out to a container orchestrator
(Docker / Kubernetes) or a cloud sandbox API.  Here all operations are
simulated in-process so the module can run and be tested without external
infrastructure.
"""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sandbox descriptor
# ---------------------------------------------------------------------------

_VALID_MODULES = frozenset({"coding", "ai_experimentation", "blockchain_dev"})
_DEFAULT_MODULES = ["coding", "ai_experimentation", "blockchain_dev"]


@dataclass
class SandboxEnvironment:
    """Descriptor for a single workshop sandbox instance."""

    sandbox_id: str
    owner_address: str
    modules: list[str]
    status: str = "provisioning"  # provisioning | running | stopped | error
    cpu_limit: float = 1.0        # fractional CPU cores
    memory_mb: int = 512
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "owner_address": self.owner_address,
            "modules": self.modules,
            "status": self.status,
            "cpu_limit": self.cpu_limit,
            "memory_mb": self.memory_mb,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# SandboxAgent
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an AI assistant embedded inside a secure sandbox
environment for an AI workshop platform.

Your role:
1. Help participants understand and experiment with AI/ML concepts.
2. Provide context-aware code suggestions (similar to GitHub Copilot) for
   Python, JavaScript, Solidity, and other languages.
3. Debug errors in participant code snippets with step-by-step explanations.
4. Guide blockchain development tasks: smart-contract patterns, gas
   optimisation, and security best-practices.
5. Explain AI model architectures and training strategies at the requested
   level of detail (beginner / intermediate / advanced).

Always respond with clear, runnable code examples where appropriate.
"""


class SandboxAgent(BaseAgent):
    """Provisions and assists inside isolated workshop sandbox environments.

    Responsibilities
    ----------------
    - **Provision** a new sandbox for a wallet-authenticated participant.
    - **Terminate** a sandbox when the session ends.
    - **Assist** inside an active sandbox: answer coding questions, debug
      code, and suggest improvements using the configured AI model.

    Context keys
    ------------
    action : str
        One of ``"provision"``, ``"terminate"``, ``"assist"``.
    owner_address : str
        Wallet address of the participant (required for provision/terminate).
    sandbox_id : str
        ID of an existing sandbox (required for terminate/assist).
    modules : list[str], optional
        Subset of ``["coding", "ai_experimentation", "blockchain_dev"]``
        to enable.  Defaults to all three.
    question : str
        Free-text question or code snippet (required for assist).
    skill_level : str, optional
        ``"beginner"``, ``"intermediate"``, or ``"advanced"`` – tailors
        the AI response depth (default ``"intermediate"``).
    """

    name = "SandboxAgent"
    description = (
        "Provisions isolated AI/blockchain sandbox environments and provides "
        "context-aware coding assistance inside them"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # In-process sandbox registry (replace with DB/cache in production)
        self._sandboxes: dict[str, SandboxEnvironment] = {}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        action = context.get("action", "")
        dispatch = {
            "provision": self._provision,
            "terminate": self._terminate,
            "assist": self._assist,
        }
        handler = dispatch.get(action)
        if handler is None:
            return self._base_result(
                "error",
                message=(
                    f"Unknown action '{action}'. "
                    "Valid actions: provision, terminate, assist."
                ),
            )
        return handler(context)

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _provision(self, context: dict[str, Any]) -> dict[str, Any]:
        """Provision a new sandbox for a workshop participant."""
        owner = context.get("owner_address", "").lower()
        if not owner:
            return self._base_result("error", message="owner_address is required")

        raw_modules = context.get("modules", _DEFAULT_MODULES)
        modules = [m for m in raw_modules if m in _VALID_MODULES]
        if not modules:
            modules = _DEFAULT_MODULES

        sandbox_id = context.get("sandbox_id") or str(uuid.uuid4())[:12]
        env = SandboxEnvironment(
            sandbox_id=sandbox_id,
            owner_address=owner,
            modules=modules,
            status="running",
            cpu_limit=float(os.getenv("SANDBOX_CPU_LIMIT", "1.0")),
            memory_mb=int(os.getenv("SANDBOX_MEMORY_MB", "512")),
        )
        self._sandboxes[sandbox_id] = env

        logger.info(
            "[SandboxAgent] Provisioned sandbox %s for %s (modules=%s)",
            sandbox_id, owner, modules,
        )
        return self._base_result(
            sandbox=env.to_dict(),
            message=f"Sandbox {sandbox_id} provisioned successfully",
        )

    def _terminate(self, context: dict[str, Any]) -> dict[str, Any]:
        """Terminate an existing sandbox."""
        sandbox_id = context.get("sandbox_id", "")
        if not sandbox_id:
            return self._base_result("error", message="sandbox_id is required")

        env = self._sandboxes.get(sandbox_id)
        if env is None:
            return self._base_result(
                "error", message=f"Sandbox '{sandbox_id}' not found"
            )

        env.status = "stopped"
        del self._sandboxes[sandbox_id]
        logger.info("[SandboxAgent] Sandbox %s terminated", sandbox_id)
        return self._base_result(
            sandbox_id=sandbox_id,
            message=f"Sandbox {sandbox_id} terminated",
        )

    def _assist(self, context: dict[str, Any]) -> dict[str, Any]:
        """Answer a coding/AI/blockchain question inside a sandbox."""
        question = context.get("question", "")
        if not question:
            return self._base_result("error", message="question is required for assist")

        skill_level = context.get("skill_level", "intermediate")
        sandbox_id = context.get("sandbox_id", "unknown")

        system = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"Current sandbox: {sandbox_id}\n"
            f"Participant skill level: {skill_level}"
        )
        answer = self.chat(system, question)

        return self._base_result(
            sandbox_id=sandbox_id,
            question=question,
            answer=answer,
        )

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def list_sandboxes(self) -> list[dict[str, Any]]:
        """Return descriptors for all currently running sandboxes."""
        return [env.to_dict() for env in self._sandboxes.values()]

    def get_sandbox(self, sandbox_id: str) -> SandboxEnvironment | None:
        """Look up a sandbox by ID."""
        return self._sandboxes.get(sandbox_id)
