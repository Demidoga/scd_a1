# ADR 0004 — PII and Data Governance

## Status

Accepted.

## Context

Citizen complaint text is free-form and can contain identifying information
— the assignment's own example complaint ("burst water main flooding Street
12 since fajr") embeds a location detail in the narrative itself, and real
citizens routinely include names, addresses, or phone numbers in complaint
text even though `reporter_contact` is a separate, optional field. Complaint
`text` and `location` are sent to a third-party hosted provider (Groq) as
part of `LLMTriage.triage(text, location)`, so this is a real data-exposure
decision, not a hypothetical one, and the assignment explicitly requires it
to be documented.

## Decision

### What leaves the machine

Only `complaint.text` and `complaint.location` — the two arguments to
`TriageProvider.triage(text, location)` — are sent to Groq, as the user
message in the triage prompt (`backend/app/providers/triage/llm.py`).
Nothing else is included in the request payload.

### What never leaves the machine

`reporter_contact` is never sent to any triage provider. This is
**structurally enforced, not a convention that could be forgotten**: the
`TriageProvider.triage()` interface signature only accepts `text` and
`location` (`docs/architecture/ai.md` §1) — there is no parameter through
which `reporter_contact` could reach a provider call even by mistake.

### Redaction

None. Complaint text is sent as-is, unredacted, to Groq when `LLMTriage` is
the active provider.

### Why this is acceptable for this project

CivicPulse, as submitted for this assignment, operates on seed/demo data and
low-stakes coursework submissions — not real citizen complaints. Automated
PII redaction (regex/NER-based scrubbing of names, phone numbers, and
addresses before the provider call) was considered and explicitly rejected
for this iteration: it would add a new component, its own test surface, and
a new failure mode (redaction masking words that change the correct
classification — e.g. stripping "Street 12" could remove information the
classifier legitimately needs), which is not a good trade against the
assignment's timeline for a system that isn't handling real personal data.

### What would have to change before this handled real citizen data

Either (a) a redaction/minimization step ahead of the provider call, so
names/addresses/phone numbers are stripped or tokenized before `text` and
`location` leave the machine, or (b) restricting AI triage to a fully local
provider (e.g. a self-hosted model) so complaint text never leaves the
machine at all. `RuleBasedTriage` already demonstrates that a fully local,
zero-network classification path is viable for this application — it just
trades away LLM-quality classification to get there.

### Provider terms (Groq), checked 2026-09-27

Per Groq's own documentation (`console.groq.com/docs/your-data`, fetched
2026-09-27):

- **No training on customer data**: Groq is not permitted to use customer
  inputs/outputs to train or fine-tune any AI model unless the customer
  explicitly grants permission.
- **Default retention**: Groq does **not** retain customer data for
  inference requests by default. Usage metadata is always collected but
  explicitly does *not* contain customer inputs or outputs.
- **Exception**: inputs/outputs may be temporarily logged for system
  reliability troubleshooting or abuse investigation, retained for **up to
  30 days**, unless law requires longer.
- **Zero Data Retention (ZDR)**: customers can enable ZDR (Console → Data
  Controls) to disable even that 30-day troubleshooting/abuse-monitoring
  retention.
- **Data location**: customer data is retained in Google Cloud Platform
  (GCP) buckets located in the United States.

Because Groq's own terms note these policies can change, re-check
`console.groq.com/docs/your-data` (and `groq.com/terms-of-use`) before
relying on this ADR as current if this project is ever extended beyond
coursework use.

### What must never be logged

Regardless of provider, the LLM API key must never appear in logs, source
control, or the frontend bundle — enforced by `LLMTriage` only ever reading
it from `Settings.llm_api_key` (environment-sourced,
`docs/architecture/ai.md` §5 "Secrets") and by the fallback-warning log
statement in `app/services/triage.py` only including `complaint_id`,
`provider`, and `error_class` — never raw provider responses or credentials.

## Consequences

- If this project were extended to handle real citizen submissions, this
  ADR is the checklist for what must change first: add redaction, or make
  `RuleBasedTriage` (or a local-only provider) the default instead of
  `LLMTriage`, and/or enable Groq ZDR.
- Reviewers/graders can audit the actual data flow by reading one file
  (`app/providers/triage/llm.py`) rather than tracing it through the whole
  service layer, because the provider interface itself is the enforcement
  mechanism for "reporter_contact never leaves the machine."
