# CivicPulse — Assignment Milestones

The assignment is structured from **contracts → core backend → frontend → containerized integration → Kubernetes → scaling → CI/CD → final evidence/docs**.

The goal is to make each milestone build on the previous one without requiring later milestones to redesign earlier work.

---

## Milestone 1 — Foundation & Contracts

- Create repository structure and branch strategy.
- Set up `dev` → feature branches → `main`.
- Define the backend API contract and data models.
- Define complaint states, categories, priorities, and validation rules.
- Define the `TriageProvider` interface and provider selection mechanism.
- Decide the frontend runtime API configuration approach.
- Decide the Compose/Kubernetes service architecture, especially the internal-network/hosted-LLM issue.
- Set up basic linting, formatting, and test frameworks.

**Goal:** All major interfaces and architectural decisions are fixed before implementation begins.

---

## Milestone 2 — Database & Backend Core

- Set up PostgreSQL and Alembic.
- Implement database schema, enums, constraints, and indexes.
- Implement repositories for all SQL access.
- Implement backend service layer.
- Implement complaint creation, retrieval, listing, filtering, pagination, and status transitions.
- Implement `/health`, `/ready`, and basic error handling.
- Add structured logging and request IDs.
- Add graceful shutdown handling.
- Create the idempotent seed system.

**Goal:** The backend works end-to-end with PostgreSQL using the required four-layer structure.

---

## Milestone 3 — AI Triage & Redis

- Implement `TriageResult` validation.
- Implement RuleBased, Simulated, hosted LLM, and Ollama providers as required.
- Implement provider factory/configuration.
- Add structured LLM output validation.
- Add timeout and single retry logic.
- Add rule-based fallback.
- Record provider, latency, and fallback information.
- Add Redis-based triage result caching.
- Add Redis stats caching and invalidation.
- Add Redis distributed rate limiting.

**Goal:** Complaint creation has a complete and reliable triage pipeline, even when the LLM fails.

---

## Milestone 4 — Complete Backend API & Backend Tests

- Finish all required endpoints.
- Finish exact response/error behavior.
- Implement `/api/stats`, `/api/meta/providers`, and `/metrics`.
- Verify state-machine behavior.
- Verify cache HIT/MISS behavior.
- Verify rate-limit behavior.
- Add fallback, malformed-output, injection, and integration tests.
- Reach the required backend coverage.

**Goal:** The backend is feature-complete and independently testable before the frontend depends on it.

---

## Milestone 5 — Frontend

- Build the complaint submission page.
- Build the operations dashboard.
- Add filtering, pagination, and status updates.
- Display server-side 409 messages correctly.
- Build the statistics view.
- Connect frontend through the typed API client.
- Add loading/error states and error boundary.
- Implement the previously chosen runtime configuration approach.
- Add the required component tests.

**Goal:** A complete user-facing application works against the stable backend contract without duplicating backend business rules.

---

## Milestone 6 — Docker & Compose Integration

- Create production Dockerfiles for backend and frontend.
- Add multi-stage builds, non-root users, pinned images, and healthchecks.
- Add `.dockerignore` files.
- Create `compose.yaml` for development.
- Create `compose.prod.yaml` for production.
- Add PostgreSQL, Redis, and Ollama persistence.
- Implement the two-network architecture.
- Verify frontend cannot reach the database.
- Verify data survives Compose restart.
- Verify the complete five-container system works with one command.

**Goal:** The application becomes a reproducible local system without changing application architecture.

---

## Milestone 7 — Kubernetes Baseline

- Create Kustomize base and dev/prod overlays.
- Create namespace and all required Deployments/StatefulSet.
- Add PostgreSQL PVC/StatefulSet.
- Add Redis persistence.
- Add Services and Ingress.
- Add ConfigMap and Secret handling.
- Add resource requests/limits.
- Add startup, liveness, and readiness probes.
- Add rolling-update settings and graceful termination.
- Deploy the already-working application to kind/k3d.
- Verify PostgreSQL data survives pod deletion.

**Goal:** Kubernetes becomes a deployment layer over the already-working application, not a second implementation.

---

## Milestone 8 — HPA, VPA & Operational Testing

- Install Metrics Server.
- Configure backend HPA.
- Run controlled load tests.
- Capture HPA scaling behavior and replicas-vs-load data.
- Measure and explain scaling lag.
- Install/configure VPA in `Off` mode.
- Capture recommendations.
- Update resource requests from measured results.
- Re-run load tests and compare behavior.
- Demonstrate zero-downtime rolling update under load.

**Goal:** Scaling and rollout behavior are measured on the stable Kubernetes deployment rather than guessed.

---

## Milestone 9 — CI/CD & Security Gates

- Create `ci.yml`.
- Add linting, type checks, backend/frontend tests, builds, Trivy, kubeconform, and Compose integration.
- Protect `main`.
- Require PR checks and approval.
- Create `cd.yml`.
- Build and push GHCR images using commit SHA tags.
- Generate SBOMs and capture image digests.
- Deploy the immutable SHA to an ephemeral Kubernetes cluster.
- Run rollout and smoke tests.
- Create release workflow for version tags.
- Implement rollback paths.
- Verify secrets and permissions are handled correctly.

**Goal:** A push to `main` produces a tested, scanned, deployable artifact and deploys that exact artifact.

---

## Milestone 10 — Documentation, Evidence & Final Hardening

- Complete README and architecture diagram.
- Write the four required ADRs.
- Write `RUNBOOK.md`.
- Write `ENGINEERING-NOTES.md`.
- Write `AI-USAGE.md`.
- Capture required screenshots/evidence.
- Verify clean-clone quickstart.
- Verify all required demo scenarios.
- Verify Git/PR/commit requirements.
- Run the submission checker.
- Record the demo and ensure both partners can explain the whole system.

**Goal:** Everything required by the rubric is documented and demonstrable, not merely implemented.

---

## Dependency Flow

```text
M1 Foundation
    ↓
M2 Database + Backend Core
    ↓
M3 AI + Redis
    ↓
M4 Complete Backend
    ↓
M5 Frontend
    ↓
M6 Docker + Compose
    ↓
M7 Kubernetes
    ↓
M8 HPA/VPA + Load Testing
    ↓
M9 CI/CD
    ↓
M10 Docs + Evidence + Final Validation
```

## Development Principle

- **M1** locks the contracts and architectural decisions.
- **M2–M5** implement the application.
- **M6** packages the application.
- **M7–M8** operate and validate it on Kubernetes.
- **M9** automates the workflows already proven manually.
- **M10** verifies, documents, and demonstrates the complete submission.

This ordering is intended to minimize later rewrites and prevent infrastructure milestones from breaking the application milestones that came before them.
