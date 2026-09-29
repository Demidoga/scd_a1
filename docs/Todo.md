# CivicPulse --- Comprehensive Assignment Checklist

> **Last audited 2026-09-29** against the repo, `docs/architecture/*`, and the assignment spec + rubric (`docs/assignment/`). Rule used: a box is ticked only when the artifact exists in the repo (or a committed evidence file shows it happened). Anything that lives in GitHub's UI (branch protection, repo secrets, PR/Issue counts, workflow-run results, GHCR packages) is left unticked or flagged "unverified", because `gh` isn't installed in this sandbox. Items added by the audit are marked "added" or carry a note explaining the gap.
>
> **Biggest open risks (assignment §5.3 deductions and high-mark items):** direct commits on `main` (−5, history can't be rewritten — use branch + PR from now on) · only 31 of the required 35 commits · the manual GitHub evidence: branch protection, red→green CI with a blocked merge, a green `cd.yml` run link, GHCR links · rollback demo, merge-conflict exercise, README screenshots, demo video · **[AUTHORS TO COMPLETE]** sections of `docs/AI-USAGE.md` and confirming the Q2/Q8 drafts · backend image not installed from `uv.lock` (§11). *Fixed in the follow-up pass:* release `needs:` gate, action pins, deterministic CI integration job, React 18, seed test, `.mailmap`, RUNBOOK, AI-USAGE, `check_submission.py`, README, Q1–Q8.

## 0. Project Setup

-   [x] Create GitHub repository.
-   [x] Add both team members. (partner `tawassulAkbr` has pushed 12 commits; instructor access is tracked in §29)
-   [x] Create `main` and `dev` branches.
-   [ ] Protect `main`. (GitHub UI setting — can't be verified from this sandbox (`gh` isn't installed). Steps: `docs/CI-CD-SETUP.md` §2. Direct commits to `main` in history suggest it is not enforced yet)
-   [ ] Require PRs for `main`. (manual GitHub setting, unverified)
-   [ ] Require CI checks for `main`. (manual GitHub setting, unverified; required job names are listed in `docs/CI-CD-SETUP.md` §2)
-   [ ] Require at least one approval. (manual GitHub setting, unverified)
-   [x] Create initial repository structure.
-   [x] Add `.gitignore`.
-   [x] Add `.env.example`.
-   [x] Ensure `.env` is ignored.
-   [x] Create `README.md`.
-   [x] Create `LICENSE`.

## 1. Backend Foundation

-   [x] Set up FastAPI + Pydantic v2.
-   [x] Create four backend layers.
-   [x] Create `routes/`.
-   [x] Create `services/`.
-   [x] Create `repositories/`.
-   [x] Create `providers/`.
-   [x] Keep SQL inside repositories.
-   [x] Keep business rules inside services.
-   [x] Keep routes HTTP-only.
-   [x] Add dependency injection.
-   [x] Add request validation.
-   [x] Add field-level error responses.
-   [x] Add request ID middleware.
-   [x] Add structured JSON logging.
-   [x] Log to stdout.
-   [x] Propagate `X-Request-ID`.
-   [x] Generate request ID when absent.
-   [x] Add graceful SIGTERM shutdown.
-   [x] Drain in-flight requests.
-   [x] Close database connections on shutdown.

## 2. Database

-   [x] Set up PostgreSQL 16. (`postgres:16-alpine` in both Compose files, `k8s/base/postgres.yaml` and the CI service container; verified live under Compose and k3d. Only the local dev sandbox runs 17)
-   [x] Set up Alembic.
-   [x] Create initial migration.
-   [x] Avoid startup-time DDL.
-   [x] Create UUID primary key.
-   [x] Enforce complaint text length 10--2000.
-   [x] Enforce location length 3--200.
-   [x] Add nullable reporter contact.
-   [x] Add category enum.
-   [x] Add priority enum.
-   [x] Add status enum.
-   [x] Default status to `open`.
-   [x] Add nullable AI summary.
-   [x] Limit AI summary to 140 characters.
-   [x] Add `triaged_by`.
-   [x] Add `triage_latency_ms`.
-   [x] Add UTC timestamps.
-   [x] Add `(status, priority)` index.
-   [x] Add `created_at` index.
-   [x] Document the purpose of both indexes.
-   [x] Create idempotent seed command.
-   [x] Seed at least 30 complaints. (36, `backend/app/seed_data.py`)
-   [x] Use Urdu-influenced English complaints.
-   [x] Spread seed data across categories. (all 6)
-   [x] Verify seed runs twice without duplicates. (`backend/tests/integration/test_seed.py` runs the seed twice and asserts the row count is unchanged)
-   [x] Verify Compose restart preserves data. (`docs/evidence/milestone-6/postgres-persistence.txt`)
-   [x] Verify Kubernetes Postgres pod deletion preserves data. (`scripts/k8s/verify-persistence.sh`, verified live)

