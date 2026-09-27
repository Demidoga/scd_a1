# Engineering Notes

Running log of decisions, discrepancies, and justifications that don't
belong in the frozen `docs/architecture/*.md` spec files but need to be
on record for review/viva. Organized by milestone.

---

## Milestone 1 — Foundation

### Assignment brief's "10 endpoints" vs. the actual 9

`docs/architecture/backend.md` §3 already flags this: the assignment brief's
API contract table lists 9 endpoints (`POST /api/complaints`,
`GET /api/complaints/{id}`, `GET /api/complaints`,
`PATCH /api/complaints/{id}/status`, `GET /api/stats`,
`GET /api/meta/providers`, `GET /health`, `GET /ready`, `GET /metrics`), but
rubric Part C references "all ten endpoints to contract." No tenth endpoint
appears anywhere else in the assignment text. Treated as a counting slip in
the brief; all 9 documented endpoints are implemented
(`backend/app/routes/`). Noting it here so it reads as noticed-and-resolved
at viva, not an oversight.

### No-Ollama scope reduction

`docs/architecture/ai.md` §0 already documents the instructor-approved
decision to implement a single live triage path (hosted Groq) instead of
both hosted and local (Ollama) paths. `TriageProvider` has 3 implementations
(`LLMTriage`, `RuleBasedTriage`, `SimulatedTriage`), satisfying the rubric's
"≥ 3 implementations" requirement. Flagging again here because
`docs/Milestones/milestone-3.md` (written before this decision) still lists
`OllamaTriage` as required — that milestone doc is superseded by
`docs/architecture/ai.md` §0 and `CLAUDE.md` on this point.

## Milestone 2 — Database & Backend Core

### Required indexes and the queries they serve

1. **`ix_complaints_status_priority` on `(status, priority)`** — serves the
   operations dashboard's primary filter query,
   `GET /api/complaints?status=...&priority=...`
   (`app/repositories/complaints.py::list_complaints`), which filters on
   both columns together. A composite index lets Postgres satisfy that
   WHERE clause with a single index scan instead of two separate scans
   merged in memory.
2. **`ix_complaints_created_at` on `created_at`** — serves the default list
   ordering (`ORDER BY created_at DESC`, `docs/architecture/backend.md` §3.2)
   and any "most recent N complaints" query, including
   `GET /api/meta/providers`'s "last 20 triage outcomes"
   (`ComplaintRepository.recent`).

Verified via `EXPLAIN`-style reasoning rather than a captured plan in this
document: both indexes exist on the live schema (see
`backend/alembic/versions/0001_create_complaints.py`) and `alembic check`
confirms the migration matches the ORM model with zero drift.

### `triaged_by` allows `simulated`, not just the three values database.md lists

`docs/architecture/database.md` §1 lists `triaged_by` as
`llm:groq | rules | rules:fallback`. That table predates the Milestone 1
no-Ollama scope decision and was never updated to account for
`TRIAGE_PROVIDER=simulated` being the CI/dev default — under a strict
reading, a successful `simulated` triage would have nowhere valid to record
itself. The `ck_complaints_triaged_by_enum` CHECK constraint
(`app/repositories/models.py`) therefore allows
`('llm:groq', 'rules', 'rules:fallback', 'simulated')`. This is a resolved
documentation gap, not a silent deviation — noted here and in
`app/repositories/models.py`'s module docstring.

### PostgreSQL version note

The architecture doc specifies PostgreSQL 16. This dev sandbox's `apt`
repository only offered PostgreSQL 17 (Debian's current default at the time
of implementation), so local development and the test database
(`civicpulse_test`) run against 17. This has no observed effect on the
schema (no version-16-specific or version-17-specific SQL is used — plain
`timestamptz`, `VARCHAR`, `CHECK`, and standard B-tree indexes throughout).
The production-shaped artifacts built in Milestone 6+ (`compose.yaml`,
`compose.prod.yaml`, `k8s/base/postgres.yaml`) pin `postgres:16` explicitly,
as the assignment requires — this note only concerns the local dev
environment.

### `id` generation: DB-side default, app-side override

