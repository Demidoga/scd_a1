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
(multi-stage `node:22-alpine` build → `nginx:1.27-alpine-slim`, 20.3MB
(see M6 addendum below for the optimization history), no
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

**Milestone 6 addendum — Docker verification pass (2026-09-29).** Re-verified
against a real Docker Desktop engine on a fresh branch
(`feature/m6-docker-verification`); evidence in
`docs/evidence/milestone-6/`. Two genuine, previously-undetected bugs found
and fixed with minimal changes (no architecture/app-code touched):

- **`BACKEND_PORT` was inert.** It was piped into the `backend` container's
  environment but nothing consumed it — `Dockerfile`'s `CMD`/`HEALTHCHECK`,
  `compose.yaml`'s dev `command:` override, and the host port mapping all
  hardcoded `8000`, and `frontend/nginx.conf`'s upstream is a hardcoded
  `backend:8000` (container-to-container, same network — doesn't need to
  vary). Fixed by making the **host-published** port follow the variable:
  `compose.yaml` backend `ports:` is now `"${BACKEND_PORT:-8000}:8000"`.
  Internal container port and the nginx upstream intentionally stay fixed
  at 8000.
- **Frontend `HEALTHCHECK` always failed.** `frontend/Dockerfile` probed
  `http://localhost:8080/`, but the alpine image's `/etc/hosts` resolves
  `localhost` to `::1` first and nginx's `listen 8080;` only binds IPv4 —
  every check failed with connection-refused, so `frontend` never left
  `health: starting`/reached `healthy`, and anything depending on it (there
  is nothing today, but this would block future `depends_on:
  service_healthy` edges onto `frontend`) would hang. Fixed by probing
  `http://127.0.0.1:8080/` instead. Confirmed fixed: all four services
  (`postgres`, `redis`, `backend`, `frontend`) reach `healthy` in
  `docker compose ps` after the fix, including across a full
  `down` → `up -d` cycle.

Re-confirmed with real commands this session: `.dockerignore` reduces
backend build context 589.3kB → would be 143.8MB without it (~99.6%
reduction), frontend 187.9kB → would be 156.1MB without it (~99.9%
reduction); frontend final image was initially 74.5MB (Node fully absent —
confirmed via `which node npm` inside the running container — but ~24%
over the ~60MB target, driven by `nginx:1.27-alpine`'s bundled dynamic
modules — geoip/image-filter/njs/xslt — none of which
`frontend/nginx.conf` uses). Optimized in a follow-up pass: swapped the
runtime base to the official `nginx:1.27-alpine-slim` tag (no other
Dockerfile/nginx.conf change) → 20.3MB, comfortably under target. Verified
the swap doesn't break anything: `nginx -t` passes, `wget` (used by
`HEALTHCHECK`) is present, the container reaches Docker `healthy`, HTTP 200
served end-to-end, and the full `docker compose` stack still reaches
`healthy` on all four services with the new image. Backend image 333MB;
frontend→postgres
isolation confirmed at the DNS layer (`frontend` is only on `edge`,
`postgres` only on `internal`); a real inserted complaint row survived a
full `docker compose down` (no `-v`) / `up -d` cycle with identical
id/timestamp; exactly 2 named volumes (`pgdata`, `redisdata`), no
`ollama_models` — consistent with the no-Ollama scope decision above;
`compose.prod.yaml` re-confirmed to require `${IMAGE_TAG}`, publish only
port 80 (frontend), and contain no dev bind mounts.

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

**Not done in Milestone 7 (moved to Milestone 8, now done there):** formal
zero-downtime evidence under k6 load, HPA/VPA. `prod` overlay applied to a
cluster is still only rendered/validated (its GHCR images don't exist until
Milestone 9); `runAsNonRoot` is still not set.

**Milestone 8 — HPA, VPA & Operational Testing. Done — including live-cluster evidence.**
`k8s/base/hpa.yaml` (`autoscaling/v2`, 2–10 replicas, CPU 60%,
`scaleUp.stabilizationWindowSeconds: 0` / `scaleDown: 300`) and
`k8s/base/vpa.yaml` (`updateMode: "Off"`) added to the base kustomization.
`backend.yaml`'s `replicas: 2` removed (the HPA owns replica count now);
`check_manifest_invariants.py::check_backend` updated to assert the
Deployment carries no `replicas` field and that `HorizontalPodAutoscaler/backend`
exists with `minReplicas >= 2`; `validate-manifests.sh` passes
`-ignore-missing-schemas` to kubeconform (no schema exists for the VPA CRD).
`load/k6-script.js` ramps GET `/api/stats` + `/api/complaints` traffic 5→50
VUs plus a steady low-rate `POST /api/complaints` scenario, with
`error rate < 1%` / `p95 < 500ms` thresholds. Tooling installed this session:
`k3d` (winget), `helm` (winget), `k6` (portable binary — the winget MSI
failed silently under this sandbox's non-interactive install, see
`docs/ENGINEERING-NOTES.md`), VPA CRDs + controllers via the
`cowboysysop/vertical-pod-autoscaler` Helm chart into `kube-system`.

**Verified live on a local k3d cluster (k3d v5.9.0, k3s v1.35.5):**
- `scripts/k8s/create-secrets.sh` had a Windows bug (`--from-env-file=<(...)`
  process substitution — `kubectl.exe` can't read Git Bash's `/proc/self/fd/N`
  path) fixed to use a real temp file. Confirmed working.
- Full `deploy.sh dev` including `hpa.yaml`/`vpa.yaml` against a live
  metrics-server + VPA install: `smoke-test.sh` green.
