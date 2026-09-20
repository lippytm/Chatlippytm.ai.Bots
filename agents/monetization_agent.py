from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

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
    description = "Maps assistant capabilities to monetization lanes and offers."

    def __init__(self, verbose: bool = False) -> None:
        self.model = "rules"
        self.temperature = 0.0
        self.max_tokens = 0
        self.verbose = verbose
        self._conversation: list[dict[str, str]] = []
        logging.basicConfig(
            level=logging.DEBUG if self.verbose else logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )

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

    def run(self, context: dict[str, Any]) -> Dict[str, object]:
        repo = str(context.get("repo", "")).strip()
        lane = str(context.get("lane", "hub")).strip() or "hub"
        maturity = str(context.get("maturity", "prototype")).strip() or "prototype"
        capabilities = [str(item) for item in context.get("capabilities", [])]
        venture_tags = [str(item) for item in context.get("venture_tags", [])]

        if not repo:
            return self._base_result(status="error", message="Missing repo for monetization task.")

        task = MonetizationTask(
            repo=repo,
            lane=lane,
            capabilities=capabilities,
            maturity=maturity,
        )
        value_role = self.evaluate_value_role(task)
        models = self.recommend_models(task)
        next_actions = [
            "document repo monetization role",
            "map capabilities to offers",
            "define value ladder based on maturity",
        ]
        if venture_tags:
            next_actions.append("align ventures to shared services and packaging")
        return self._base_result(
            repo=repo,
            lane=lane,
            maturity=maturity,
            value_role=value_role,
            recommended_models=models,
            capabilities=capabilities,
            venture_tags=venture_tags,
            next_actions=next_actions,
        )
