# Cross-Repo Operations

This document defines how `Chatlippytm.ai.Bots` should operate across multiple repositories in the lippytm ecosystem.

## Goal

Turn specialist DevOps-style agents into a coordinated improvement system for documentation, quality, security, monetization, and repo readiness.

---

## Primary Use Cases

- documentation improvement across many repos
- repo health scans across product and lab lanes
- monetization role mapping for active repos
- issue triage and classification
- architecture drift detection

---

## Operating Principles

- follow BrainKit role and folder standards
- respect lane boundaries
- treat hub, control, and commerce repos as higher-sensitivity targets
- prefer proposals and reports before high-impact code changes
- preserve a record of what changed and why

---

## Suggested Workflow

1. read repo role and lane
2. classify risk level
3. run specialist agent in the correct sequence
4. generate findings or proposed changes
5. apply only low-risk changes automatically
6. escalate policy-sensitive actions to control layer or operator review

---

## Suggested Agent Order

1. RepoScannerAgent
2. DocumentationAgent
3. MonetizationAgent
4. SecurityAgent
5. ReleaseAgent or operator review path

---

## Best Practices

- do not treat all repos the same
- separate lab experimentation from commercial optimization
- keep creative mythos repos from being forced into narrow sales language
- keep customer-facing repos clearer and more conversion-focused
- use cross-repo operations to raise the quality floor, not erase diversity

---

## Rule of thumb

Cross-repo automation should create consistency in structure and quality while still allowing each lane to preserve its own role, tone, and product logic.
