from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "config.yaml"

ALLOWED_STRATEGIES = {
    "embed_directly",
    "wrap_as_service",
    "fork_customize",
    "track_only",
}


@dataclass(frozen=True)
class JarvisCapability:
    id: str
    name: str
    category: str
    phase: str
    license: str
    maturity: str
    runtime_requirements: list[str]
    api_surface: str
    fit: str
    integration_strategy: str
    repo_role: str
    owner_repo: str
    enabled_by_default: bool
    source_url: str


@dataclass(frozen=True)
class JarvisTarget:
    repo: str
    role: str
    enabled_modules: list[str]
    planned_modules: list[str]
    phases: list[str]
    monetization_lane: str
    monetization_maturity: str
    venture_tags: list[str]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_registry_path(config_path: Path, registry_path: str) -> Path:
    raw_path = Path(registry_path)
    if raw_path.is_absolute():
        return raw_path
    return config_path.resolve().parent.parent / raw_path


def load_hub_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    config_file = Path(config_path)
    config_data = _load_yaml(config_file)
    jarvis_config = config_data.get("jarvis", {})
    registry_file = _resolve_registry_path(
        config_file,
        jarvis_config.get("registry_path", "config/jarvis_registry.yaml"),
    )
    registry_data = _load_yaml(registry_file)
    return {
        "config_path": str(config_file.resolve()),
        "registry_path": str(registry_file.resolve()),
        "config": config_data,
        "jarvis": jarvis_config,
        "registry": registry_data,
    }


def capabilities_from_registry(registry: dict[str, Any]) -> list[JarvisCapability]:
    capabilities: list[JarvisCapability] = []
    for raw in registry.get("capabilities", []):
        capabilities.append(
            JarvisCapability(
                id=raw["id"],
                name=raw["name"],
                category=raw["category"],
                phase=raw["phase"],
                license=raw["license"],
                maturity=raw["maturity"],
                runtime_requirements=list(raw.get("runtime_requirements", [])),
                api_surface=raw["api_surface"],
                fit=raw["fit"],
                integration_strategy=raw["integration_strategy"],
                repo_role=raw["repo_role"],
                owner_repo=raw["owner_repo"],
                enabled_by_default=bool(raw.get("enabled_by_default", False)),
                source_url=raw["source_url"],
            )
        )
    return capabilities


def targets_from_config(config: dict[str, Any]) -> list[JarvisTarget]:
    jarvis = config.get("jarvis", {})
    targets: list[JarvisTarget] = []
    for raw in jarvis.get("managed_targets", []):
        monetization = raw.get("monetization", {})
        targets.append(
            JarvisTarget(
                repo=raw["repo"],
                role=raw.get("role", "managed_assistant_repo"),
                enabled_modules=list(raw.get("enabled_modules", [])),
                planned_modules=list(raw.get("planned_modules", [])),
                phases=list(raw.get("phases", [])),
                monetization_lane=monetization.get("lane", "hub"),
                monetization_maturity=monetization.get("maturity", "prototype"),
                venture_tags=list(monetization.get("venture_tags", [])),
            )
        )
    return targets


def filter_capabilities(
    capabilities: list[JarvisCapability],
    *,
    category: str | None = None,
    phase: str | None = None,
    strategy: str | None = None,
) -> list[JarvisCapability]:
    filtered = capabilities
    if category:
        filtered = [cap for cap in filtered if cap.category == category]
    if phase:
        filtered = [cap for cap in filtered if cap.phase == phase]
    if strategy:
        filtered = [cap for cap in filtered if cap.integration_strategy == strategy]
    return filtered


