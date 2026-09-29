# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Git repo (`main`/`dev`, remote `Demidoga/scd_a1`). **Milestones 1–6 are implemented**: `backend/` has the full four-layer backend (routes/services/repositories/providers), PostgreSQL schema via Alembic, the 3-provider AI triage pipeline, Redis caching/rate-limiting, and 112 passing tests at 94.5% coverage; `frontend/` has the React 18 + Vite + TypeScript + Tailwind app (submit/dashboard/stats views, typed API client, runtime-configured via same-origin `/api`, 8 Vitest component tests); the whole system is containerized (`backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`, `compose.yaml`/`compose.prod.yaml`, `edge`/`internal` networks, `migrate` service, `pgdata`/`redisdata` volumes) and verified end-to-end with Docker Desktop. **Milestone 7 (Kubernetes baseline)** is implemented as Kustomize manifests (`k8s/base`, `k8s/components`, `k8s/overlays/{dev,prod}`) plus `scripts/k8s/`, statically validated and verified live on a local k3d cluster (deploy, Ingress, probes, Postgres persistence — see `docs/progress.md`). HPA/VPA/load testing and CI don't exist yet — that's Milestones 8–9. See `docs/progress.md` for the current, maintained snapshot of what's done/next; don't rely on this paragraph's specifics staying current, only `docs/progress.md`. When continuing implementation, follow the architecture and milestone order below rather than inventing a different structure — the docs are a binding spec, not background reading.

## What CivicPulse is

An end-to-end municipal complaint intake, AI-assisted triage, persistence, and operations platform: a citizen submits free-text complaint + location, the backend validates it, classifies it through a replaceable triage provider, persists it in PostgreSQL, and exposes it to an operations dashboard. Redis provides read-through stats caching and distributed rate limiting. Runs as four cooperating containers under Docker Compose locally, and as a scaled/probed/autoscaling workload on Kubernetes via CI/CD.

**Central principle — replaceability with controlled failure:** frontend owns no domain rules; backend doesn't depend on one AI implementation; persistence is isolated behind repositories; outbound integrations are isolated behind providers/interfaces; probabilistic AI is wrapped in deterministic validation/timeout/retry/cache/fallback; deployment uses immutable image references (build-once-deploy-many).

## Documentation map — read the specific file, not everything

`docs/architecture.md` is a **router**, not a spec — start there, then jump to the one domain file you need:

| Need to work on... | Read |
|---|---|
| Layering, API contract, status state machine, health/readiness, logging | `docs/architecture/backend.md` |
| Schema, migrations (Alembic, `migrate` Job pattern), indexes, seed data | `docs/architecture/database.md` |
| Redis stats cache + rate limiter | `docs/architecture/cache.md` |
| `TriageProvider`, reliability pipeline, PII policy | `docs/architecture/ai.md` |
| React views, runtime config, typed API client, container build | `docs/architecture/frontend.md` |
| Images, networks, volumes, compose files | `docs/architecture/docker-compose.md` |
| Manifests, probes, rollouts, HPA/VPA, rollback | `docs/architecture/kubernetes.md` |
| Workflows, security boundaries, build-once-deploy-many | `docs/architecture/cicd.md` |
| Unit/integration/component test requirements | `docs/architecture/testing.md` |
| Network isolation, secrets, cross-cutting security | `docs/architecture/security.md` |
| Full planned directory tree | `docs/architecture/repository-layout.md` |
| The assignment spec itself (requirements, rubric, deductions, submission) — routed by task | `docs/assignment/INDEX.md` (verbatim split of the original assignment; not the architecture docs) |
| Build-order dependency chain | `docs/architecture/roadmap.md` |
| Detailed per-milestone task lists (working checklist) | `docs/Milestones.md`, `docs/Milestones/milestone-*.md` |
| What can be built in parallel vs. what blocks what | `docs/Component_Dependencies.md` |
| The full graded checklist | `docs/Todo.md` |

Detailed decisions, schemas, workflows, and configuration belong in `docs/architecture/*.md`, never duplicated back into the router file.

### Reading the assignment

Whenever you need to check what the assignment requires or how it is graded (requirements, API contract, rubric marks, automatic deductions, submission, viva, engineering-notes questions):

1. Open `docs/assignment/INDEX.md` and use its routing table to pick the relevant file(s) — the spec file for the topic, plus the matching `docs/assignment/rubric/*.md` file for grading.
2. Read only those files.
3. **Do not open `docs/Software Construction and Design -  Assignment 1.md` (or its `.pdf`)** to look things up. The split files are verbatim copies of it, so nothing is lost. Open the original only for a quirk the index flags as needing the PDF (garbled tables, flattened code blocks, the architecture diagram), or if the user explicitly asks for it.

The assignment spec (`docs/assignment/`) says what is required; `docs/architecture/` says how this project satisfies it. Don't mix them up.

## Architecture at a glance