- **Run 1** (original guessed requests, `cpu: 100m`): k6 ramp to 50 VUs drove
  the HPA through its full range, `SuccessfulRescale` events captured —
  2→5→7→10 replicas, CPU pinned 130-248%/60% even at `maxReplicas` (the
  original request was too small a denominator — the fleet's real-CPU
  ceiling at 10 pods was only 1 core). Scale-down 10→6→2 measured 296s after
  the last above-target reading, matching the configured 300s
  `scaleDown.stabilizationWindowSeconds` almost exactly.
- **VPA recommendation** captured after Run 1: Target `cpu: 296m,
  memory: 250Mi` (`kubectl describe vpa backend-vpa`).
  `k8s/base/backend.yaml`'s `resources.requests` updated to `300m/256Mi`
  (`limits` to `750m/384Mi`) to match, redeployed.
- **Run 2** (resized requests): same k6 script, HPA topped out at 9/10
  (never hit max) with CPU settling to 30-50%/60% instead of pinning above
  100% — direct evidence the resize fixed the fleet's real capacity ceiling,
  not just the HPA's math.
- **Zero-downtime rolling update under load:** `kubectl set image` on all 10
  replicas mid-k6-run (05:33:14Z→05:34:40Z, ~86s) — 0.00% `http_req_failed`
  across 36,294 requests during that run.
- Replicas-vs-load charts rendered from the raw `kubectl get hpa` captures:
  `load/results/hpa-run1-replicas-vs-load.png`,
  `load/results/hpa-run2-replicas-vs-load.png`.
- Full data/analysis, plus a discovered gotcha (redeploying resets an
  imperative `kubectl patch configmap` rate-limit bump, since the committed
  ConfigMap still has the real default — this caused Run 2's one non-zero
  error rate, on the rate-limited POST path only, unrelated to HPA/VPA
  behavior), are in `docs/ENGINEERING-NOTES.md` Milestone 8, including Q5
  (measured HPA lag, not a placeholder) and Q6 (VPA `Off` mode) with real
  numbers cited throughout.

**Not done (by design / out of scope):** `prod` overlay HPA/VPA behavior on
a real cluster (same GHCR-image blocker as Milestone 7); a second, cleaner
Run 2 with the rate limit correctly re-bumped (not worth re-running — the
0.64% failures were isolated to the rate-limited write scenario and didn't
affect the CPU signal the HPA/VPA comparison depends on).

**Milestone 9 — CI/CD & Security Gates. Workflows written; live results not verified from this sandbox.**
`.github/workflows/ci.yml` (PR to `main` and push to `dev`: `lint-and-type`, `test-backend` with Postgres 16/Redis 7 service containers and `TRIAGE_PROVIDER=simulated`, `test-frontend`, `build` (no push), Trivy `scan` with `--ignore-unfixed` on HIGH/CRITICAL, `manifests` via `scripts/k8s/validate-manifests.sh`, Compose `integration` smoke test asserting the exact category and X-Cache MISS→HIT); `cd.yml` (`test` → `build-push` → `deploy-k8s`, each `needs:` the previous; GHCR images tagged by `github.sha` plus `latest`, Syft SBOMs, digests as outputs, ephemeral k3d cluster, `deploy.sh prod <sha>`, Ingress smoke test, `kubectl get hpa`); `release.yml` (tag `v*`, gated on the same CI via `workflow_call`, semver-tagged images, generated release notes). Least-privilege `permissions:` on each; all registry auth uses `GITHUB_TOKEN`; actions pinned `@v4`+ or a full version tag. Operational guide: `docs/CI-CD-SETUP.md`. **Not confirmed:** that the latest CI/CD runs are green, branch protection, and the repo secrets — GitHub-side, `gh` is not installed here. The two newest CD commits were crash fixes.

**Milestone 10 audit pass (2026-09-29).** Todo re-audited against the rubric (`docs/Todo.md`). Fixed: `release.yml` had no `needs:` gate; several actions were below `@v4`; the CI integration job used the default `TRIAGE_PROVIDER=llm` instead of `simulated` and only warned on a missing cache MISS; frontend was on React 19 (now React 18.3.1; build, types and 9 tests pass); no seed idempotency test (`backend/tests/integration/test_seed.py`); duplicate git identities (`.mailmap`). Added: `docs/RUNBOOK.md`, `docs/AI-USAGE.md` (authors must complete marked sections), `scripts/check_submission.py`, `docs/evidence/README.md`, README problem statement/badges/Mermaid/API table/one-command quickstart, engineering-note answers Q1–Q4, Q7, Q8 (Q2 and Q8 are drafts to confirm). Test state: 118 backend tests at 98% coverage, 9 frontend tests.

**Known gap found by the audit, not fixed:** the backend image installs dependencies with `pip install .` (`backend/Dockerfile:18-21`), not from `uv.lock`, so the shipped dependency set can differ from the tested one (Q1 in `docs/ENGINEERING-NOTES.md`).

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

**Milestone 10 — docs, evidence, hardening.** Remaining work is mostly manual and outside the repository: enable branch protection and add the repo secrets (`docs/CI-CD-SETUP.md`), do the deliberate failing PR (red then green) and the merge-conflict exercise using feature branches and PRs, record a green `cd.yml` run, demonstrate both rollbacks (`docs/RUNBOOK.md` §2), add README screenshots, record the demo video, and complete the `[AUTHORS TO COMPLETE]` sections of `docs/AI-USAGE.md`. Then run `python scripts/check_submission.py` and finish `docs/Todo.md` §25 and §29. See `docs/architecture/roadmap.md` for the dependency chain.