`Complaint.id` has `server_default=gen_random_uuid()` (native to PostgreSQL
13+, no `pgcrypto` extension needed) — genuinely DB-generated for any insert
that doesn't specify one. In practice, `ComplaintService.create()` generates
the UUID in Python *before* calling the triage pipeline, so a triage
fallback's WARNING log line can include the complaint's real ID even though
triage happens before the row is persisted (validate → triage → persist
ordering, `docs/architecture/backend.md` §3.1). The server-side default
remains as a safety net for any future direct-SQL insert path.

## Milestone 3 — AI Triage & Redis

### Retry/fallback lives in the service layer, not inside each provider

`docs/architecture/ai.md`'s pipeline diagram shows the "one jittered retry"
arrow originating from the provider-call step in the overall pipeline, not
from inside a specific provider implementation. `TriageService`
(`app/services/triage.py`) owns retry-once-then-fallback as one policy
applied uniformly to whichever live provider is configured — `LLMTriage`
itself makes exactly one HTTP attempt per `triage()` call and raises a
classified error on failure. This keeps retry/fallback/jitter/caching
testable once, via `SimulatedTriage(force_failure=...)`, instead of
duplicated per provider.

### Triage cache stores provenance, not just the result

The content-hash cache (`app/providers/redis/cache.py::TriageCache`) stores
`{result, triaged_by}`, not a bare `TriageResult`. A cache hit reports the
`triaged_by` marker that actually produced the cached classification,
rather than whatever provider happens to be active at hit time — relevant
if `TRIAGE_PROVIDER` changes while a still-live 24h cache entry exists.

### Triage cache hit rate

Measured via Prometheus counters `triage_cache_hits_total` /
`triage_cache_misses_total` (`app/core/metrics.py`), exposed on `/metrics`.
Hit rate = `hits / (hits + misses)`. Verified functionally in
`backend/tests/integration/test_triage_cache.py` (repeated identical
`(text, location)` input causes exactly one provider call across two
`triage()` invocations).

### Redis AOF justification

Redis is used for two responsibilities (stats cache, rate limiter) plus the
triage content-hash cache — all three are, in principle, rebuildable: stats
recompute from PostgreSQL, triage cache entries just cost one re-inference,
and the rate limiter's worst case on data loss is a temporarily under-
enforced limit, not incorrect enforcement. AOF is still enabled
(`appendonly yes`, named volume `redisdata`) because:

1. **Rate-limiter continuity matters within its own outage window.** If
   Redis restarts mid-burst without AOF, every IP's counter resets to zero,
   handing a clean rate-limit window to exactly the traffic pattern (a
   burst) the limiter exists to catch.
2. **It costs nothing extra to demonstrate the required persistence
   behavior** (`docs/architecture/cache.md` §3) — the assignment explicitly
   asks for AOF on a named volume, and the operational cost of enabling it
   on a single-instance Redis at this scale is negligible.
3. Without AOF, a container recreate (not just a process restart) loses all
   three data sets simultaneously; with it, only the fail-open caches
   (stats, triage) would need to naturally repopulate on next use, and even
   the rate limiter recovers its exact prior counters instead of resetting.

### Fail-open vs. fail-closed, restated

`docs/architecture/cache.md` §2 already documents this, restated here for
visibility: the stats cache and triage cache fail **open** on a Redis
outage (degrade to a direct PostgreSQL query / direct provider call — pure
optimizations, no cost-control role). The rate limiter fails **closed**
(`503`) — it exists specifically to protect the shared Groq free-tier
quota, and an outage window is exactly when unlimited traffic is least
affordable. Both behaviors are unit-tested directly against a
`redis.RedisError`-raising mock client in
`backend/tests/unit/test_redis_fail_modes.py`, independent of whether a
real Redis outage can be reproduced in this environment.

### Hosted-LLM / internal-network topology (decided, not yet built)

`docs/architecture/ai.md` §6 and `docs/Milestones/milestone-1.md` §F2 fix
the decision that the backend is the only service attached to both the
`edge` and `internal` Compose networks, so hosted Groq calls leave through
`edge` while PostgreSQL/Redis stay on `internal: true` with no outbound
internet path. This is recorded as decided during Milestone 1; the actual
`compose.yaml` implementing it is Milestone 6 scope and doesn't exist yet.
