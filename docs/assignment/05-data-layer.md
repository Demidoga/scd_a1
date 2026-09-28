<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 123-153 (§2.3). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Data layer (PostgreSQL, schema, indexes, seed, persistence). Source: §2.3. Index: [INDEX.md](INDEX.md). Related: [rubric/D-data-layer.md](rubric/D-data-layer.md).

# **2.3 Data layer** 

**PostgreSQL 16.** Schema managed by **Alembic migrations** — no CREATE TABLE in application startup code, ever. A migration is a versioned, reviewable, reversible change; a startup script is a hope. 

Minimum schema: 

|**Column**|**Notes**|
|---|---|
|id|UUID, server-generated|
|text|10–2000 chars, enforced in the DB as well as the app|
|location|3–200 chars|
|reporter_contact|nullable|
|category|enum: water · electricity · sanitation · roads · streetlights · other|
|priority|enum: high · normal · low|
|status|enum: open · in_progress · resolved · rejected, default open|
|ai_summary|nullable — one line, ≤ 140 chars|
|triaged_by|llm:groq · llm:ollama · rules · rules:fallback|



|triage_latency_ms|integer — you cannot reason<br>measuring it|about cost or latency without|
|---|---|---|
|created_at / updated_at|timestamptz, UTC||



**Required:** indexes on (status, priority) and created_at — and a sentence in your engineering notes on _which query_ each one serves. An unexplained index is cargo cult. 

**Required:** an idempotent seed command loading ≥ 30 realistic complaints in Urdu-influenced English, spread across categories. Running it twice must not duplicate rows. Your dashboard demo is worthless against an empty table, and "idempotent" is the whole point of a seed script. 

**Persistence contract.** docker compose down then up must preserve every row. On Kubernetes, deleting the Postgres pod must preserve every row. You will demonstrate both. 
