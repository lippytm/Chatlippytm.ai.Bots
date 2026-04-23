from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from agents.base_agent import BaseAgent


@dataclass
class MonetizationTask:
    repo: str
    lane: str
    capabilities: List[str]
    maturity: str = "prototype"


class MonetizationAgent(BaseAgent):
    name = "MonetizationAgent"
    role = "monetization"

    def recommend_models(self, task: MonetizationTask) -> List[str]:
        lane = task.lane
        if lane == "revenue":
            return ["service packages", "strategy sessions", "lead-generation offers", "retainers"]
        if lane == "commerce":
            return ["subscriptions", "usage-based billing", "token-gated access", "affiliate programs"]
        if lane == "product":
            return ["SaaS tiers", "white-label licensing", "managed deployment", "premium support"]
        if lane == "knowledge":
            return ["ebooks", "courses", "member libraries", "media bundles"]
        if lane == "hub":
            return ["platform enablement value", "consulting leverage", "fleet acceleration"]
        return ["experimental value mapping", "future packaging analysis"]

    def evaluate_value_role(self, task: MonetizationTask) -> str:
        if task.lane in {"revenue", "commerce"}:
            return "direct"
        if task.lane in {"hub", "control", "swarm"}:
            return "platform"
        if task.lane == "product":
            return "supporting"
        return "experimental"

    def run(self, repo: str, lane: str, capabilities: List[str], maturity: str = "prototype") -> Dict[str, object]:
        task = MonetizationTask(repo=repo, lane=lane, capabilities=capabilities, maturity=maturity)
        value_role = self.evaluate_value_role(task)
        models = self.recommend_models(task)
        next_actions = [
            "document repo monetization role",
            "map capabilities to offers",
            "define value ladder based on maturity",
        ]
        return {
            "agent": self.name,
            "repo": repo,
            "lane": lane,
            "maturity": maturity,
            "value_role": value_role,
            "recommended_models": models,
            "capabilities": capabilities,
            "next_actions": next_actions,
            "status": "completed",
        }
