# AI Jarvis Capability Matrix

## Purpose

This repository is the orchestration hub for Jarvis-style assistant capabilities across the `lippytm` assistant repositories. It does not vendor third-party projects into the codebase. Instead, it approves, categorises, enables, and plans how open-source capabilities are rolled out.

## Definition of "AI Jarvis free and open source"

A capability qualifies only when it:

- has a clear approved open-source license
- fits one of the assistant categories used by this repo
- adds distinct value beyond the repo's existing orchestration, training, security, or workflow features
- can be embedded directly, wrapped as a service, forked/customised, or tracked for later adoption

The current allowed licenses and exclusion rules are maintained in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/config/jarvis_registry.yaml`.

## Rollout phases

| Phase | Goal |
| --- | --- |
| phase_1 | Core assistant capabilities aligned to Jarvis-style workflows |
| phase_2 | Tool-use and workflow automation |
| phase_3 | Optional voice, local model, and device integrations |
| phase_4 | Cross-repository rollout and governance |

## Canonical capability matrix

| Capability | Category | License | Phase | Strategy | Repo role | Owner repo | Current state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LangChain | agents | MIT | phase_1 | embed_directly | shared_orchestration | `lippytm/Chatlippytm.ai.Bots` | enabled |
| Chroma | memory | Apache-2.0 | phase_1 | wrap_as_service | shared_memory | `lippytm/Chatlippytm.ai.Bots` | enabled |
| FastAPI | integrations | MIT | phase_1 | embed_directly | integration_gateway | `lippytm/Chatlippytm.ai.Bots` | enabled |
| Haystack | agents | Apache-2.0 | phase_2 | track_only | optional_agent_runtime | `lippytm/Chatlippytm.ai.Bots` | planned |
| Node-RED | automation | Apache-2.0 | phase_2 | wrap_as_service | automation_runtime | `lippytm/Chatlippytm.ai.Bots` | planned |
| Open WebUI | ui | BSD-3-Clause | phase_2 | wrap_as_service | assistant_ui | `lippytm/Chatlippytm.ai.Bots` | planned |
| whisper.cpp | voice | MIT | phase_3 | wrap_as_service | voice_ingest | `lippytm/Chatlippytm.ai.Bots` | planned |
| Ollama | local_models | MIT | phase_3 | wrap_as_service | local_model_runtime | `lippytm/Chatlippytm.ai.Bots` | enabled |
| Home Assistant | home_device_control | Apache-2.0 | phase_3 | wrap_as_service | device_control_runtime | `lippytm/Chatlippytm.ai.Bots` | planned |

## Repo ownership model

- `Chatlippytm.ai.Bots` owns orchestration policy, validation, rollout planning, and swarm integration.
- Managed assistant repositories must be listed in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/config/config.yaml` under `repositories.targets`.
- Per-repo module enablement lives under `jarvis.managed_targets` in the same config file.
- The shared multi-repo starter profile lives under `jarvis.default_target_template` so any repo can inherit the same approved module stack.
- Monetization metadata lives with each target so business lanes, venture tags, and maturity can be reused across all ventures.
- The registry of approved capabilities lives in `/home/runner/work/Chatlippytm.ai.Bots/Chatlippytm.ai.Bots/config/jarvis_registry.yaml`.

## Multi-repo monetization workflow

Use the shared template when bringing Jarvis capabilities into a new repo:

1. Generate a target entry with `python main.py jarvis bootstrap-target --repo owner/repo --lane commerce`.
2. Add the repo to `repositories.targets` and paste the generated target into `jarvis.managed_targets`.
3. Run `python main.py jarvis plan --repo owner/repo` to confirm the enabled and planned module stack.
4. Run `python main.py jarvis monetize --repo owner/repo` to map the selected capabilities into monetization models for that venture.
5. Promote the repo through phases as its business maturity increases.

## CLI and workflow entry points

Use the orchestration hub to inspect or validate the matrix:

```bash
python main.py jarvis policy
python main.py jarvis inventory
python main.py jarvis targets
python main.py jarvis plan --repo lippytm/Chatlippytm.ai.Bots
python main.py jarvis bootstrap-target --repo lippytm/venture-repo --lane product --venture-tag white-label
python main.py jarvis monetize --repo lippytm/venture-repo --use-template --lane commerce
python main.py jarvis validate
```

The `Jarvis Capability Registry` GitHub Actions workflow runs the validation and inventory commands for the managed registry.
