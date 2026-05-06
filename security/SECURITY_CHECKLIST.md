# Security Checklist for Chatlippytm.ai.Bots

## Purpose

Use this checklist before changing bot workflows, prompts, CRM paths, lead capture forms, GitHub Actions, dependencies, website copy, or future deployments.

## Core principle

Quality and Quality Assurance is Job #1. Bot security is part of quality because bots can touch leads, customers, messages, websites, CRM records, and business follow-up.

## Repository checklist

- [ ] `SECURITY.md` exists.
- [ ] Security checklist exists.
- [ ] Dependabot is configured.
- [ ] CodeQL or equivalent scanning is configured where useful.
- [ ] Dependency review runs on pull requests.
- [ ] No secrets are committed.
- [ ] No `.env` files are committed.
- [ ] No private lead/customer data is committed.
- [ ] No CRM exports are committed.
- [ ] No database dumps are committed.

## Bot workflow checklist

- [ ] Every bot has one clear job.
- [ ] The bot collects only necessary information.
- [ ] Human handoff exists.
- [ ] The bot does not ask for passwords, SSNs, banking credentials, private keys, or sensitive legal/tax documents.
- [ ] FAQ answers are reviewed before publishing.
- [ ] Follow-up messages are reviewed before automation.
- [ ] Affiliate/tool recommendations include disclosure where needed.
- [ ] Bot claims avoid guaranteed leads, sales, income, funding, or business outcomes.

## CRM and lead data checklist

- [ ] Lead source is tracked.
- [ ] CRM tag is assigned.
- [ ] Sensitive data is minimized.
- [ ] Contact records are stored in an appropriate system, not public GitHub.
- [ ] Private notes are not added to public docs.
- [ ] Retention/deletion process is documented when needed.

## GitHub Actions checklist

- [ ] Workflow permissions use least privilege.
- [ ] Pull request workflows do not expose secrets to untrusted code.
- [ ] Third-party actions are reviewed.
- [ ] Failed runs are categorized using the control-tower taxonomy.
- [ ] True vulnerabilities get a security-risk issue.

## Dependency checklist

- [ ] New dependencies are necessary.
- [ ] High/critical vulnerabilities are reviewed.
- [ ] Major upgrades are reviewed before merge.
- [ ] Unused dependencies are removed.

## Website and public copy checklist

- [ ] CTA is clear and safe.
- [ ] No guaranteed lead/sales/income claims.
- [ ] No unsupported cybersecurity claims.
- [ ] Affiliate disclosures are included where needed.
- [ ] Contact forms do not collect unnecessary sensitive data.

## Weekly security rhythm

- [ ] Review failed Actions runs.
- [ ] Review Dependabot alerts and PRs.
- [ ] Review CodeQL findings if applicable.
- [ ] Review bot prompts for unsafe data collection.
- [ ] Review CRM and lead handling notes.
- [ ] Update security docs when new risks are found.

## Best practice

Start with safe, narrow bot workflows. Expand automation only after the workflow, data handling, human handoff, and follow-up path are documented.