## 3. API

-   [x] Implement `POST /api/complaints`.
-   [x] Return `201` on successful creation.
-   [x] Return `400` for validation errors.
-   [x] Return `429` when rate limited.
-   [x] Implement `GET /api/complaints/{id}`.
-   [x] Return `404` for missing complaints.
-   [x] Implement `GET /api/complaints`.
-   [x] Add category filtering.
-   [x] Add priority filtering.
-   [x] Add status filtering.
-   [x] Add pagination.
-   [x] Enforce `page_size <= 100`.
-   [x] Return total count.
-   [x] Implement `PATCH /api/complaints/{id}/status`.
-   [x] Return `409` for invalid transitions.
-   [x] Include attempted transition in `409`.
-   [x] Implement `GET /api/stats`.
-   [x] Add `X-Cache` response header.
-   [x] Implement `GET /api/meta/providers`.
-   [x] Return active provider.
-   [x] Return last 20 triage outcomes.
-   [x] Include provider and latency.
-   [x] Include fallback status.
-   [x] Implement `GET /health`.
-   [x] Keep `/health` independent of the database.
-   [x] Implement `GET /ready`.
-   [x] Check PostgreSQL in readiness.
-   [x] Check Redis in readiness.
-   [x] Return `503` with failed dependency when unavailable.
-   [x] Implement `GET /metrics`.
-   [x] Expose request count.
-   [x] Expose request latency histogram.
-   [x] Expose triage latency.
-   [x] Expose fallback counter.

## 4. Complaint State Machine

-   [x] Define explicit transition table.
-   [x] Allow `open → in_progress`.
-   [x] Allow `in_progress → resolved`.
-   [x] Allow `open → rejected`.
-   [x] Allow `in_progress → rejected`.
-   [x] Make `resolved` terminal.
-   [x] Make `rejected` terminal.
-   [x] Reject all other transitions with `409`.
-   [x] Keep transition rules out of the frontend.

## 5. Redis

-   [x] Set up Redis 7. (`redis:7-alpine` in both Compose files, `k8s/base/redis.yaml` and the CI service container. Only the local dev sandbox runs 8)
-   [x] Implement read-through stats cache.
-   [x] Set stats TTL to 30 seconds.
-   [x] Return `X-Cache: HIT`.
-   [x] Return `X-Cache: MISS`.
-   [x] Invalidate stats cache after writes.
-   [x] Implement distributed IP rate limiting.
-   [x] Use fixed-window algorithm, 10 req/60s per IP (architecture decision — not token-bucket).
-   [x] Use atomic Lua `INCR`+`EXPIRE` (never plain `INCR` then a separate `EXPIRE`).
-   [x] Key rate limits by client IP.
-   [x] Return `429` when exceeded.
-   [x] Return `Retry-After`.
-   [x] Fail closed (`503`) on Redis outage for the rate limiter. (unit-tested, `test_redis_fail_modes.py`)
-   [x] Fail open (degrade to direct query/provider call) on Redis outage for stats cache and triage cache. (unit-tested)
-   [x] Enable Redis AOF. (`--appendonly yes` in both Compose files and `k8s/base/redis.yaml`)
-   [x] Store Redis data on named volume. (`redisdata` in Compose; PVC `redis-data` in Kubernetes)
-   [x] Document the AOF volume decision. (`docs/ENGINEERING-NOTES.md`)

## 6. AI Triage

-   [x] Create `TriageResult` Pydantic model.
-   [x] Add category field.
-   [x] Add priority field.
-   [x] Add summary field.
-   [x] Enforce summary max 140 characters.
-   [x] Add confidence field.
-   [x] Enforce confidence 0--1.
-   [x] Define `TriageProvider` interface.
-   [x] Add provider name.
-   [x] Implement `LLMTriage`.
-   [x] Implement `RuleBasedTriage`.
-   [x] Implement `SimulatedTriage`.
-   [x] Select provider using `TRIAGE_PROVIDER`.
-   [x] Configure hosted provider. (Groq)
-   [x] Use a small instruct model. (`openai/gpt-oss-20b`)
-   [x] Document the selected provider. (ADR 0001, `ai.md`)
-   [ ] Document live provider limits. (no Groq free-tier RPM/TPM limits recorded anywhere yet)
-   [x] Document PII handling: raw complaint text is sent to Groq unredacted (architecture decision, not open).
-   [x] Record PII decision in an ADR. (ADR 0004)

## 7. AI Reliability