**Stack:** React 18 + Vite + TypeScript (nginx) · FastAPI + Pydantic v2 + SQLAlchemy + Alembic · PostgreSQL 16 · Redis 7 · Docker Compose (local) · Kubernetes via k3d + Kustomize · GitHub Actions → GHCR/Trivy/kubeconform/Syft.

**Backend layering — dependency arrows are one-way:**

```text
routes → services → repositories → PostgreSQL
services → TriageProvider interface (LLM / Rules / Simulated)
services → Redis stats-cache abstraction
```

`routes/` = HTTP only, `services/` = domain logic, `repositories/` = all SQL, `providers/` = external systems. A route opening a DB session or encoding a transition rule is a defect. **Named exception:** the distributed IP rate limiter runs as a route-level FastAPI dependency *before* Pydantic validation (cost control — reject before spending validation/AI budget) — this is the one sanctioned bypass of routes→services→repositories.

**Status state machine** (explicit transition table, not scattered conditionals): `open → {in_progress, rejected}`, `in_progress → {resolved, rejected}`, `resolved`/`rejected` terminal. Illegal transitions → `409` naming the attempted transition. Frontend never duplicates this table — it renders based on backend responses only.

**AI triage (`TriageProvider` interface, 3 implementations — no Ollama, instructor-approved scope reduction):** `LLMTriage` (Groq, `TRIAGE_PROVIDER=llm`), `RuleBasedTriage` (`rules`), `SimulatedTriage` (`simulated`, used in CI). Pipeline: content-hash `(text, location)` Redis cache (24h TTL) → provider call → prompt-injection-resistant structured JSON → `TriageResult` Pydantic validation → 10s timeout, one jittered retry on timeout/429/5xx only → fall back to `RuleBasedTriage` on failure (`triaged_by = rules:fallback`) → persist. A provider outage must never surface as a 500.

**Redis has two responsibilities with opposite failure modes:** stats cache (30s TTL, `X-Cache: HIT|MISS`, invalidated on writes) and triage cache **fail open** (degrade to direct query/provider call) on Redis outage — they're pure optimizations. The rate limiter (fixed-window, 10 req/60s/IP, atomic Lua `INCR`+`EXPIRE`, never plain `INCR` then `EXPIRE`) **fails closed** (`503`) on Redis outage, because it exists to protect the shared Groq free-tier quota.

**Network topology:** two Compose networks — `edge` (frontend, backend, egress to Groq) and `internal: true` (backend, postgres, redis). Backend is the only bridge; frontend structurally cannot reach PostgreSQL/Redis. Kubernetes mirrors this with ClusterIP-only Services on the data layer.

**Deploy-by-SHA:** CI never publishes; only a push to `main` (post-PR-approval) builds, tags with commit SHA, scans, and deploys that exact SHA. `latest` may be pushed for convenience but is never deployed. Migrations run via a dedicated `migrate` Compose service / Kubernetes `Job` (never an `initContainer`, never backend startup code) that must reach `Complete` before the app receives traffic.

