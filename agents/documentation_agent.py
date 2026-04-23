from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from agents.base_agent import BaseAgent


@dataclass
class DocumentationTask:
    repo: str
    changed_paths: List[str]
    objective: str = "Improve repository documentation quality"


class DocumentationAgent(BaseAgent):
    name = "DocumentationAgent"
    role = "knowledge"

    def build_plan(self, task: DocumentationTask) -> Dict[str, object]:
        priorities = [
            "README.md",
            "ARCHITECTURE.md",
            "OPERATIONS.md",
            "docs/workflows/",
            "docs/integrations/",
        ]
        return {
            "repo": task.repo,
            "objective": task.objective,
            "changed_paths": task.changed_paths,
            "priority_targets": priorities,
            "expected_outputs": [
                "documentation summary",
                "suggested file updates",
                "gap list",
            ],
        }

    def summarize_gaps(self, task: DocumentationTask) -> List[str]:
        gaps = []
        paths = set(task.changed_paths)
        if not any(path.endswith("README.md") for path in paths):
            gaps.append("README was not part of the changed paths review.")
        if not any("docs/" in path for path in paths):
            gaps.append("No docs folder changes detected; documentation drift may exist.")
        if not any("workflow" in path.lower() for path in paths):
            gaps.append("Workflow behavior may have changed without matching runbook updates.")
        return gaps

    def run(self, repo: str, changed_paths: List[str]) -> Dict[str, object]:
        task = DocumentationTask(repo=repo, changed_paths=changed_paths)
        plan = self.build_plan(task)
        gaps = self.summarize_gaps(task)
        return {
            "agent": self.name,
            "repo": repo,
            "plan": plan,
            "gaps": gaps,
            "status": "completed",
        }
