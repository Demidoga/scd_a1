# CivicPulse --- Comprehensive Assignment Checklist

## 0. Project Setup

-   [x] Create GitHub repository.
-   [ ] Add both team members.
-   [x] Create `main` and `dev` branches.
-   [ ] Protect `main`.
-   [ ] Require PRs for `main`.
-   [ ] Require CI checks for `main`.
-   [ ] Require at least one approval.
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

-   [ ] Set up PostgreSQL 16. (local dev sandbox runs 17; `postgres:16` is pinned only in the not-yet-built Compose/K8s artifacts — documented gap in `docs/ENGINEERING-NOTES.md`)
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
-   [ ] Verify seed runs twice without duplicates. (idempotency check exists in code, not demonstrated/tested)
-   [ ] Verify Compose restart preserves data.
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

-   [ ] Set up Redis 7. (local dev sandbox runs 8; version is pinned only in the not-yet-built Compose/K8s artifacts)
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
-   [ ] Store CI credentials in GitHub Secrets.
-   [x] Treat complaint text as untrusted data.
-   [x] Add prompt-injection guardrail.
-   [x] Add prompt-injection test.
-   [ ] Configure CI to use `SimulatedTriage`. (default is already `simulated`; no CI workflow exists yet to consume it)
-   [x] Add provider failure injection.
-   [x] Test fallback using a failing provider.
-   [x] Test malformed output handling.

## 8. Frontend

-   [ ] Set up React 18. (`frontend/package.json` pins React 19.2, not 18 — flag against `CLAUDE.md`/architecture stack choice)
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
-   [ ] Make one frontend image usable across environments. (no frontend Docker image yet)
-   [x] Document the choice in an ADR. (ADR 0002)
-   [x] Verify runtime configuration in dev.
-   [ ] Verify runtime configuration in production.

## 10. Frontend Testing

-   [x] Set up Vitest.
-   [x] Write at least 5 meaningful component tests. (8)
-   [x] Test submission validation.
-   [x] Test loading state.
-   [x] Test complaint rendering.
-   [x] Test dashboard filtering/pagination.
-   [x] Test `409` error display.
-   [x] Test stats/cache indicator.
-   [ ] Run frontend tests in CI.

## 11. Docker Images

### Backend

-   [ ] Use `python:3.12-slim`.
-   [ ] Use multi-stage build.
-   [ ] Install dependencies in builder stage.
-   [ ] Optimize COPY order.
-   [ ] Create non-root user.
-   [ ] Use exec-form `CMD`.
-   [ ] Add Docker `HEALTHCHECK`.
-   [ ] Pin image versions.
-   [ ] Optionally pin base images by digest.

### Frontend

-   [ ] Use `node:22-alpine` build stage.
-   [ ] Use `nginx:1.27-alpine` runtime stage.
-   [ ] Exclude Node from final image.
-   [ ] Exclude `node_modules` from final image.
-   [ ] Exclude source from final runtime image.
-   [ ] Report final image size.
-   [ ] Target frontend image around 60 MB or less.

### Build Context

-   [ ] Add backend `.dockerignore`.
-   [ ] Add frontend `.dockerignore`.
-   [ ] Exclude `.git`.
-   [ ] Exclude `node_modules`.
-   [ ] Exclude `.venv`.
-   [ ] Exclude `__pycache__`.
-   [ ] Exclude `.env`.
-   [ ] Exclude test fixtures where appropriate.
-   [ ] Measure build-context size before.
-   [ ] Measure build-context size after.

## 12. Docker Compose

-   [ ] Create `compose.yaml`.
-   [ ] Create `compose.prod.yaml`.
-   [ ] Configure frontend service.
-   [ ] Configure backend service.
-   [ ] Configure PostgreSQL service.
-   [ ] Configure Redis service.
-   [ ] Create a dedicated `migrate` Compose service for Alembic migrations (never run from backend startup).
-   [ ] Use `edge` network.
-   [ ] Use `internal` network.
-   [ ] Set `internal: true`.
-   [ ] Put frontend on `edge` only.
-   [ ] Put backend on both networks.
-   [ ] Put database on `internal` only.
-   [ ] Put cache on `internal` only.
-   [ ] Verify frontend cannot reach database.
-   [ ] Resolve hosted-LLM outbound-network requirements.
-   [ ] Create `pgdata` volume.
-   [ ] Create `redisdata` volume.
-   [ ] Justify all volumes.
-   [ ] Use dev bind mounts where appropriate.
-   [ ] Exclude dev bind mounts from production.
-   [ ] Add healthchecks to every service.
-   [ ] Use `depends_on: service_healthy`.
-   [ ] Load credentials from `.env`.
-   [x] Commit `.env.example`.
-   [x] Keep `.env` ignored.
-   [ ] Pin image tags.
-   [ ] Use `restart: unless-stopped`.
-   [ ] Set resource limits.
-   [ ] Avoid DB/cache ports in production.
-   [ ] Use `image: ${IMAGE_TAG}` in production.
-   [ ] Ensure production Compose has no `build:` keys.
-   [ ] Verify `docker compose down` preserves PostgreSQL data.

