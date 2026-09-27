# CivicPulse --- Comprehensive Assignment Checklist

## 0. Project Setup

-   [ ] Create GitHub repository.
-   [ ] Add both team members.
-   [ ] Create `main` and `dev` branches.
-   [ ] Protect `main`.
-   [ ] Require PRs for `main`.
-   [ ] Require CI checks for `main`.
-   [ ] Require at least one approval.
-   [ ] Create initial repository structure.
-   [ ] Add `.gitignore`.
-   [ ] Add `.env.example`.
-   [ ] Ensure `.env` is ignored.
-   [ ] Create `README.md`.
-   [ ] Create `LICENSE`.

## 1. Backend Foundation

-   [ ] Set up FastAPI + Pydantic v2.
-   [ ] Create four backend layers.
-   [ ] Create `routes/`.
-   [ ] Create `services/`.
-   [ ] Create `repositories/`.
-   [ ] Create `providers/`.
-   [ ] Keep SQL inside repositories.
-   [ ] Keep business rules inside services.
-   [ ] Keep routes HTTP-only.
-   [ ] Add dependency injection.
-   [ ] Add request validation.
-   [ ] Add field-level error responses.
-   [ ] Add request ID middleware.
-   [ ] Add structured JSON logging.
-   [ ] Log to stdout.
-   [ ] Propagate `X-Request-ID`.
-   [ ] Generate request ID when absent.
-   [ ] Add graceful SIGTERM shutdown.
-   [ ] Drain in-flight requests.
-   [ ] Close database connections on shutdown.

## 2. Database

-   [ ] Set up PostgreSQL 16.
-   [ ] Set up Alembic.
-   [ ] Create initial migration.
-   [ ] Avoid startup-time DDL.
-   [ ] Create UUID primary key.
-   [ ] Enforce complaint text length 10--2000.
-   [ ] Enforce location length 3--200.
-   [ ] Add nullable reporter contact.
-   [ ] Add category enum.
-   [ ] Add priority enum.
-   [ ] Add status enum.
-   [ ] Default status to `open`.
-   [ ] Add nullable AI summary.
-   [ ] Limit AI summary to 140 characters.
-   [ ] Add `triaged_by`.
-   [ ] Add `triage_latency_ms`.
-   [ ] Add UTC timestamps.
-   [ ] Add `(status, priority)` index.
-   [ ] Add `created_at` index.
-   [ ] Document the purpose of both indexes.
-   [ ] Create idempotent seed command.
-   [ ] Seed at least 30 complaints.
-   [ ] Use Urdu-influenced English complaints.
-   [ ] Spread seed data across categories.
-   [ ] Verify seed runs twice without duplicates.
-   [ ] Verify Compose restart preserves data.
-   [ ] Verify Kubernetes Postgres pod deletion preserves data.

## 3. API

-   [ ] Implement `POST /api/complaints`.
-   [ ] Return `201` on successful creation.
-   [ ] Return `400` for validation errors.
-   [ ] Return `429` when rate limited.
-   [ ] Implement `GET /api/complaints/{id}`.
-   [ ] Return `404` for missing complaints.
-   [ ] Implement `GET /api/complaints`.
-   [ ] Add category filtering.
-   [ ] Add priority filtering.
-   [ ] Add status filtering.
-   [ ] Add pagination.
-   [ ] Enforce `page_size <= 100`.
-   [ ] Return total count.
-   [ ] Implement `PATCH /api/complaints/{id}/status`.
-   [ ] Return `409` for invalid transitions.
-   [ ] Include attempted transition in `409`.
-   [ ] Implement `GET /api/stats`.
-   [ ] Add `X-Cache` response header.
-   [ ] Implement `GET /api/meta/providers`.
-   [ ] Return active provider.
-   [ ] Return last 20 triage outcomes.
-   [ ] Include provider and latency.
-   [ ] Include fallback status.
-   [ ] Implement `GET /health`.
-   [ ] Keep `/health` independent of the database.
-   [ ] Implement `GET /ready`.
-   [ ] Check PostgreSQL in readiness.
-   [ ] Check Redis in readiness.
-   [ ] Return `503` with failed dependency when unavailable.
-   [ ] Implement `GET /metrics`.
-   [ ] Expose request count.
-   [ ] Expose request latency histogram.
-   [ ] Expose triage latency.
-   [ ] Expose fallback counter.

## 4. Complaint State Machine

-   [ ] Define explicit transition table.
-   [ ] Allow `open → in_progress`.
-   [ ] Allow `in_progress → resolved`.
-   [ ] Allow `open → rejected`.
-   [ ] Allow `in_progress → rejected`.
-   [ ] Make `resolved` terminal.
-   [ ] Make `rejected` terminal.
-   [ ] Reject all other transitions with `409`.
-   [ ] Keep transition rules out of the frontend.

## 5. Redis