-   [x] Request structured JSON from the LLM.
-   [x] Validate output with Pydantic.
-   [x] Reject malformed output safely.
-   [x] Reject invalid enum values.
-   [x] Enforce 10-second timeout.
-   [x] Retry once on timeout.
-   [x] Retry once on `429`.
-   [x] Retry once on `5xx`.
-   [x] Add jitter to retry.
-   [x] Do not retry `400`.
-   [x] Fall back to rule-based triage.
-   [x] Record `triaged_by = rules:fallback`.
-   [x] Add content-hash triage cache.
-   [x] Set triage cache TTL to 24 hours.
-   [x] Measure triage cache hit rate. (Prometheus counters, functionally verified)
-   [ ] Report the measured hit rate. (no observed number recorded — needs real/load traffic)
-   [x] Never log API keys.
-   [x] Load API keys from environment variables.
-   [x] Store Kubernetes API keys in Secrets.
-   [x] Store CI credentials in GitHub Secrets. (`cd.yml` reads `secrets.POSTGRES_PASSWORD`, `secrets.LLM_API_KEY` and `GITHUB_TOKEN`. Creating the repo secrets is a manual step (`docs/CI-CD-SETUP.md` §1) that can't be verified from here)
-   [x] Treat complaint text as untrusted data.
-   [x] Add prompt-injection guardrail.
-   [x] Add prompt-injection test.
-   [x] Configure CI to use `SimulatedTriage`. (`TRIAGE_PROVIDER: simulated` in `test-backend` (`ci.yml:89`) and pinned explicitly in the `integration` job (`ci.yml:280`) because `.env.example` now defaults to `llm`)
-   [x] Add provider failure injection.
-   [x] Test fallback using a failing provider.
-   [x] Test malformed output handling.

## 8. Frontend

-   [x] Set up React 18. (downgraded to React 18.3.1 (`react`, `react-dom`, `@types/*`); lint, `tsc -b`, 9 tests and `npm run build` all pass)
-   [x] Set up Vite.
-   [x] Set up TypeScript.
-   [x] Create submission view.
-   [x] Add complaint text input.
-   [x] Add location input.
-   [x] Add optional contact input.
-   [x] Add client-side validation.
-   [x] Mirror server validation rules.
-   [x] Add honest loading state.
-   [x] Display returned category.
-   [x] Display returned priority.
-   [x] Display AI summary.
-   [x] Display triage provider.
-   [x] Create dashboard view.
-   [x] Add paginated complaint list.
-   [x] Add category filter.
-   [x] Add priority filter.
-   [x] Add status filter.
-   [x] Add status transition controls.
-   [x] Display server `409` message verbatim.
-   [x] Create stats view.
-   [x] Display category aggregates.
-   [x] Display priority aggregates.
-   [x] Display cache-hit state.
-   [x] Read `X-Cache` header.
-   [x] Add typed API client.
-   [ ] Generate or verify client against OpenAPI. (hand-maintained mirror of the backend schemas, no generation/diff step)
-   [x] Add React error boundary.
-   [x] Keep secrets out of frontend.
-   [x] Avoid duplicated backend business rules.

## 9. Frontend Runtime Configuration

-   [x] Use nginx `/api` proxy for runtime configuration (architecture decision — not `/config.js`; dev-time Vite proxy implements the same contract, production nginx config is Milestone 6).
-   [x] Prevent API URL from being baked into the Vite build.
-   [x] Make one frontend image usable across environments. (one `frontend/Dockerfile` output runs under Compose dev/prod and both k8s overlays; the API is same-origin `/api` via `nginx.conf`, nothing baked in)
-   [x] Document the choice in an ADR. (ADR 0002)
-   [x] Verify runtime configuration in dev.
-   [x] Verify runtime configuration in production. (`compose.prod.yaml` and the k3d Ingress both served the SPA + `/api` from the same nginx image — `docs/progress.md` M6/M7)

## 10. Frontend Testing

-   [x] Set up Vitest.
-   [x] Write at least 5 meaningful component tests. (8)
-   [x] Test submission validation.
-   [x] Test loading state.
-   [x] Test complaint rendering.
-   [x] Test dashboard filtering/pagination.
-   [x] Test `409` error display.
-   [x] Test stats/cache indicator.
-   [x] Run frontend tests in CI. (`test-frontend` job in `ci.yml`)

## 11. Docker Images

### Backend

-   [x] Use `python:3.12-slim`.
-   [x] Use multi-stage build.
-   [x] Install dependencies in builder stage.
-   [x] Optimize COPY order.
-   [x] Create non-root user.
-   [x] Use exec-form `CMD`.
-   [x] Add Docker `HEALTHCHECK`.
-   [x] Pin image versions.
-   [ ] Install backend image dependencies from `uv.lock`, not bare `pip install .` (added by audit: `backend/Dockerfile:18-21` lets pip resolve fresh versions, so shipped dependencies can differ from the tested ones — see Q1).
-   [ ] Optionally pin base images by digest.

### Frontend

-   [x] Use `node:22-alpine` build stage.
-   [x] Use `nginx:1.27-alpine` runtime stage.
-   [x] Exclude Node from final image (verified: `which node npm` empty in the running container).
-   [x] Exclude `node_modules` from final image.
-   [x] Exclude source from final runtime image.
-   [x] Report final image size (20.3MB, after the `nginx:1.27-alpine-slim` optimization below — `docs/evidence/milestone-6/image-sizes.txt`).
-   [x] Target frontend image around 60 MB or less. **Met**: initial
    measurement was 74.5MB (~24% over, driven by `nginx:1.27-alpine`'s
    bundled dynamic modules — geoip/image-filter/njs/xslt — that
    `frontend/nginx.conf` never uses). Swapped the runtime base to the
    official `nginx:1.27-alpine-slim` tag (no other Dockerfile/nginx.conf
    change); rebuilt at 20.3MB. Verified nginx still starts, config test
    passes, `HEALTHCHECK`'s `wget` binary is present and healthy, and the
    full `docker compose` stack reaches `healthy` on all four services.
    See `docs/evidence/milestone-6/image-sizes.txt`.

### Build Context

-   [x] Add backend `.dockerignore`.
-   [x] Add frontend `.dockerignore`.
-   [x] Exclude `.git`.
-   [x] Exclude `node_modules`.
-   [x] Exclude `.venv`.
-   [x] Exclude `__pycache__`.
-   [x] Exclude `.env`.
-   [x] Exclude test fixtures where appropriate.
-   [x] Measure build-context size before (with `.dockerignore` present).
-   [x] Measure build-context size after (temporarily renamed away —
    backend 589.3kB → 143.8MB, frontend 187.9kB → 156.1MB; see
    `docs/evidence/milestone-6/build-context.txt`).

## 12. Docker Compose

-   [x] Create `compose.yaml`.
-   [x] Create `compose.prod.yaml`.
-   [x] Configure frontend service.
-   [x] Configure backend service.
-   [x] Configure PostgreSQL service.
-   [x] Configure Redis service.
-   [x] Create a dedicated `migrate` Compose service for Alembic migrations (never run from backend startup).
-   [x] Use `edge` network.
-   [x] Use `internal` network.
-   [x] Set `internal: true`.
-   [x] Put frontend on `edge` only (confirmed via `docker inspect`).
-   [x] Put backend on both networks.
-   [x] Put database on `internal` only (confirmed via `docker inspect`).
-   [x] Put cache on `internal` only.
-   [x] Verify frontend cannot reach database (DNS-level isolation confirmed — `docs/evidence/milestone-6/frontend-db-isolation.txt`).
-   [ ] Resolve hosted-LLM outbound-network requirements. (backend sits on
    `edge`+`internal`, giving it outbound routing; not re-verified this
    pass with a live outbound call to the hosted LLM API.)
-   [x] Create `pgdata` volume.
-   [x] Create `redisdata` volume.
-   [x] Justify all volumes (`docs/evidence/milestone-6/volumes-and-scope.txt` — 2 volumes is 100% compliance under the hosted-LLM/no-Ollama architecture).
-   [x] Use dev bind mounts where appropriate (`backend/app` hot-reload mount in `compose.yaml`).
-   [x] Exclude dev bind mounts from production (confirmed: `compose.prod.yaml` has no bind mounts).
-   [x] Add healthchecks to every service (all 4 long-running services reach `healthy`; fixed a real bug in the frontend `HEALTHCHECK` this pass — see `docs/progress.md` M6 addendum).
-   [x] Use `depends_on: service_healthy`.
-   [x] Load credentials from `.env`.
-   [x] Commit `.env.example`.
-   [x] Keep `.env` ignored.
-   [x] Pin image tags (`postgres:16-alpine`, `redis:7-alpine`; prod backend/frontend pinned via required `${IMAGE_TAG}`, never `latest`).
-   [x] Use `restart: unless-stopped`.
-   [x] Set resource limits (`deploy.resources.limits` on every service).
-   [x] Avoid DB/cache ports in production (confirmed: no `ports:` on `postgres`/`redis` in `compose.prod.yaml`).
-   [x] Use `image: ${IMAGE_TAG}` in production.
-   [x] Ensure production Compose has no `build:` keys.
-   [x] Verify `docker compose down` preserves PostgreSQL data (real row survived a full `down`/`up -d` cycle — `docs/evidence/milestone-6/postgres-persistence.txt`).

## 13. Kubernetes Base

> Milestone 7 status: every manifest below is written and passes `scripts/k8s/validate-manifests.sh` (kustomize build + kubeconform + invariants). The live k3d deploy has been run and verified (`docs/progress.md`). Rolling-update-under-load evidence was captured in Milestone 8 (§14).

-   [x] Use k3d (architecture decision — not kind; built-in Traefik).
-   [x] Set up Kustomize.
-   [x] Create `k8s/base`.
-   [x] Create `k8s/overlays/dev`.
-   [x] Create `k8s/overlays/prod`.
-   [x] Create `civicpulse` namespace.
-   [x] Deploy backend with at least 2 replicas.
-   [x] Deploy frontend with at least 2 replicas.
-   [x] Deploy PostgreSQL as StatefulSet.
-   [x] Add PostgreSQL PVC via `volumeClaimTemplates`.
-   [x] Deploy Redis.
-   [x] Use `strategy: Recreate` for the Redis Deployment (RWO PVC would deadlock a RollingUpdate).
-   [x] Add Redis PVC.
-   [x] Create `migrate` Kubernetes `Job` for migrations (never an `initContainer`); must reach `Complete` before the app receives traffic. (verified live: `deploy.sh` waited for `Complete` before the rollouts)
-   [x] Create four ClusterIP services.
-   [x] Keep database away from NodePort/LoadBalancer.
-   [x] Create Ingress.
-   [x] Route `/` to frontend.
-   [x] Route `/api` to backend.
-   [x] Use one host.
-   [x] Create ConfigMap.
-   [x] Create Secret.
-   [x] Keep secrets out of committed manifests.
-   [x] Commit placeholders only.

## 14. Kubernetes Probes and Updates

-   [x] Add startup probe.
-   [x] Use `/health` for startup probe.
-   [x] Add liveness probe.
-   [x] Keep liveness independent of database.
-   [x] Add readiness probe.
-   [x] Use `/ready` for readiness.
-   [x] Make readiness depend on dependencies.
-   [x] Configure `maxSurge: 1`.
-   [x] Configure `maxUnavailable: 0`.
-   [x] Set termination grace period.
-   [x] Add `preStop` sleep.
-   [x] Demonstrate rolling update. (`kubectl set image` on all replicas mid-k6-run — `load/results/k6-rollout-*`, `docs/ENGINEERING-NOTES.md` M8)
-   [x] Test zero failed requests under load. (0.00% `http_req_failed` over 36,294 requests — `load/results/k6-rollout-summary.json`)

## 15. Kubernetes Resources and HPA

-   [x] Set CPU requests on every container.
-   [x] Set CPU limits on every container.
-   [x] Set memory requests/limits as appropriate.
-   [x] Install metrics-server. (k3d ships it built in; HPA read live CPU — `docs/progress.md` M8)
-   [x] Create HPA v2 for backend. (`k8s/base/hpa.yaml`, `autoscaling/v2`)
-   [x] Set minimum replicas to 2.
-   [x] Set maximum replicas to 10.
-   [x] Target 60% CPU utilization.
-   [x] Configure immediate scale-up. (`scaleUp.stabilizationWindowSeconds: 0`)
-   [x] Configure 300-second scale-down stabilization. (`scaleDown.stabilizationWindowSeconds: 300`; measured at 296s in the live run)
-   [x] Generate load with k6 or hey. (`load/k6-script.js`)
-   [x] Capture `kubectl get hpa -w`. (`load/results/hpa-watch.log`, `hpa-watch-2.log`)
-   [x] Create replicas-vs-load chart. (`load/results/hpa-run1-replicas-vs-load.png`, `hpa-run2-…png`)
-   [x] Measure HPA response lag. (`docs/ENGINEERING-NOTES.md` Q5)
-   [x] Explain the observed lag. (`docs/ENGINEERING-NOTES.md` Q5)

## 16. Kubernetes VPA

-   [x] Install Vertical Pod Autoscaler. (Helm chart `cowboysysop/vertical-pod-autoscaler` into `kube-system` — `docs/progress.md` M8)
-   [x] Configure backend VPA. (`k8s/base/vpa.yaml`)
-   [x] Set `updateMode: Off`.
-   [x] Run the load test.
-   [x] Capture VPA recommendations. (`docs/ENGINEERING-NOTES.md` M8)
-   [x] Commit Target recommendation. (cpu 296m / memory 250Mi)
-   [x] Commit Lower Bound recommendation. (cpu 106m / memory 250Mi)
-   [x] Commit Upper Bound recommendation. (cpu 25517m — very wide because of the short observation window, noted as such)
-   [x] Update resource requests. (`k8s/base/backend.yaml` now 300m/256Mi requests)
-   [x] Re-run load test. (Run 2 — HPA topped out at 9/10 with CPU at 30–50%)
-   [x] Compare HPA behavior. (Run 1 vs Run 2 in `docs/ENGINEERING-NOTES.md` M8)
-   [x] Explain why VPA remains in Off mode. (Q6)
-   [x] Explain HPA/VPA resource-request conflict. (Q6)

## 17. CI Workflow

> `.github/workflows/ci.yml` contains every job in the spec (`lint-and-type`, `test-backend`, `test-frontend`, `build`, `scan`, `manifests`, `integration`). Ticked = the step is in the file. Whether the latest run is green on GitHub can't be checked from here.

-   [x] Create `.github/workflows/ci.yml`.
-   [x] Run CI on PRs to `main`.
-   [x] Run CI on pushes to `dev`.
-   [x] Run Ruff.
-   [x] Run mypy.
-   [x] Run ESLint. (the project linter is oxlint (`npm run lint`); the assignment says eslint — same job (`lint-and-type`), different tool)
-   [x] Run TypeScript checks.
-   [x] Run backend tests.
-   [x] Require backend coverage ≥65%.
-   [x] Set `TRIAGE_PROVIDER=simulated`.
-   [x] Run frontend tests.
-   [x] Build both images.
-   [x] Do not push images from PR CI.
-   [x] Run Trivy on both images.
-   [x] Fail on HIGH/CRITICAL vulnerabilities.
-   [x] Validate production Kustomize output.
-   [x] Run kubeconform.
-   [x] Run Compose integration test.
-   [x] Wait for `/ready`.
-   [x] POST a complaint.
-   [x] GET the complaint back.
-   [x] Verify category. (asserts the exact value `streetlights` on both the POST and GET responses (deterministic under simulated triage))
-   [x] Verify cache MISS → HIT. (first `/api/stats` read must be `MISS` (the POST invalidates the cache), second must be `HIT`; both are hard failures)
-   [x] Run `docker compose down -v`.

## 18. CD Workflow

> `.github/workflows/cd.yml` has `test` → `build-push` → `deploy-k8s`, chained with `needs:`. No successful run is confirmed: the two most recent CD commits (`116c4d6`, `b939a41`) are crash fixes. The submission needs a green run link (§29).

-   [x] Create `.github/workflows/cd.yml`.
-   [x] Trigger on pushes to `main`.
-   [x] Run full test suite.
-   [x] Gate publishing with `needs`.
-   [x] Build backend image.
-   [x] Build frontend image.
-   [x] Push images to GHCR.
-   [x] Tag images with commit SHA.
-   [x] Also push `latest`.
-   [x] Generate SBOM with Syft.
-   [x] Capture image digest.
-   [x] Create ephemeral kind/k3d cluster.
-   [x] Deploy production overlay.
-   [x] Deploy using SHA tag.
-   [x] Wait for rollout status.
-   [x] Smoke-test Ingress.
-   [x] Print HPA status.
-   [x] Never deploy `latest`.

## 19. Release Workflow

-   [x] Create `.github/workflows/release.yml`.
-   [x] Trigger on `v*` tags.
-   [x] Build release images.
-   [x] Push semver tags. (tag is `github.ref_name`, so `v1.2.3` (v-prefixed))
-   [x] Gate `release.yml` publishing with `needs:` on a test job. (`release.yml` `test` job reuses `ci.yml`; `build-push-release` has `needs: test`)
-   [x] Generate release notes.

## 20. CI/CD Security

-   [x] Store credentials in GitHub Secrets. (workflow side done (`cd.yml`); populating the repo secrets is manual)
-   [x] Use scoped registry token. (`GITHUB_TOKEN`)
-   [x] Prefer `GITHUB_TOKEN`. (used for GHCR login and the cluster pull secret; no PAT anywhere)
-   [x] Grant only required permissions. (`ci.yml` read-only; `cd.yml` adds `packages: write`; `release.yml` adds `contents: write`)
-   [x] Add workflow permissions blocks. (all three workflows)
-   [x] Pin GitHub Actions to at least `@v4`. (all `@v4`+ or a full version tag (`anchore/sbom-action@v0.24.2`, `softprops/action-gh-release@v3.0.3`); k3d installer pinned to `v5.9.0`. Enforced by `scripts/check_submission.py`)
-   [ ] Optionally pin actions to commit SHA.
-   [x] Verify no credentials exist in Git history. (pattern scan of `git log --all -p` this session: `.env` never tracked, no `gsk_…`, `LLM_API_KEY=<value>` or AWS-key strings. A regex scan, not a proof — re-run before submitting)
-   [ ] Create a deliberately failing PR.
-   [ ] Capture red CI evidence.
-   [ ] Verify merge is blocked.
-   [ ] Fix the failure.
-   [ ] Capture green CI evidence.

## 21. Rollback

-   [ ] Demonstrate `kubectl rollout undo`. (procedure documented in `docs/CI-CD-SETUP.md` §5.1; never run/recorded)
-   [ ] Demonstrate rollback using previous overlay/SHA. (procedure documented in `docs/CI-CD-SETUP.md` §5.2 (`deploy.sh prod <old-sha>`); never run/recorded)
-   [x] Explain imperative rollback. (`docs/CI-CD-SETUP.md` §5.1)
-   [x] Explain declarative rollback. (`docs/CI-CD-SETUP.md` §5.2)

## 22. Collaboration Requirements

-   [ ] Use `dev` plus feature branches. (`dev` and one feature branch (`feature/m6-docker-verification`) exist, but most commits go straight to `main`/`dev`)
-   [ ] Avoid direct commits to `main`. (5 non-merge commits sit directly on `main`'s first-parent line: `b7d14a7`, `116c4d6`, `6c3ae4e`, `f76477e`, `b939a41` (§5.3: −5). Use branch + PR from here on)
-   [ ] Merge at least 5 PRs. (`git log` shows about 3–4 `Merge PR | …` merges (`df23618`, `e0cfaa4`, `51193be`, `d812c6a`). PR and Issue counts can't be checked without `gh`)
-   [ ] Link each PR to an Issue.
-   [ ] Add substantive partner review comments.
-   [ ] Make at least 35 commits per required assignment threshold. (31 on `main` HEAD (32 across all branches))
-   [x] Use conventional commit prefixes. (`feat:`, `docs:`, `fix:` observed in `git log`)
-   [x] Keep both partners above required contribution threshold. (`git shortlog -sn HEAD` now shows Asad Ahmed 19, tawassulAkbr 12 = 38.7% (`.mailmap` added); margin is thin, so re-check at submission)
-   [x] Add a `.mailmap` so `asad` and `Asad Ahmed` show as one line in `git shortlog -sn`. (`.mailmap` at the repo root)
-   [ ] Create one deliberate merge conflict.
-   [ ] Resolve the conflict.
-   [ ] Preserve conflict evidence.
-   [ ] Explain why the chosen version won.

## 23. Documentation

-   [x] Write problem statement in README.
-   [x] Add badges. (CI, CD, Release, license badges at the top of `README.md`)
-   [x] Add Mermaid architecture diagram. (`README.md` Architecture section)
-   [x] Add one-command quickstart. (`cp .env.example .env && docker compose up --build` is now the README headline; not yet verified from a truly clean clone (see §27))
-   [x] Add API table. (`README.md` API section (all 9 endpoints, status codes))
-   [ ] Add screenshots. (placeholder section in `README.md`; images still to be captured under `docs/evidence/screenshots/`)
-   [x] Create provider-interface ADR. (0001)
-   [x] Create frontend-runtime-config ADR. (0002)
-   [x] Create deploy-by-SHA ADR. (0003)
-   [x] Create PII/data-governance ADR. (0004)
-   [x] Create `docs/RUNBOOK.md`. (deploy, rollback, log reading, triage-failure response)
-   [x] Document deployment. (`docs/RUNBOOK.md` §1)
-   [x] Document rollback. (`docs/RUNBOOK.md` §2)
-   [x] Document log inspection. (`docs/RUNBOOK.md` §3)
-   [x] Document triage failure response. (`docs/RUNBOOK.md` §4)
-   [x] Create `docs/ENGINEERING-NOTES.md`.
-   [x] Answer all 8 engineering questions. (Q1–Q4, Q7, Q8 added under "Milestone 9/10"; Q5/Q6 under Milestone 8. Q2 (ladder wording) and Q8 (time cost) are drafts for the authors to confirm)
-   [x] Reference exact files and lines. (Q1–Q4, Q7, Q8 cite `file:line`; re-check line numbers if those files change)
-   [x] Create `docs/AI-USAGE.md`. (exists; contains **[AUTHORS TO COMPLETE]** sections)
-   [x] Document AI tools used. (Claude Code and Impeccable named; the partner's tools still to be filled in)
-   [x] Document AI-generated contributions.
-   [ ] Document your changes and reasoning. (table of corrections found is written; the authors' own hand-made changes and reasoning still need adding)
-   [x] Create `docs/TRIAGE.md`.

## 24. Evidence

-   [ ] Capture branch protection evidence.
-   [ ] Capture merge-conflict evidence.
-   [ ] Capture blocked-merge evidence.
-   [ ] Capture successful CI evidence.
-   [x] Capture HPA `-w` output. (`load/results/hpa-watch*.log` (assignment wants it referenced from `docs/evidence/`))
-   [x] Capture scaling chart. (`load/results/hpa-run{1,2}-replicas-vs-load.png`)
-   [x] Capture network-isolation failure. (`docs/evidence/milestone-6/frontend-db-isolation.txt`)
-   [x] Capture database persistence. (`docs/evidence/milestone-6/postgres-persistence.txt`)
-   [ ] Capture Kubernetes persistence. (verified live (`docs/progress.md` M7) but no output file committed under `docs/evidence/`)
-   [ ] Capture fallback behavior.
-   [ ] Capture cache MISS → HIT.
-   [x] Capture rolling-update behavior. (`load/results/k6-rollout-{output.log,summary.json}`)
-   [ ] Capture rollback.
-   [ ] Store evidence in `docs/evidence/`. (`docs/evidence/README.md` now indexes every artifact and lists what's still to capture; HPA/k6 files stay under `load/results/`)

## 25. Demo

-   [ ] Keep demo at or below 5 minutes.
-   [ ] Have both partners speak.
-   [ ] Start from a clean clone.
-   [ ] Show one-command startup.
-   [ ] Show complaint submission.
-   [ ] Show AI triage.
-   [ ] Show fallback.
-   [ ] Show dashboard.
-   [ ] Show network isolation.
-   [ ] Show HPA scaling.
-   [ ] Show rollback.

## 26. Engineering Notes

-   [x] Explain laptop vs CI differences. (Q1)
-   [x] Identify lines freezing those differences. (Q1, with file:line for each; also records that the backend image is not installed from `uv.lock`)
-   [x] Identify CI/CD maturity level. (Q2 (continuous delivery, no persistent prod) — align rung names with Lecture 03 slide 32)
-   [x] Justify the maturity level. (Q2)
-   [x] Name the next maturity level. (Q2)
-   [x] Explain what the next level provides. (Q2)
-   [x] Identify build-once-deploy-many line. (Q3 (`cd.yml:55,67,97,154`, `frontend/nginx.conf:38-39`))
-   [x] Explain what breaks without it. (Q3)
-   [x] Define correctness for probabilistic LLM behavior. (Q4)
-   [x] Explain deterministic CI. (Q4)
-   [x] Measure HPA load-to-scale lag. (Q5)
-   [x] Explain where HPA lag comes from. (Q5)
-   [x] Explain how to reduce HPA lag. (Q5)
-   [x] Explain VPA Off mode. (Q6)
-   [x] Explain HPA/VPA conflict. (Q6)
-   [x] Explain `internal: true` implications. (Q7)
-   [x] Explain hosted-LLM networking solution. (Q7; no recorded live Groq call, stated as such)
-   [x] Document the biggest failure encountered. (Q8 (draft — authors confirm))
-   [x] Document initial incorrect assumption. (Q8 (draft — authors confirm))
-   [x] Document the command/log that revealed the cause. (Q8)

## 27. Pre-Submission Safety Checks

-   [x] Run `python scripts/check_submission.py`. (exists and runs: 22 pass, 0 fail, 3 warn (direct commits to `main`, 31/35 commits, no screenshots). Re-run before submitting)
-   [x] Remove all secrets from Git history. (nothing found (see §20 scan))
-   [x] Rotate any exposed credentials. (n/a — no exposure found. Rotate immediately if a key is ever pasted into a commit)
-   [x] Remove API keys from Kubernetes manifests. (`k8s/base/secret.yaml` holds `REPLACE_ME` only, and both overlays delete it)
-   [x] Pin all base images. (`python:3.12-slim`, `node:22-alpine`, `nginx:1.27-alpine-slim`, `postgres:16-alpine`, `redis:7-alpine` — all tagged (digest pin optional))
-   [x] Avoid `localhost` for service-to-service calls. (Compose and k8s use `postgres`/`redis` service names; `localhost` appears only as local-dev defaults in `backend/app/core/config.py`)
-   [x] Verify frontend cannot reach database. (`docs/evidence/milestone-6/frontend-db-isolation.txt`)
-   [x] Verify production DB/cache ports are unpublished. (`compose.prod.yaml` has no `ports:` on postgres/redis; k8s data Services are ClusterIP)
-   [x] Verify publishing jobs use `needs`. (`cd.yml` and `release.yml`; checked by `scripts/check_submission.py`)
-   [x] Verify deployment never uses `latest`. (`scripts/k8s/deploy.sh` rejects `latest`; `cd.yml` deploys `${{ github.sha }}`)
-   [x] Verify PostgreSQL uses StatefulSet + PVC. (`k8s/base/postgres.yaml`, enforced by `check_manifest_invariants.py`)
-   [ ] Verify README works from clean clone.
-   [ ] Verify no direct commits to `main`. (currently false — see §22)

## 28. Optional Bonus

-   [x] Demonstrate zero-downtime rolling update under live load. (+4 — 0.00% failed of 36,294 requests, `load/results/k6-rollout-summary.json`)
-   [ ] Add Argo CD or Flux GitOps. (+4)
-   [ ] Deploy by image digest. (+3)
-   [ ] Sign images with Cosign. (+3)
-   [ ] Verify image signatures in CI. (+3)
-   [ ] Add Prometheus scraping. (+2)
-   [ ] Add Grafana dashboard. (+2)
-   [ ] Add OpenTelemetry tracing. (+2)

## 29. Final Submission

-   [ ] Submit GitHub repository URL.
-   [ ] Add instructors if repository is private.
-   [ ] Submit successful `cd.yml` run link.
-   [ ] Submit both GHCR image links.
-   [ ] Show SHA-tagged images.
-   [ ] Submit unlisted demo video.
-   [ ] Submit `git shortlog -sn` output.
-   [ ] Submit HPA `kubectl get hpa -w` capture. (capture exists (`load/results/hpa-watch.log`); still to submit)
-   [ ] Submit replicas-vs-load chart. (chart exists (`load/results/hpa-run*-replicas-vs-load.png`); still to submit)
-   [ ] Run final submission checker.
-   [ ] Verify all required evidence is committed.
