# Data Classification for Chatlippytm.ai.Bots

## Purpose

Define how bot, CRM, lead, prompt, and workflow data should be handled.

## Public data

Examples:

- Public bot workflow examples.
- Public README files.
- Public Canva prompts without private information.
- Public website copy.
- Public social posts.

Handling:

- Safe to publish after review.
- Still review for accuracy, affiliate disclosure, and safe claims.

## Internal data

Examples:

- Draft bot scripts.
- Internal workflow notes.
- Non-sensitive campaign ideas.
- Performance summaries without private lead details.

Handling:

- Review before publishing.
- Keep private if it includes business-sensitive plans.

## Confidential data

Examples:

- Lead/customer names and contact details.
- CRM exports.
- Private business notes.
- Customer conversation transcripts.
- Bot intake responses connected to real people.

Handling:

- Do not commit to public GitHub.
- Store only in approved CRM or private systems.
- Limit access.
- Redact before using in examples.

## Restricted / high-risk data

Examples:

- Passwords.
- API keys.
- Bot platform tokens.
- ManyChat/BotBuilders credentials.
- Private keys.
- `.env` files.
- Banking credentials.
- SSNs.
- Sensitive legal/tax documents.
- Database credentials.

Handling:

- Never commit to GitHub.
- Rotate immediately if exposed.
- Use secure secret storage.
- Do not ask users for this data through bots.

## Bot data minimization rules

Bots may ask for:

- Name.
- Contact method.
- Business/project name.
- General workflow need.
- Preferred next step.

Bots should not ask for:

- Passwords.
- Banking credentials.
- SSNs.
- Private keys.
- Sensitive legal/tax documents.
- Full payment information.

## Example safe bot intake

```text
What should your first bot help with?
1. Lead capture
2. FAQ
3. Appointment routing
4. Follow-up
5. Support triage
6. Affiliate/tool routing
```

## Incident rule

If private or restricted data is exposed:

1. Remove exposure.
2. Rotate secrets if needed.
3. Document the issue.
4. Add prevention checklist.
5. Review bot prompts and forms.