-   [ ] Set up Redis 7.
-   [ ] Implement read-through stats cache.
-   [ ] Set stats TTL to 30 seconds.
-   [ ] Return `X-Cache: HIT`.
-   [ ] Return `X-Cache: MISS`.
-   [ ] Invalidate stats cache after writes.
-   [ ] Implement distributed IP rate limiting.
-   [ ] Choose fixed-window or token-bucket algorithm.
-   [ ] Key rate limits by client IP.
-   [ ] Return `429` when exceeded.
-   [ ] Return `Retry-After`.
-   [ ] Enable Redis AOF.
-   [ ] Store Redis data on named volume.
-   [ ] Document the AOF volume decision.

## 6. AI Triage

-   [ ] Create `TriageResult` Pydantic model.
-   [ ] Add category field.
-   [ ] Add priority field.
-   [ ] Add summary field.
-   [ ] Enforce summary max 140 characters.
-   [ ] Add confidence field.
-   [ ] Enforce confidence 0--1.
-   [ ] Define `TriageProvider` interface.
-   [ ] Add provider name.
-   [ ] Implement `LLMTriage`.
-   [ ] Implement `OllamaTriage`.
-   [ ] Implement `RuleBasedTriage`.
-   [ ] Implement `SimulatedTriage`.
-   [ ] Select provider using `TRIAGE_PROVIDER`.
-   [ ] Configure hosted provider.
-   [ ] Use a small instruct model.
-   [ ] Document the selected provider.
-   [ ] Document live provider limits.
-   [ ] Decide how complaint PII is handled.
-   [ ] Record PII decision in an ADR.

## 7. AI Reliability

-   [ ] Request structured JSON from the LLM.
-   [ ] Validate output with Pydantic.
-   [ ] Reject malformed output safely.
-   [ ] Reject invalid enum values.
-   [ ] Enforce 10-second timeout.
-   [ ] Retry once on timeout.
-   [ ] Retry once on `429`.
-   [ ] Retry once on `5xx`.
-   [ ] Add jitter to retry.
-   [ ] Do not retry `400`.
-   [ ] Fall back to rule-based triage.
-   [ ] Record `triaged_by = rules:fallback`.
-   [ ] Add content-hash triage cache.
-   [ ] Set triage cache TTL to 24 hours.
-   [ ] Measure triage cache hit rate.
-   [ ] Report the measured hit rate.
-   [ ] Never log API keys.
-   [ ] Load API keys from environment variables.
-   [ ] Store Kubernetes API keys in Secrets.
-   [ ] Store CI credentials in GitHub Secrets.
-   [ ] Treat complaint text as untrusted data.
-   [ ] Add prompt-injection guardrail.
-   [ ] Add prompt-injection test.
-   [ ] Configure CI to use `SimulatedTriage`.
-   [ ] Add provider failure injection.
-   [ ] Test fallback using a failing provider.
-   [ ] Test malformed output handling.

## 8. Frontend

-   [ ] Set up React 18.
-   [ ] Set up Vite.
-   [ ] Set up TypeScript.
-   [ ] Create submission view.
-   [ ] Add complaint text input.
-   [ ] Add location input.
-   [ ] Add optional contact input.
-   [ ] Add client-side validation.
-   [ ] Mirror server validation rules.
-   [ ] Add honest loading state.
-   [ ] Display returned category.
-   [ ] Display returned priority.
-   [ ] Display AI summary.
-   [ ] Display triage provider.
-   [ ] Create dashboard view.
-   [ ] Add paginated complaint list.
-   [ ] Add category filter.
-   [ ] Add priority filter.
-   [ ] Add status filter.
-   [ ] Add status transition controls.
-   [ ] Display server `409` message verbatim.
-   [ ] Create stats view.
-   [ ] Display category aggregates.
-   [ ] Display priority aggregates.
-   [ ] Display cache-hit state.
-   [ ] Read `X-Cache` header.
-   [ ] Add typed API client.
-   [ ] Generate or verify client against OpenAPI.
-   [ ] Add React error boundary.
-   [ ] Keep secrets out of frontend.
-   [ ] Avoid duplicated backend business rules.

## 9. Frontend Runtime Configuration

-   [ ] Choose runtime `/config.js` or nginx `/api` proxy.
-   [ ] Prevent API URL from being baked into the Vite build.
-   [ ] Make one frontend image usable across environments.
-   [ ] Document the choice in an ADR.
-   [ ] Verify runtime configuration in dev.
-   [ ] Verify runtime configuration in production.

## 10. Frontend Testing