## 13. Kubernetes Base

> Milestone 7 status: every manifest below is written and passes `scripts/k8s/validate-manifests.sh` (kustomize build + kubeconform + invariants). The live k3d deploy has been run and verified (`docs/progress.md`). Rolling-update-under-load evidence belongs to Milestone 8.

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
-   [ ] Demonstrate rolling update.
-   [ ] Test zero failed requests under load.

## 15. Kubernetes Resources and HPA

-   [x] Set CPU requests on every container.
-   [x] Set CPU limits on every container.
-   [x] Set memory requests/limits as appropriate.
-   [ ] Install metrics-server.
-   [ ] Create HPA v2 for backend.
-   [ ] Set minimum replicas to 2.
-   [ ] Set maximum replicas to 10.
-   [ ] Target 60% CPU utilization.
-   [ ] Configure immediate scale-up.
-   [ ] Configure 300-second scale-down stabilization.
-   [ ] Generate load with k6 or hey.
-   [ ] Capture `kubectl get hpa -w`.
-   [ ] Create replicas-vs-load chart.
-   [ ] Measure HPA response lag.
-   [ ] Explain the observed lag.

## 16. Kubernetes VPA

-   [ ] Install Vertical Pod Autoscaler.
-   [ ] Configure backend VPA.
-   [ ] Set `updateMode: Off`.
-   [ ] Run the load test.
-   [ ] Capture VPA recommendations.
-   [ ] Commit Target recommendation.
-   [ ] Commit Lower Bound recommendation.
-   [ ] Commit Upper Bound recommendation.
-   [ ] Update resource requests.
-   [ ] Re-run load test.
-   [ ] Compare HPA behavior.
-   [ ] Explain why VPA remains in Off mode.
-   [ ] Explain HPA/VPA resource-request conflict.

## 17. CI Workflow

-   [ ] Create `.github/workflows/ci.yml`.
-   [ ] Run CI on PRs to `main`.
-   [ ] Run CI on pushes to `dev`.
-   [ ] Run Ruff.
-   [ ] Run mypy.
-   [ ] Run ESLint.
-   [ ] Run TypeScript checks.
-   [ ] Run backend tests.
-   [ ] Require backend coverage ≥65%.
-   [ ] Set `TRIAGE_PROVIDER=simulated`.
-   [ ] Run frontend tests.
-   [ ] Build both images.
-   [ ] Do not push images from PR CI.
-   [ ] Run Trivy on both images.
-   [ ] Fail on HIGH/CRITICAL vulnerabilities.
-   [ ] Validate production Kustomize output.
-   [ ] Run kubeconform.
-   [ ] Run Compose integration test.
-   [ ] Wait for `/ready`.
-   [ ] POST a complaint.
-   [ ] GET the complaint back.
-   [ ] Verify category.
-   [ ] Verify cache MISS → HIT.
-   [ ] Run `docker compose down -v`.

## 18. CD Workflow

-   [ ] Create `.github/workflows/cd.yml`.
-   [ ] Trigger on pushes to `main`.
-   [ ] Run full test suite.
-   [ ] Gate publishing with `needs`.
-   [ ] Build backend image.
-   [ ] Build frontend image.
-   [ ] Push images to GHCR.
-   [ ] Tag images with commit SHA.
-   [ ] Also push `latest`.
-   [ ] Generate SBOM with Syft.
-   [ ] Capture image digest.
-   [ ] Create ephemeral kind/k3d cluster.
-   [ ] Deploy production overlay.
-   [ ] Deploy using SHA tag.
-   [ ] Wait for rollout status.
-   [ ] Smoke-test Ingress.
-   [ ] Print HPA status.
-   [ ] Never deploy `latest`.

## 19. Release Workflow

-   [ ] Create `.github/workflows/release.yml`.
-   [ ] Trigger on `v*` tags.
-   [ ] Build release images.
-   [ ] Push semver tags.
-   [ ] Generate release notes.

## 20. CI/CD Security

-   [ ] Store credentials in GitHub Secrets.
-   [ ] Use scoped registry token.
-   [ ] Prefer `GITHUB_TOKEN`.
-   [ ] Grant only required permissions.
-   [ ] Add workflow permissions blocks.
-   [ ] Pin GitHub Actions to at least `@v4`.
-   [ ] Optionally pin actions to commit SHA.
-   [ ] Verify no credentials exist in Git history.
-   [ ] Create a deliberately failing PR.
-   [ ] Capture red CI evidence.
-   [ ] Verify merge is blocked.
-   [ ] Fix the failure.
-   [ ] Capture green CI evidence.

## 21. Rollback

-   [ ] Demonstrate `kubectl rollout undo`.
-   [ ] Demonstrate rollback using previous overlay/SHA.
-   [ ] Explain imperative rollback.
-   [ ] Explain declarative rollback.

## 22. Collaboration Requirements

