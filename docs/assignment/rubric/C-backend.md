<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 423-437 (§4 C). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric C: Backend (25). Source: §4 C. Index: [../INDEX.md](../INDEX.md). Related: [../03-backend-layering-and-api.md](../03-backend-layering-and-api.md), [../04-backend-domain-rules.md](../04-backend-domain-rules.md).

# **C · Backend — 25** 

- All ten endpoints to contract, correct status codes, field-level validation errors — **7** 

- Four-layer separation: no SQL outside repositories, no business rules in routes — **4** 

- Status state machine as an explicit transition table; invalid transitions 409 — **3** 

- /health and /ready correctly distinguished; /health does not touch the database — **3** 

- Structured JSON logging to stdout with a propagated request_id — **3** 

- SIGTERM handled: in-flight requests drain before exit — **2** 

- ≥ 14 backend tests, unit and integration, deterministic, coverage ≥ 65% — **3** 
