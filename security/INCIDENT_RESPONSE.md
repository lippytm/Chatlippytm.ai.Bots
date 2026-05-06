# Incident Response for Chatlippytm.ai.Bots

## Purpose

Provide a response plan for bot, CRM, lead data, workflow, dependency, and automation security issues.

## Incident examples

- Bot asks for sensitive private information.
- Bot platform token or API key exposed.
- CRM export or lead list committed to GitHub.
- Customer conversation transcript exposed.
- Dependency vulnerability found.
- GitHub Actions workflow fails insecurely.
- Public bot claim creates compliance risk.

## Response process

### 1. Identify

Record:

- What happened?
- Which workflow/bot/file/platform is affected?
- What data may be exposed?
- Is the issue low, medium, high, or critical?

### 2. Contain

- Remove exposed data.
- Disable risky bot flow or workflow.
- Rotate affected token/key.
- Stop unsafe intake question.
- Restrict access if needed.

### 3. Fix

- Patch the workflow or prompt.
- Update dependency.
- Rewrite unsafe bot copy.
- Add human handoff.
- Update data handling docs.

### 4. Recover

- Re-run security checks.
- Confirm bot no longer collects unsafe data.
- Confirm CRM/lead routing is safe.
- Confirm no secrets remain exposed.

### 5. Learn

- Add a prevention checklist.
- Update `SECURITY_CHECKLIST.md`.
- Create a security-risk issue if needed.
- Document what changed.

## Severity guide

### Low

Documentation or wording issue.

### Medium

Unsafe bot prompt, dependency alert, workflow misconfiguration.

### High

Exposed token/key, private lead data, CRM export, unsafe automation.

### Critical

Compromised account, active abuse, major data exposure, production credential compromise.

## Incident report template

```md
# Chatlippytm.ai.Bots Security Incident

Date found:
Affected workflow/bot/file:
Severity:

## Summary

## Impact

## Containment

## Root cause

## Fix

## Prevention added
```

## Best practice

A bot security incident should improve the bot system. Fix the issue, then improve the workflow, checklist, and documentation so the problem is less likely to repeat.
