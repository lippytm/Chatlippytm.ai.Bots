# Prompt #11 Auto Training Review Plan

This file applies only to:

`lippytm/Chatlippytm.ai.Bots`

## Purpose

Chatlippytm.ai.Bots should support an AI auto-training workflow that learns from reviewed GitHub evidence and improves future documentation, code review, issue triage, repo health reporting, and computer-language support.

## Operating Boundary

AI proposes. RiskGate reviews. Human owner approves. QA verifies. Evidence is documented.

## Approved Evidence Sources

Potential training evidence can include:

- closed issues
- merged pull request discussions
- approved review comments
- workflow failure summaries
- test failure summaries
- repo health reports
- approved documentation changes
- approved Prompt #11 review notes

## Required Boundaries

- keep target repositories explicit
- keep private data out of training sets unless approved
- keep generated artifacts reviewable
- document what data was collected
- document why the data was collected
- document what workflow the data improves
- keep fine-tuning submission human-approved

## Current Workflow Evidence

The repository contains `.github/workflows/auto-train.yml`.

Observed workflow behavior:

- runs on push to `main`
- runs on weekly schedule
- supports manual workflow dispatch
- accepts a manual `submit_fine_tune` input
- uploads training artifacts

## Review Questions

1. What repositories are approved as training sources?
2. What data types are allowed?
3. What data types are excluded?
4. Where are artifacts stored?
5. Who approves any fine-tuning submission?
6. What evidence proves the workflow improved?

## Next Action

Inspect `training/pipeline.py` and confirm how examples are collected, validated, merged, stored, and optionally submitted.
