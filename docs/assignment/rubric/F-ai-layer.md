<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 459-473 (§4 F). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric F: AI layer (25). Source: §4 F. Index: [../INDEX.md](../INDEX.md). Related: [../07-ai-interface-and-providers.md](../07-ai-interface-and-providers.md), [../08-ai-reliability-and-testing.md](../08-ai-reliability-and-testing.md).

# **F · AI layer — 25** 

- TriageProvider interface with ≥ 3 working implementations selected by environment variable — **5** 

- Structured output requested **and** validated against a Pydantic schema; malformed output rejected safely — **5** 

- Timeout, single jittered retry on retryable errors only, fallback to rules, triaged_by recorded — **6** 

- Content-hash caching of triage results with a measured, reported hit rate — **3** 

- Prompt-injection guardrail plus a test that submits an injection attempt — **3** 

- triage_latency_ms recorded and surfaced through /api/meta/providers — **2** 

- PII/data-governance ADR: what leaves your machine, to whom, and why that is acceptable — **1** 
