# Progress

Snapshot of what's done and what's next, so a new session (human or Claude
Code) can continue without re-deriving decisions already made. Update this
when a milestone's status changes — don't let it go stale.

## Done

**Milestone 1 — Foundation & Contracts.** Git repo initialized
(`main`/`dev`, GitHub remote `Demidoga/scd_a1`). Domain contract
(`Category`/`Priority`/`Status` enums, explicit transition table,
`TriageResult`) in `backend/app/domain/`. `TriageProvider` protocol +
3-implementation scope (no Ollama, `docs/architecture/ai.md` §0) in
`backend/app/providers/triage/`. Frontend runtime config decision (nginx
`/api` proxy) recorded in ADR 0002, not yet implemented (frontend doesn't
exist yet). Compose/Kubernetes topology decisions recorded in the
architecture docs, not yet implemented. `backend/pyproject.toml` (ruff,
mypy, pytest+coverage) configured and passing. ADRs 0001–0004 written.

**Milestone 2 — Database & Backend Core.** PostgreSQL schema via one Alembic
migration (`backend/alembic/versions/0001_create_complaints.py`), verified
against the ORM model with `alembic check` (zero drift). Repository layer
(`ComplaintRepository`), service layer (`ComplaintService`), all 9 API
endpoints (`backend/app/routes/`), `/health` + `/ready`, structured JSON
logging with request-ID propagation (`app/core/logging.py`,
`app/core/middleware.py`), graceful shutdown via FastAPI lifespan, idempotent
seed (`backend/app/seed.py` + `seed_data.py`, 36 complaints across all 6
categories, Urdu-influenced English).

**Milestone 3 — AI Triage & Redis.** `LLMTriage` (Groq), `RuleBasedTriage`,
`SimulatedTriage` all implemented and provider-factory-selectable via
`TRIAGE_PROVIDER`. Retry-once-then-fallback orchestration in
`TriageService`. Redis triage content-hash cache (24h TTL, stores
provenance), stats cache (30s TTL, `X-Cache` header, invalidated on write),
distributed rate limiter (atomic Lua INCR+EXPIRE, fixed-window, fails
closed on Redis outage; caches fail open). Prompt-injection guardrail in the
`LLMTriage` prompt.

**Milestone 4 — Complete Backend API & Tests.** All endpoints finished
including `/api/stats`, `/api/meta/providers`, `/metrics`. 112 tests (63
unit, 49 integration — see `backend/tests/`), 94.5% coverage on `app/`
(gate is 65%). Mandatory fallback test
(`tests/integration/test_fallback_e2e.py`) passes end-to-end through the
real HTTP API via `app.dependency_overrides`.

**Milestone 5 — Frontend.** React 18 + Vite + TypeScript + Tailwind CSS in
`frontend/`. Three views: `SubmitPage` (client validation mirroring backend
limits, honest loading state, renders category/priority/AI summary/provider
on success, field-level 400 errors), `DashboardPage` (category/priority/status
filters, server-driven pagination, status-transition buttons that surface the
backend's 409 message verbatim — no client copy of the transition table, see
`docs/architecture/backend.md` §4), `StatsPage` (aggregates + `X-Cache`
HIT/MISS display). Typed API client in `frontend/src/api/` mirrors
`backend/app/domain/schemas.py`/`enums.py`. Runtime configuration per ADR
0002: all calls go to same-origin `/api/...`, no backend URL baked into the
build — the Vite dev server proxies `/api` to `localhost:8000` as the
dev-time equivalent of the nginx proxy Milestone 6 will add. `ErrorBoundary`
wraps the routed pages. 8 Vitest + Testing Library component tests across
the three pages (validation, loading state, triage rendering, filters,
pagination, 409 verbatim rendering, stats cache state — exceeds the 5
required). Verified end-to-end against the real backend (Postgres + Redis +
`SimulatedTriage`) via the dev proxy: submit → triage → persist → list →
409 on an illegal transition → legal transition succeeds. Docker/nginx
container build is explicitly out of scope here — that's Milestone 6.

## Known, deliberate gaps (not oversights)

- **No Ollama.** Instructor-approved scope reduction — see ADR 0001 and
  `docs/architecture/ai.md` §0.
- **Local dev Postgres is v17, not v16.** `apt` only offered 17 in this
  sandbox. Production-shaped artifacts (Milestone 6+) will pin `postgres:16`
  as required. See `docs/ENGINEERING-NOTES.md`.
- **No live Groq smoke test yet.** `LLMTriage` is fully implemented and
  unit-tested against mocked HTTP responses, but hasn't been exercised
  against the real Groq API — no `LLM_API_KEY` has been provided to this
  session yet. Drop a key into `backend/.env` and run
  `TRIAGE_PROVIDER=llm uv run uvicorn app.main:app` to smoke-test it.
- **`triaged_by` allows `simulated`** in addition to the three values
  `docs/architecture/database.md` §1 literally lists — a resolved doc gap
  from before the no-Ollama decision, not a silent deviation. See
  `docs/ENGINEERING-NOTES.md`.
- **Git workflow is local-only so far.** `dev` branch created locally;
  GitHub branch protection / required PR reviews on `main`/`dev` haven't
  been configured through the GitHub UI or `gh` (not installed in this
  sandbox) — that's a manual step outside this session's tool access.

## Next

**Milestone 6 — Docker/Compose.** Not started. Needs: `frontend/Dockerfile`
(multi-stage `node:22-alpine` build → `nginx:1.27-alpine`, ~60MB target,
`frontend/nginx.conf` implementing the `/api` proxy the frontend already
assumes), `backend/Dockerfile`, `compose.yaml`/`compose.prod.yaml`,
`edge`/`internal` networks, the dedicated `migrate` Compose service.

After that, in order: 7–8 (Kubernetes baseline, then HPA/VPA + load
testing), 9 (CI/CD), 10 (docs/evidence/hardening). See
`docs/architecture/roadmap.md` and `docs/Milestones.md` for the full
dependency chain — don't jump ahead to Kubernetes work while anything in the
backend contract is still moving.
