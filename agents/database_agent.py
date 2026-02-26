"""
DatabaseAgent – autonomous AI database management agent.

Manages database systems, automates optimisations, handles schema migrations,
and performs autonomous scaling decisions.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert AI database administrator for the Chatlippytm
AI DevOps platform.

Given a database context (schema description, query logs, performance metrics,
and configuration), produce a JSON object (no markdown fences) with exactly
these keys:

{
  "db_type": "<database type, e.g. PostgreSQL, MongoDB, Redis>",
  "health_score": <int 0–100>,
  "optimisations": [
    {
      "type": "index" | "query" | "schema" | "config" | "scaling",
      "description": "<what to optimise>",
      "impact": "high" | "medium" | "low",
      "sql_or_command": "<SQL statement or CLI command if applicable>"
    }
  ],
  "scaling_recommendation": {
    "action": "scale_up" | "scale_out" | "scale_down" | "no_change",
    "rationale": "<reason>",
    "suggested_config": "<new configuration hint>"
  },
  "anomalies": ["<detected anomaly>", ...],
  "maintenance_tasks": ["<task description>", ...],
  "summary": "<overall database health summary>"
}
"""


class DatabaseAgent(BaseAgent):
    """Autonomously manages, optimises, and scales database systems."""

    name = "DatabaseAgent"
    description = "Autonomous DB manager – optimisation, scaling, and anomaly detection"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        db_type : str
            Database type (e.g. ``PostgreSQL``, ``MongoDB``, ``Redis``).
        schema : str, optional
            Schema definition or data model description.
        query_logs : str, optional
            Sample of recent slow or problematic queries.
        metrics : str, optional
            Performance metrics (CPU, memory, IOPS, connection count, etc.).
        config : str, optional
            Current database configuration snippet.
        """
        db_type = context.get("db_type", "")
        if not db_type:
            return self._base_result("error", message="No database type provided")

        schema = context.get("schema", "")
        query_logs = context.get("query_logs", "")
        metrics = context.get("metrics", "")
        config = context.get("config", "")

        if not any([schema, query_logs, metrics, config]):
            return self._base_result(
                "error",
                message="No database context provided (need at least one of: "
                        "schema, query_logs, metrics, config)",
            )

        logger.info("[%s] Analysing %s database …", self.name, db_type)

        parts: list[str] = [f"Database type: {db_type}\n"]
        if schema:
            parts.append(f"Schema:\n{schema[:2000]}")
        if query_logs:
            parts.append(f"Query logs:\n{query_logs[:2000]}")
        if metrics:
            parts.append(f"Performance metrics:\n{metrics[:1000]}")
        if config:
            parts.append(f"Configuration:\n{config[:1000]}")

        user_message = "\n\n".join(parts)
        raw = self.chat(_SYSTEM_PROMPT, user_message)

        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            report = json.loads(match.group()) if match else {"raw": raw}

        return self._base_result(
            db_type=db_type,
            db_report=report,
        )
