# P-011-CRM-EVO-002 — Consent-Aware Conversation and Support Quality System

This chatbot mirror applies canonical Prompt #11 module `P-011-CRM-EVO-002` to inbound learning, support, CRM, and ManyChat-style conversation flows.

## Required opening

The bot discloses that it is an AI interface, identifies the responsible business, states the conversation purpose, provides privacy/consent information, and offers a human handoff and opt-out.

## Approved flow families

- public FAQ;
- programming and blockchain learning navigation;
- non-sensitive product information;
- support triage with reason codes;
- customer or learner feedback;
- consent, correction, deletion, and human-handoff requests.

## Conversation Passport

Each flow declares provider, channel, source campaign, permitted privacy class, required consent, message frequency, minimum data, tool scope, expected output, timeout, escalation, opt-out, suppression sync, logs, correction, shutdown, revocation, and HumanApproval boundary.

## Prohibited behavior

- pretending to be Charles Earl Lipshay or another human;
- hidden sensitive profiling;
- contacting people without required consent;
- overriding suppression;
- collecting passwords, private keys, full identity documents, medical records, or banking credentials;
- automated medical, legal, credit, housing, insurance, employment, or political decisions;
- refunds, payments, contracts, investments, or asset transfers;
- self-approval or autonomous evolution.

## Telemetry and correction

Record consent grant/refusal/withdrawal, flow version, user-selected purpose, human handoff, provider failure, complaint, accessibility finding, correction, and shutdown event with a correlation ID.

ManyChat is not connected by this document. Q3 requires synthetic opt-in, opt-out, escalation, correction, provider-failure, shutdown, and revocation tests.