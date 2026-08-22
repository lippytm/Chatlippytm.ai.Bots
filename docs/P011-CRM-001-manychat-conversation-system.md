# P-011-CRM-001 — Consent-Aware Conversation, ManyChat, and Human-Handoff System

**Canonical source:** `lippytm/Prompt-11-`  
**Status:** Q2 architecture mirror

## Objective

Define a provider-neutral chatbot and ManyChat-style conversation architecture for Prompt #11 CRM, Educational Entertainment, learner success, customer support, opportunities, memberships, affiliates, and Business of Businesses journeys.

## Inbound conversation flow

1. Record the entry source, campaign, channel, and correlation ID.
2. Treat the channel identity as a token until a legitimate relationship purpose is established.
3. Display an understandable AI disclosure, privacy notice, and preference choice.
4. Offer bounded paths: learn, get support, explore an offer, affiliate/partner, unsubscribe, or request a human.
5. Provide approved FAQs, navigation, or Educational Entertainment content.
6. Ask only minimum-necessary, non-sensitive qualification questions.
7. Check consent, suppression, age or eligibility constraints when applicable, and channel preference before follow-up.
8. Transfer ambiguous, sensitive, high-impact, complaint, refund, contract, or financial matters to an authorized human.
9. Record the result, evidence, gate state, next action, and correction route.
10. Apply opt-out immediately on the originating channel and synchronize suppression through approved adapters.

## Permitted bot functions

- answer approved public FAQs;
- route users to programming, blockchain, AI, cybersecurity, entrepreneurship, or Fable 5 learning content;
- collect voluntary preferences and support context;
- schedule or request a human follow-up;
- create a bounded CRM mission;
- show product information with transparent limitations;
- provide status and correction links.

## Prohibited bot functions

- impersonate Charles Earl Lipshay or any human;
- hide that an AI or automation is involved;
- infer sensitive traits or create hidden high-impact profiles;
- contact another channel without appropriate consent;
- make medical, legal, credit, employment, housing, insurance, political, or investment decisions;
- approve refunds, prices, payments, contracts, or transfers;
- guarantee earnings, funding, employment, learning, health, or business results;
- publish private evidence or credentials;
- pass HumanApprovalGate.

## Conversation Passport

- flow ID and version;
- provider and channel;
- human owner;
- purpose and target audience;
- source/campaign ID;
- disclosure text;
- consent and suppression rules;
- permitted data fields and privacy class;
- intent routes and human-handoff conditions;
- approved content references;
- timeout, rate limit, and budget;
- logging and correlation;
- tests, defects, and gates;
- rollback, shutdown, revocation, correction, and retirement;
- human approval.

## Required synthetic tests

- first-contact disclosure;
- consent grant, refusal, withdrawal, and unknown state;
- immediate opt-out;
- duplicate or identity ambiguity;
- support escalation;
- complaint and correction;
- financial-authority refusal;
- restricted-data rejection;
- provider failure and human handoff;
- shutdown and revocation.

## CRM event examples

- `conversation.started`
- `preference.selected`
- `consent.granted`
- `consent.withdrawn`
- `lesson.requested`
- `support.requested`
- `human_handoff.requested`
- `opportunity.interest_recorded`
- `suppression.applied`
- `correction.issued`

## Current boundary

ManyChat is not connected through the available tools in this continuation. This document defines a staged architecture and test plan only. No live bot flow, subscriber import, message, or campaign has been created.