-   [ ] Set up Vitest.
-   [ ] Write at least 5 meaningful component tests.
-   [ ] Test submission validation.
-   [ ] Test loading state.
-   [ ] Test complaint rendering.
-   [ ] Test dashboard filtering/pagination.
-   [ ] Test `409` error display.
-   [ ] Test stats/cache indicator.
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
-   [ ] Configure Ollama service.
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
-   [ ] Create `ollama_models` volume.
-   [ ] Justify all volumes.
-   [ ] Use dev bind mounts where appropriate.
-   [ ] Exclude dev bind mounts from production.
-   [ ] Add healthchecks to every service.
-   [ ] Use `depends_on: service_healthy`.
-   [ ] Load credentials from `.env`.
-   [ ] Commit `.env.example`.
-   [ ] Keep `.env` ignored.
-   [ ] Pin image tags.
-   [ ] Use `restart: unless-stopped`.
-   [ ] Set resource limits.
-   [ ] Avoid DB/cache ports in production.
-   [ ] Use `image: ${IMAGE_TAG}` in production.
-   [ ] Ensure production Compose has no `build:` keys.
-   [ ] Verify `docker compose down` preserves PostgreSQL data.

## 13. Kubernetes Base

-   [ ] Choose kind or k3d.
-   [ ] Set up Kustomize.
-   [ ] Create `k8s/base`.
-   [ ] Create `k8s/overlays/dev`.
-   [ ] Create `k8s/overlays/prod`.
-   [ ] Create `civicpulse` namespace.
-   [ ] Deploy backend with at least 2 replicas.
-   [ ] Deploy frontend with at least 2 replicas.
-   [ ] Deploy PostgreSQL as StatefulSet.
-   [ ] Add PostgreSQL PVC via `volumeClaimTemplates`.
-   [ ] Deploy Redis.
-   [ ] Add Redis PVC.
-   [ ] Create four ClusterIP services.
-   [ ] Keep database away from NodePort/LoadBalancer.
-   [ ] Create Ingress.
-   [ ] Route `/` to frontend.
-   [ ] Route `/api` to backend.
-   [ ] Use one host.
-   [ ] Create ConfigMap.
-   [ ] Create Secret.
-   [ ] Keep secrets out of committed manifests.
-   [ ] Commit placeholders only.

## 14. Kubernetes Probes and Updates

-   [ ] Add startup probe.
-   [ ] Use `/health` for startup probe.
-   [ ] Add liveness probe.
-   [ ] Keep liveness independent of database.
-   [ ] Add readiness probe.
-   [ ] Use `/ready` for readiness.
-   [ ] Make readiness depend on dependencies.
-   [ ] Configure `maxSurge: 1`.
-   [ ] Configure `maxUnavailable: 0`.
-   [ ] Set termination grace period.
-   [ ] Add `preStop` sleep.
-   [ ] Demonstrate rolling update.
-   [ ] Test zero failed requests under load.

## 15. Kubernetes Resources and HPA

-   [ ] Set CPU requests on every container.
-   [ ] Set CPU limits on every container.
-   [ ] Set memory requests/limits as appropriate.
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

-   [ ] Use `dev` plus feature branches.
-   [ ] Avoid direct commits to `main`.
-   [ ] Merge at least 5 PRs.
-   [ ] Link each PR to an Issue.
-   [ ] Add substantive partner review comments.
-   [ ] Make at least 35 commits per required assignment threshold.
-   [ ] Use conventional commit prefixes.
-   [ ] Keep both partners above required contribution threshold.
-   [ ] Create one deliberate merge conflict.
-   [ ] Resolve the conflict.
-   [ ] Preserve conflict evidence.
-   [ ] Explain why the chosen version won.

## 23. Documentation

-   [ ] Write problem statement in README.
-   [ ] Add badges.
-   [ ] Add Mermaid architecture diagram.
-   [ ] Add one-command quickstart.
-   [ ] Add API table.
-   [ ] Add screenshots.
-   [ ] Create provider-interface ADR.
-   [ ] Create frontend-runtime-config ADR.
-   [ ] Create deploy-by-SHA ADR.
-   [ ] Create PII/data-governance ADR.
-   [ ] Create `docs/RUNBOOK.md`.
-   [ ] Document deployment.
-   [ ] Document rollback.
-   [ ] Document log inspection.
-   [ ] Document triage failure response.
-   [ ] Create `docs/ENGINEERING-NOTES.md`.
-   [ ] Answer all 8 engineering questions.
-   [ ] Reference exact files and lines.
-   [ ] Create `docs/AI-USAGE.md`.
-   [ ] Document AI tools used.
-   [ ] Document AI-generated contributions.
-   [ ] Document your changes and reasoning.
-   [ ] Create `docs/TRIAGE.md`.

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

-   [ ] Explain laptop vs CI differences.
-   [ ] Identify lines freezing those differences.
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
-   [ ] Explain `internal: true` implications.
-   [ ] Explain hosted-LLM networking solution.
-   [ ] Document the biggest failure encountered.
-   [ ] Document initial incorrect assumption.
-   [ ] Document the command/log that revealed the cause.

## 27. Pre-Submission Safety Checks

-   [ ] Run `python scripts/check_submission.py`.
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
-   [ ] Verify no direct commits to `main`.

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