def validate_hub_definition(hub_data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    config = hub_data["config"]
    jarvis = hub_data["jarvis"]
    registry = hub_data["registry"]
    policy = registry.get("policy", {})
    phases = set((registry.get("phases") or {}).keys())
    categories = set(policy.get("categories", []))
    allowed_licenses = set(policy.get("allowed_licenses", []))
    capability_ids: set[str] = set()

    if not jarvis.get("orchestration_hub"):
        errors.append("jarvis.orchestration_hub must be true.")
    if not jarvis.get("default_target_template"):
        errors.append("jarvis.default_target_template must be defined.")

    for target_repo in config.get("repositories", {}).get("targets", []):
        if not isinstance(target_repo, str) or "/" not in target_repo:
            errors.append(f"Invalid repository target: {target_repo!r}")

    for capability in capabilities_from_registry(registry):
        if capability.id in capability_ids:
            errors.append(f"Duplicate capability id: {capability.id}")
        capability_ids.add(capability.id)

        if capability.category not in categories:
            errors.append(
                f"Capability '{capability.id}' uses unknown category '{capability.category}'."
            )
        if capability.phase not in phases:
            errors.append(f"Capability '{capability.id}' uses unknown phase '{capability.phase}'.")
        if capability.license not in allowed_licenses:
            errors.append(
                f"Capability '{capability.id}' uses non-approved license '{capability.license}'."
            )
        if capability.integration_strategy not in ALLOWED_STRATEGIES:
            errors.append(
                f"Capability '{capability.id}' uses unsupported strategy '{capability.integration_strategy}'."
            )

    template = jarvis.get("default_target_template", {})
    template_enabled = sorted(set(template.get("enabled_modules", [])) - capability_ids)
    template_planned = sorted(set(template.get("planned_modules", [])) - capability_ids)
    if template_enabled:
        errors.append(
            f"jarvis.default_target_template references unknown enabled modules: {', '.join(template_enabled)}"
        )
    if template_planned:
        errors.append(
            f"jarvis.default_target_template references unknown planned modules: {', '.join(template_planned)}"
        )

    repository_targets = set(config.get("repositories", {}).get("targets", []))
    for target in targets_from_config(config):
        if target.repo not in repository_targets:
            errors.append(
                f"Managed target '{target.repo}' must also be listed in repositories.targets."
            )
        unknown_enabled = sorted(set(target.enabled_modules) - capability_ids)
        unknown_planned = sorted(set(target.planned_modules) - capability_ids)
        if unknown_enabled:
            errors.append(
                f"Managed target '{target.repo}' references unknown enabled modules: {', '.join(unknown_enabled)}"
            )
        if unknown_planned:
            errors.append(
                f"Managed target '{target.repo}' references unknown planned modules: {', '.join(unknown_planned)}"
            )
        if set(target.enabled_modules) & set(target.planned_modules):
            overlap = sorted(set(target.enabled_modules) & set(target.planned_modules))
            errors.append(
                f"Managed target '{target.repo}' overlaps enabled and planned modules: {', '.join(overlap)}"
            )
        if not target.monetization_lane:
            errors.append(f"Managed target '{target.repo}' must define monetization.lane.")
        if not target.monetization_maturity:
            errors.append(f"Managed target '{target.repo}' must define monetization.maturity.")

    return errors


def build_target_template(
    hub_data: dict[str, Any],
    repo: str,
    lane: str | None = None,
    maturity: str | None = None,
    venture_tags: list[str] | None = None,
) -> dict[str, Any]:
    template = dict(hub_data["jarvis"].get("default_target_template", {}))
    monetization = dict(template.get("monetization", {}))
    if lane:
        monetization["lane"] = lane
    if maturity:
        monetization["maturity"] = maturity
    if venture_tags is not None:
        monetization["venture_tags"] = venture_tags
    template["repo"] = repo
    template["monetization"] = monetization
    return template


def build_target_plan(
    hub_data: dict[str, Any],
    repo: str,
    phase: str | None = None,
    use_template: bool = False,
    lane: str | None = None,
    maturity: str | None = None,
    venture_tags: list[str] | None = None,
) -> dict[str, Any]:
    registry = hub_data["registry"]
    capabilities = {cap.id: cap for cap in capabilities_from_registry(registry)}
    target = next((item for item in targets_from_config(hub_data["config"]) if item.repo == repo), None)
    if target is None:
        if not use_template:
            raise ValueError(f"Managed target not found: {repo}")
        template = build_target_template(
            hub_data,
            repo=repo,
            lane=lane,
            maturity=maturity,
            venture_tags=venture_tags,
        )
        template_monetization = template.get("monetization", {})
        target = JarvisTarget(
            repo=template["repo"],
            role=template.get("role", "managed_assistant_repo"),
            enabled_modules=list(template.get("enabled_modules", [])),
            planned_modules=list(template.get("planned_modules", [])),
            phases=list(template.get("phases", [])),
            monetization_lane=template_monetization.get("lane", "hub"),
            monetization_maturity=template_monetization.get("maturity", "prototype"),
            venture_tags=list(template_monetization.get("venture_tags", [])),
        )

    def _serialize(ids: list[str]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for capability_id in ids:
            capability = capabilities[capability_id]
            if phase and capability.phase != phase:
                continue
            selected.append(
                {
                    "id": capability.id,
                    "name": capability.name,
                    "category": capability.category,
                    "phase": capability.phase,
                    "license": capability.license,
                    "integration_strategy": capability.integration_strategy,
                    "repo_role": capability.repo_role,
                    "owner_repo": capability.owner_repo,
                }
            )
        return selected

    enabled = _serialize(target.enabled_modules)
    planned = _serialize(target.planned_modules)
    covered_categories = sorted({item["category"] for item in enabled + planned})
    all_categories = sorted(hub_data["registry"].get("policy", {}).get("categories", []))

    return {
        "repo": target.repo,
        "role": target.role,
        "phase_filter": phase,
        "phases": target.phases,
        "monetization": {
            "lane": target.monetization_lane,
            "maturity": target.monetization_maturity,
            "venture_tags": target.venture_tags,
        },
        "enabled_modules": enabled,
        "planned_modules": planned,
        "covered_categories": covered_categories,
        "missing_categories": [category for category in all_categories if category not in covered_categories],
    }
