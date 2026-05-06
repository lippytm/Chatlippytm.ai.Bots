# Security Policy

## Mission

Quality and Quality Assurance is Job #1. Security is a foundation of quality, transparency, documentation, database management, bot workflows, CRM routing, automation, and trust.

## Scope

This repository is part of the lippytm.ai Business of Businesses ecosystem and focuses on AI/chatbot workflow planning.

Security review applies to:

- Bot workflow scripts and prompts.
- ManyChat/BotBuilders planning notes.
- Website and CRM routing copy.
- Lead capture and follow-up workflows.
- GitHub Actions and dependencies.
- Any future code, APIs, databases, or deployments.

## High-risk items

Treat these as high risk:

- API keys, tokens, passwords, private keys, `.env` files.
- Customer/lead data or CRM exports.
- Bot prompts that ask for unnecessary private data.
- Authentication, payment, database, or deployment workflows.
- Automated actions that message, publish, deploy, or change external systems.

## Bot security rules

- Bots should not request passwords, banking credentials, SSNs, private keys, or sensitive legal/tax documents.
- Bots should collect only the information needed for the next business step.
- Human handoff must exist for important or sensitive situations.
- Bot claims should avoid guaranteed leads, sales, income, or outcomes.
- Affiliate/tool recommendations should be disclosed where needed.

## Reporting a security issue

Do not post secrets, private lead/customer data, or exploit details in public issues. Use a private report path where available, or create a general security-risk issue without exposing sensitive details.

## Incident response

If sensitive information is exposed:

1. Remove the exposure.
2. Rotate affected secrets if needed.
3. Review bot/CRM logs if relevant.
4. Patch the root cause.
5. Document prevention steps.
6. Improve automation/checklists.
