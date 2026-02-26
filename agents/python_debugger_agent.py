"""
PythonDebuggerAgent – AI-powered Python debugging development toolkit.

Analyses Python code, tracebacks, and test failures to identify root causes,
suggest targeted fixes, and surface best-practice recommendations.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert Python debugger and developer for the
Chatlippytm AI DevOps platform. Your job is to analyse Python code, error
tracebacks, and failing test output to identify the root cause of issues and
suggest concrete fixes.

For each problem provided, you must:
1. Identify the root cause with a clear explanation
2. Pinpoint the exact file(s) and line(s) responsible where possible
3. Provide a corrected code snippet or diff
4. List any secondary issues or code smells discovered during analysis
5. Recommend preventive measures (tests, type hints, linting rules)

Format your response as structured Markdown.
"""


class PythonDebuggerAgent(BaseAgent):
    """AI-powered Python debugging and development toolkit."""

    name = "PythonDebuggerAgent"
    description = "AI Python Debugging Development toolkit – root-cause analysis and fix suggestions"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Parameters in ``context``
        -------------------------
        repo : str
            Full repo name, e.g. ``lippytm/Chatlippytm.ai.Bots``.
        traceback : str
            Python exception traceback text.
        code_snippet : str, optional
            Relevant source code surrounding the error.
        test_output : str, optional
            Output from a failing test run (pytest, unittest, etc.).
        description : str, optional
            Free-text description of the unexpected behaviour.
        """
        repo = context.get("repo", "unknown/repo")
        traceback = context.get("traceback", "")
        code_snippet = context.get("code_snippet", "")
        test_output = context.get("test_output", "")
        description = context.get("description", "")

        if not any([traceback, code_snippet, test_output, description]):
            return self._base_result(
                "error",
                message="No debugging context provided (traceback, code_snippet, test_output, or description required)",
            )

        logger.info("[%s] Debugging Python issue in %s …", self.name, repo)

        parts: list[str] = [f"Repository: {repo}"]
        if description:
            parts.append(f"Description:\n{description[:1000]}")
        if traceback:
            parts.append(f"Traceback:\n```\n{traceback[:4000]}\n```")
        if code_snippet:
            parts.append(f"Code snippet:\n```python\n{code_snippet[:4000]}\n```")
        if test_output:
            parts.append(f"Test output:\n```\n{test_output[:3000]}\n```")

        user_message = "\n\n".join(parts)

        analysis = self.chat(_SYSTEM_PROMPT, user_message)

        return self._base_result(
            repo=repo,
            analysis=analysis,
        )
