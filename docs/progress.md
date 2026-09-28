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

**Milestone 7 — Kubernetes Baseline.** `k8s/base/` (namespace, ConfigMap, placeholder
Secret, `postgres` StatefulSet with `volumeClaimTemplates`, `redis` Deployment
with PVC and `strategy: Recreate`, `migrate` Job, `backend` and `frontend`
Deployments at 2 replicas, 4 ClusterIP Services, Ingress `/`→frontend and
`/api`→backend with no `host:`, backend PDB `minAvailable: 1`), overlays
`dev` (local images, `TRIAGE_PROVIDER=simulated`) and `prod` (GHCR image
names, `llm`), and the shared component `k8s/components/external-secret` that
removes the placeholder Secret from both overlays (real credentials are made
by `scripts/k8s/create-secrets.sh` from `.env`, and by CD later). Backend
probes: startup+liveness `/health`, readiness `/ready`; `maxSurge: 1` /
`maxUnavailable: 0`; `preStop` sleep; requests/limits on every container per
`docs/architecture/kubernetes.md` §8. `scripts/k8s/` holds the workflow
(`create-cluster`, `load-images`, `create-secrets`, `deploy`, `smoke-test`,
`verify-persistence`) and the static checks (`validate-manifests.sh`,
`check_manifest_invariants.py`). Design decisions and gotchas are in
`docs/ENGINEERING-NOTES.md` (Milestone 7).

**Verified live on a local k3d cluster (k3s v1.35.5, Docker Desktop):**
- `scripts/k8s/validate-manifests.sh` clean for base/dev/prod (`kubeconform -strict` + invariants checker, itself mutation-tested against 11 broken variants).
- `deploy.sh dev`: `job/migrate` reached `Complete` (after 3 in-place retries while Postgres started) before the rollouts; backend ×2, frontend ×2, `postgres-0`, `redis` all Ready.
- `smoke-test.sh` through the Ingress on `localhost:8080`: SPA `200`, `/api/stats` `200 application/json`, `/api/meta/providers` `200`, complaint POST `201` + GET `200`.
- `verify-persistence.sh`: a complaint survived `kubectl delete pod postgres-0` (new pod UID, same PVC).
- Probe semantics: with Redis scaled to 0, both backend pods went `NotReady`, Service endpoints emptied, Ingress returned `503`, and `RESTARTS` stayed `0` (liveness is dependency-independent); everything recovered when Redis returned.
- Rate limiter: `429` after 10 POSTs. Requests sent inside the cluster with `X-Forwarded-For: 203.0.113.77` were bucketed under that address, so `FORWARDED_ALLOW_IPS` works. (On k3d, external clients all appear as `10.42.0.1` — k3d's load balancer rewrites the source address.)
- Rolling restart of the backend under a ~10 req/s `curl` loop: 62 requests, 0 non-200. This is a sanity check only; the formal `kubectl set image` + k6 zero-downtime demonstration is Milestone 8.
- Seed: `kubectl exec deploy/backend -n civicpulse -- python -m app.seed` inserted 36 complaints.

**Bugs/gotchas found by the live run (fixed or documented; details in `docs/ENGINEERING-NOTES.md`):**
- Kubernetes service-link env vars (`BACKEND_PORT=tcp://...`) crashed the migrate Job → `enableServiceLinks: false` on every pod template, enforced by the invariants checker.
- Repo-root `.env` did not exist (only `backend/.env`), so `create-secrets.sh` stopped; created it from `.env.example` (gitignored, dev-default password).
- The k3d node could not pull from Docker Hub on this machine → optional `scripts/k8s/load-base-images.sh`.

**Not done (Milestone 8 / by design):** formal zero-downtime evidence under k6 load, HPA/VPA, `prod` overlay applied to a cluster (only rendered/validated; its GHCR images don't exist until Milestone 9), `runAsNonRoot`.

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

**Milestone 8 — HPA, VPA & operational testing.** Not started. Handoffs from
M7: remove `replicas: 2` from the backend Deployment when the HPA is added;
VPA needs its CRDs installed before `vpa.yaml` can be applied (k3s already
bundles metrics-server); k6 must avoid `POST /api/complaints` or raise
`RATE_LIMIT_REQUESTS` because of the 10 req/60s/IP limiter.

After that, in order: 9 (CI/CD), 10 (docs/evidence/hardening). See
`docs/architecture/roadmap.md` and `docs/Milestones.md` for the full
dependency chain.