-   [ ] Use `dev` plus feature branches. (`dev` exists and diverges from `main`; no feature branches used — work committed straight to `dev`)
-   [ ] Avoid direct commits to `main`.
-   [ ] Merge at least 5 PRs. (0 PRs so far — all 4 commits are direct pushes, no merge commits)
-   [ ] Link each PR to an Issue.
-   [ ] Add substantive partner review comments.
-   [ ] Make at least 35 commits per required assignment threshold. (4 commits so far)
-   [x] Use conventional commit prefixes. (`feat:`, `docs:`, `fix:` observed in `git log`)
-   [ ] Keep both partners above required contribution threshold. (only one contributor, "asad", in `git shortlog` so far)
-   [ ] Create one deliberate merge conflict.
-   [ ] Resolve the conflict.
-   [ ] Preserve conflict evidence.
-   [ ] Explain why the chosen version won.

## 23. Documentation

-   [x] Write problem statement in README.
-   [ ] Add badges.
-   [ ] Add Mermaid architecture diagram. (only in `docs/architecture.md`, not README)
-   [ ] Add one-command quickstart. (current quickstart is multi-step `uv`/manual DB setup — one-command needs Compose)
-   [ ] Add API table.
-   [ ] Add screenshots.
-   [x] Create provider-interface ADR. (0001)
-   [x] Create frontend-runtime-config ADR. (0002)
-   [x] Create deploy-by-SHA ADR. (0003)
-   [x] Create PII/data-governance ADR. (0004)
-   [ ] Create `docs/RUNBOOK.md`. (does not exist)
-   [ ] Document deployment.
-   [ ] Document rollback.
-   [ ] Document log inspection.
-   [ ] Document triage failure response.
-   [x] Create `docs/ENGINEERING-NOTES.md`.
-   [ ] Answer all 8 engineering questions. (notes are organized per-milestone; several questions need CI/CD/K8s/HPA evidence that doesn't exist yet)
-   [ ] Reference exact files and lines.
-   [ ] Create `docs/AI-USAGE.md`. (does not exist)
-   [ ] Document AI tools used.
-   [ ] Document AI-generated contributions.
-   [ ] Document your changes and reasoning.
-   [x] Create `docs/TRIAGE.md`.

## 24. Evidence

-   [ ] Capture branch protection evidence.
-   [ ] Capture merge-conflict evidence.
-   [ ] Capture blocked-merge evidence.
-   [ ] Capture successful CI evidence.
-   [ ] Capture HPA `-w` output.
-   [ ] Capture scaling chart.
-   [ ] Capture network-isolation failure.
-   [ ] Capture database persistence.
-   [ ] Capture Kubernetes persistence.
-   [ ] Capture fallback behavior.
-   [ ] Capture cache MISS → HIT.
-   [ ] Capture rolling-update behavior.
-   [ ] Capture rollback.
-   [ ] Store evidence in `docs/evidence/`.

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

-   [ ] Explain laptop vs CI differences. (Postgres 17-vs-16 dev/prod gap is noted; full laptop/CI framing not written)
-   [ ] Identify lines freezing those differences. (target line named but doesn't exist yet — Milestone 6 artifact)
-   [ ] Identify CI/CD maturity level.
-   [ ] Justify the maturity level.
-   [ ] Name the next maturity level.
-   [ ] Explain what the next level provides.
-   [ ] Identify build-once-deploy-many line.
-   [ ] Explain what breaks without it.
-   [ ] Define correctness for probabilistic LLM behavior.
-   [ ] Explain deterministic CI.
-   [ ] Measure HPA load-to-scale lag.
-   [ ] Explain where HPA lag comes from.
-   [ ] Explain how to reduce HPA lag.
-   [ ] Explain VPA Off mode.
-   [ ] Explain HPA/VPA conflict.
-   [ ] Explain `internal: true` implications. (recorded as a decision in `docs/ENGINEERING-NOTES.md`, not yet built)
-   [ ] Explain hosted-LLM networking solution. (same — decided, not built)
-   [ ] Document the biggest failure encountered.
-   [ ] Document initial incorrect assumption.
-   [ ] Document the command/log that revealed the cause.

## 27. Pre-Submission Safety Checks

-   [ ] Run `python scripts/check_submission.py`. (script does not exist yet)
-   [ ] Remove all secrets from Git history.
-   [ ] Rotate any exposed credentials.
-   [ ] Remove API keys from Kubernetes manifests.
-   [ ] Pin all base images.
-   [ ] Avoid `localhost` for service-to-service calls.
-   [ ] Verify frontend cannot reach database.
-   [ ] Verify production DB/cache ports are unpublished.
-   [ ] Verify publishing jobs use `needs`.
-   [ ] Verify deployment never uses `latest`.
-   [ ] Verify PostgreSQL uses StatefulSet + PVC.
-   [ ] Verify README works from clean clone.
-   [ ] Verify no direct commits to `main`. (currently false — the initial commit is direct on `main`)

## 28. Optional Bonus

-   [ ] Demonstrate zero-downtime rolling update under live load. (+4)
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
-   [ ] Submit HPA `kubectl get hpa -w` capture.
-   [ ] Submit replicas-vs-load chart.
-   [ ] Run final submission checker.
-   [ ] Verify all required evidence is committed.
