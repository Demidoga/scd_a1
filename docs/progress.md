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

**Milestone 6 — Docker/Compose.** `backend/Dockerfile` (multi-stage
`python:3.12-slim`, dependency-first COPY order via a stub package so
`app/` edits don't invalidate the dependency layer, non-root `app` user,
exec-form `CMD`, `HEALTHCHECK` against `/health`), `frontend/Dockerfile`
(multi-stage `node:22-alpine` build → `nginx:1.27-alpine`, 74.5MB, no
Node/node_modules/source in the runtime stage — verified), `frontend/nginx.conf`
(same-origin `/api` proxy to the `backend` service, SPA fallback for React
Router, DNS resolved at request time via Docker's embedded resolver so the
container doesn't crash if `backend` is briefly unresolvable — this was hit
and fixed during verification, see below). `.dockerignore` for both.
`compose.yaml` (dev: `build:`, backend hot-reload bind mount on
`backend/app`) and `compose.prod.yaml` (prod: `image: ${BACKEND_IMAGE}:${IMAGE_TAG}`
/ `${FRONTEND_IMAGE}:${IMAGE_TAG}`, no `build:`). Both define `edge`/`internal`
(`internal: true`) networks, `pgdata`/`redisdata` named volumes, the one-off
`migrate` service (`alembic upgrade head`, `restart: "no"`,
`service_completed_successfully` gating `backend`), healthchecks +
`condition: service_healthy` on every dependency edge, `restart:
unless-stopped`, and `deploy.resources.limits` on every service. Root
`.env.example`/`.env` extended with `POSTGRES_USER/PASSWORD/DB` and
`BACKEND_IMAGE`/`FRONTEND_IMAGE`/`IMAGE_TAG`. Generated
`frontend/package-lock.json` (didn't exist before; needed for `npm ci` in
the frontend Dockerfile).

Verified live with Docker Desktop in this session: `docker compose up
--build` brings up all four containers (`migrate` runs to completion and
exits, not counted among the four) healthy; frontend→backend traffic
confirmed through the nginx `/api` proxy (submit → simulated triage →
persist → list, through port 8080 only); `docker exec frontend ... postgres`
and `... redis` both fail at DNS resolution (network isolation intact);
`docker compose down` + `up` preserves data in `pgdata` (a complaint
submitted before `down` was still listed after); `compose.prod.yaml`
verified separately by tagging the locally-built images with a fake commit
SHA and running it standalone — healthy, only port 80 published (no
backend/postgres/redis host ports), same persisted data visible through the
shared volumes. Bug found and fixed during this verification: nginx's
`proxy_pass` does not apply its usual location-prefix rewriting when the
proxied host is a variable (needed for request-time DNS resolution) — the
initial `nginx.conf` was silently sending every `/api/...` request to a bare
`/api/` on the backend. Fixed by dropping the trailing URI from
`proxy_pass` so the original request URI passes through unchanged.
`uv run pytest tests/unit -q` (68 passed) and `npm run test` (8 passed) both
still pass unchanged — this milestone touched no application code.

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

**Milestone 7 — Kubernetes Baseline.** Not started. The Compose topology
(`edge`/`internal` networks, `migrate` job pattern, health-gated startup
order) is designed to carry over directly per
`docs/architecture/kubernetes.md` — don't redesign it, translate it.

After that, in order: 8 (HPA/VPA + load testing), 9 (CI/CD), 10
(docs/evidence/hardening). See `docs/architecture/roadmap.md` and
`docs/Milestones.md` for the full dependency chain.