**Kubernetes specifics worth remembering:** PostgreSQL is a `StatefulSet` with PVC (a bare Deployment here is an automatic assignment failure); Redis is a `Deployment` with PVC but `strategy: Recreate` (RWO volume would otherwise deadlock a RollingUpdate); backend HPA v2 targets 60% CPU, `minReplicas: 2`, `maxReplicas: 10`, 300s scale-down stabilization; VPA stays in `updateMode: Off` (Auto would fight HPA's utilization denominator) and is advisory only; `/health` (liveness, DB-independent) vs `/ready` (readiness, checks PostgreSQL + Redis, `503` naming the failed dependency) must never be swapped.

## Cross-cutting rules (apply everywhere, already decided — don't relitigate)

- No SQL outside repositories; no business rules in routes (rate limiter is the one named exception).
- No frontend copy of backend state-transition rules.
- No secrets in source, frontend bundles, or committed Kubernetes manifests (placeholders only, including base64 Secret data).
- No `latest` as a deployment target — deploy by immutable SHA.
- No localhost-based service-to-service communication.
- No database/cache exposure via production host ports or public Kubernetes Services.
- PostgreSQL is the sole source of truth for complaint data; Redis holds only derived/cache state.
- Builds are reusable across environments (build once, deploy many) — no environment-specific images. This is why the frontend uses an nginx `/api` proxy instead of baking an API URL into the Vite build.
- FastAPI's default validation error is `422`; the assignment contract requires `400` — this needs an explicit `RequestValidationError` handler in `app/main.py`/`app/errors.py`, not a per-route fix.

## Repository layout (planned — create matching this when scaffolding)

```text
civicpulse/
├── backend/app/{routes,services,repositories,providers/{redis,triage}}/, alembic/versions/, tests/, Dockerfile
├── frontend/src/{components,pages,api}/, tests/, Dockerfile, nginx.conf
├── k8s/base/{namespace,backend,frontend,postgres,redis,migrate-job,ingress,configmap,secret,hpa,vpa,pdb,kustomization}.yaml, overlays/{dev,prod}/
├── load/k6-script.js
├── docs/{architecture.md, architecture/, ENGINEERING-NOTES.md, RUNBOOK.md, AI-USAGE.md, TRIAGE.md, adr/000{1..4}-*.md, evidence/}
├── scripts/check_submission.py
├── .github/workflows/{ci.yml,cd.yml,release.yml}
├── compose.yaml, compose.prod.yaml, .env.example, .gitignore, README.md, LICENSE
```

Full annotated version: `docs/architecture/repository-layout.md`.

## Commands

Backend, frontend, and Docker Compose commands below are runnable today (Milestones 1–6 done; backend via `uv`, frontend via `npm`; see `README.md` for full local setup including the one-time Postgres role/DB creation). Kubernetes commands below are runnable for Milestone 7 (the manifests and `scripts/k8s/*`); HPA/VPA/load-test/CI commands remain aspirational until Milestones 8–9 land.

- Backend lint/type: `uv run ruff check .`, `uv run mypy app` (run from `backend/`)
- Backend tests: `uv run pytest tests/unit -q` (no DB needed) or `uv run pytest tests/ --cov=app --cov-report=term-missing -q` (full suite, needs local `civicpulse_test` Postgres + Redis db 15); CI/dev default `TRIAGE_PROVIDER=simulated`; coverage gate is ≥65% on `app/` (currently ~94.5%)
- Migrations: `uv run alembic upgrade head` (local dev only for now; the dedicated `migrate` Compose service / k8s `Job` pattern is Milestone 6/7 work)
- Seed: `uv run python -m app.seed` (idempotent, ≥30 complaints)
- Frontend dev server: `npm run dev` (run from `frontend/`; proxies `/api` to `http://localhost:8000`, requires the backend running)
- Frontend lint/type: `npm run lint` (oxlint), `npx tsc -b` (run from `frontend/`)
- Frontend build: `npm run build` — `tsc -b && vite build` (run from `frontend/`)
- Frontend tests: `npm run test` (Vitest + Testing Library, run from `frontend/`)
- Local stack: `docker compose up --build` (dev, hot-reload), `IMAGE_TAG=<sha> docker compose -f compose.prod.yaml up -d` (prod-shaped, pre-built images only)
- K8s manifest validation (no cluster needed; needs `kubectl`, `kubeconform`, `uv`): `scripts/k8s/validate-manifests.sh`
- K8s local deploy (needs Docker + `k3d` + `kubectl`): `scripts/k8s/create-cluster.sh` → `load-images.sh` → `create-secrets.sh` → `deploy.sh dev` → `smoke-test.sh` / `verify-persistence.sh`; `DRY_RUN=1 scripts/k8s/deploy.sh dev <tag>` just renders the manifests
- Load testing: `k6 run load/k6-script.js`, watch scaling with `kubectl get hpa -w` — not yet written
- Pre-submission check: `python scripts/check_submission.py` — not yet written

## Build order

Follow `docs/architecture/roadmap.md` / `docs/Milestones.md`: Foundation & contracts → Database & backend core → AI + Redis → Complete backend API + tests → Frontend → Docker/Compose → Kubernetes baseline → HPA/VPA + load testing → CI/CD → Docs/evidence/hardening. Later milestones are designed not to require redesigning earlier ones — don't jump ahead to Kubernetes work while the backend contract is still moving, for example.

## File and Folders

Build the application using a **clean, and scalable file/folder architecture**.

* Use meaningful, descriptive names for files, folders, components, services, utilities, and modules.
* Organize code by **feature/domain and responsibility**, so a new developer can locate any component intuitively by following the folder hierarchy.
* Avoid large files. Split complex components, business logic, API calls, types, hooks, utilities, and configuration into focused modules.
* Avoid overcrowded folders. Create logical subdirectories when a feature contains multiple related files.
* Keep UI, business logic, data access, types, configuration, and utilities properly separated.
* Prefer small, single-responsibility files and components with clear boundaries.
* Maintain consistent naming and structure throughout the entire project.
* Before implementing a feature, determine where it belongs in the architecture rather than simply placing code in the nearest existing file.
* The resulting structure should be easy to understand and extend **without needing to inspect the implementation of every file**.

Prioritize **maintainability, discoverability, separation of concerns, and scalability** over minimizing the number of files.

## Architectural Flexibility

`ARCHITECTURE.md` and `Milestones.md` are a guideline, not a strict whitelist of files or folders.

* Create, modify, move, rename, or delete files and folders when necessary.
* Improvise and introduce new structure when it improves clarity, separation of concerns, or maintainability.
* Do not force code into documented locations if a better structure makes more sense.
* Update `ARCHITECTURE.md` when making significant architectural changes.

## Response Guidelines

- Explain concepts simply and assume the developer is a junior. Avoid unexplained framework-specific or advanced terminology.
- Name tools, services, extensions, and infrastructure explicitly. State where each comes from and what it does.
- Clearly identify all manual steps, including configuration, database changes, dashboard settings, environment variables, CLI commands, and deployment steps.
- End every response with a `Files Edited` section listing every file modified.

