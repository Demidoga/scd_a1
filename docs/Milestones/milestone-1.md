# Milestone 1 — Foundation & Contracts

> **Purpose:** Freeze the interfaces, domain rules, repository conventions, and deployment decisions that the rest of CivicPulse will implement.
>
> **Scope:** Foundation only. Do not build the complete complaint flow yet.
>
> **Goal:** A developer can start Milestone 2 without having to reinterpret the domain, API, provider abstraction, frontend runtime configuration, service topology, or basic project tooling.

---

## 1. Milestone Outcome

At the end of Milestone 1, the repository should contain:

- the agreed Git workflow and initial project structure;
- a versioned description of the API and shared domain models;
- explicit complaint categories, priorities, statuses, validation rules, and status transitions;
- the `TriageProvider` contract and provider-selection mechanism;
- the frontend runtime API configuration decision;
- the Docker Compose and Kubernetes service topology, including the hosted-LLM/internal-network decision;
- initial lint, formatting, type-check, and test configuration;
- ADRs for the architectural decisions that will constrain later implementation;
- a short project-state file so another context/session can continue without rediscovering decisions.

**Milestone 1 is complete when the interfaces are stable enough that backend, frontend, AI-provider, and DevOps work can proceed independently without inventing conflicting contracts.**

---

## 2. What Is In Scope vs. Out of Scope

### In scope

- repository scaffolding;
- branch/PR conventions;
- API and domain contract definition;
- Pydantic/domain model skeletons;
- provider interface and factory contract;
- runtime configuration decision;
- Compose/Kubernetes topology design;
- environment-variable naming and configuration ownership;
- basic developer tooling;
- ADRs and architecture documentation;
- contract-level tests where useful.

### Out of scope

- implementing PostgreSQL repositories;
- implementing Redis cache/rate limiter;
- implementing real LLM calls;
- implementing the complete React UI;
- writing production Dockerfiles;
- writing full Kubernetes manifests;
- implementing CI/CD workflows;
- HPA/VPA/load testing;
- seeded data implementation.

Those belong to later milestones. Milestone 1 may create placeholders/directories for them.

---

# 3. Workstream A — Repository & Git Foundation

## A1. Create the repository skeleton

Create the agreed top-level structure before feature work begins:

```text
civicpulse/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── providers/
│   │       └── triage/
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   └── package.json
│
├── k8s/
│   ├── base/
│   └── overlays/
│       ├── dev/
│       └── prod/
│
├── load/
├── docs/
│   ├── adr/
│   └── evidence/
├── scripts/
├── .github/
│   └── workflows/
├── compose.yaml
├── compose.prod.yaml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

Do not fill the repository with speculative implementation files. Create only the directories and initial files needed to establish the architecture.

## A2. Establish the branch model

Use:

```text
main
  ↑
  PR
  │
dev
  ↑
  PRs
  │
feature/<issue>-<short-name>
```

### Rules

| Rule | Required behavior |
|---|---|
| `main` | Protected; no direct pushes |
| `dev` | Integration branch for completed feature work |
| Feature branches | Created from `dev` |
| Feature → `dev` | Pull request + review |
| `dev` → `main` | Pull request; required checks must pass |
| Commit style | Use conventional prefixes such as `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:` |
| Issue linkage | Each substantive feature branch/PR should reference its GitHub Issue |

The assignment requires the two-branch model, protected `main`, PR-based work, partner review, and no direct commits to `main`.

## A3. Initial repository policies

Add/check:

- `.gitignore` covering `.env`, virtual environments, `node_modules`, Python caches, build output, IDE files, and local secrets;
- `.env.example` containing variable names only and safe placeholders;
- no real keys, passwords, or tokens anywhere in source/history;
- repository-level contribution/PR expectations if useful;
- a concise `CLAUDE.md` if Claude Code is being used, containing stable architectural rules rather than the entire assignment.

### Acceptance criteria

- [ ] Clean clone has the expected directory structure.
- [ ] `main` protection is configured on GitHub.
- [ ] `dev` exists.
- [ ] First feature branch is created from `dev`.
- [ ] No secret values are committed.
- [ ] `.env` is ignored and `.env.example` is tracked.

---

# 4. Workstream B — Domain Contract

The domain contract must be written before implementation so backend and frontend share one source of truth.

## B1. Complaint categories

Use exactly the assignment categories:

```text
water
 electricity
 sanitation
 roads
 streetlights
 other
```

Implementation expectation:

```python
class Category(str, Enum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"
```

The actual naming style may follow project conventions, but serialized API/DB values must remain contract-compatible.

## B2. Priority values

```text
high
normal
low
```

## B3. Complaint status values

```text
open
in_progress
resolved
rejected
```

Default status for a newly persisted complaint:

```text
open
```

## B4. Explicit status transition table

Do not encode this as scattered conditionals. Create one explicit transition table as the backend source of truth.

| Current | Allowed next states |
|---|---|
| `open` | `in_progress`, `rejected` |
| `in_progress` | `resolved`, `rejected` |
| `resolved` | none |
| `rejected` | none |

Every transition not represented in this table is invalid and must become HTTP `409`.

The frontend must **not** recreate this table as a second source of truth. The backend owns transition validity; the frontend renders the server's result.

## B5. Complaint input validation

| Field | Rule | Where enforced |
|---|---|---|
| `text` | 10–2000 characters | application + database |
| `location` | 3–200 characters | application + appropriate schema constraint |
| `reporter_contact` | optional / nullable | application schema |
| `category` | one of defined enum values | backend/domain schema |
| `priority` | one of defined enum values | backend/domain schema |
| `status` | one of defined enum values | backend/domain/state machine |
| `ai_summary` | nullable, maximum 140 characters | Pydantic + database |
| `triaged_by` | controlled provider marker | backend/service |
| `triage_latency_ms` | integer measurement | backend/service |
| timestamps | UTC `timestamptz` | persistence layer |

For the create request, the client supplies complaint content and location and may supply reporter contact. Triage-derived fields are backend-owned and must not be accepted as authoritative client input.

## B6. Persistence model contract

Minimum complaint record:

```text
id                  UUID, server-generated
text                string, 10–2000 chars
location            string, 3–200 chars
reporter_contact    nullable
category            enum
priority            enum
status              enum, default open
ai_summary          nullable, max 140 chars
triaged_by          provider/fallback marker
triage_latency_ms   integer
created_at          timestamptz UTC
updated_at          timestamptz UTC
```

Milestone 1 should define this model in the backend's domain/schema layer, even though SQLAlchemy persistence is implemented later.

### Acceptance criteria

- [ ] All enums exist in one backend-owned contract location.
- [ ] Status transition table exists as data, not scattered `if/elif` logic.
- [ ] Create-input validation is explicitly documented.
- [ ] Backend-owned triage fields are distinguishable from citizen input.
- [ ] Frontend contract can be generated/checked from backend OpenAPI later.

---

# 5. Workstream C — Backend API Contract

FastAPI + Pydantic v2 is the selected backend approach. FastAPI provides the OpenAPI document that the frontend client will consume/check.

## C1. Endpoint contract

| Method | Path | Contract |
|---|---|---|
| `POST` | `/api/complaints` | Validate → rate-limit → triage → persist; return `201`; `400` for field-level validation; `429` on rate-limit rejection |
| `GET` | `/api/complaints/{id}` | Return complaint or `404` |
| `GET` | `/api/complaints` | Filter by category/priority/status; paginate; return total |
| `PATCH` | `/api/complaints/{id}/status` | Validate state transition; invalid transition → `409` naming attempted transition |
| `GET` | `/api/stats` | Aggregate counts; Redis read-through cache; `X-Cache: HIT|MISS`; TTL 30 s |
| `GET` | `/api/meta/providers` | Active provider + last 20 triage outcomes with provider, latency, fallback flag |
| `GET` | `/health` | Liveness; must not access DB |
| `GET` | `/ready` | Readiness; succeeds only when PostgreSQL + Redis are reachable; failure response names failed dependency |
| `GET` | `/metrics` | Prometheus text format with request count, request latency histogram, triage latency, fallback counter |

## C2. List endpoint query contract

`GET /api/complaints` supports:

```text
category=<category>
priority=<priority>
status=<status>
page=<positive integer>
page_size=<positive integer, maximum 100>
```

Response contract should include:

```text
items   complaint[]
total   integer
page    integer
page_size integer
```

Do not let the frontend maintain a separate authoritative copy of filtering/pagination rules.

## C3. Create endpoint conceptual flow

```text
POST /api/complaints
        │
        ├── request validation
        ├── distributed IP rate-limit check
        ├── triage orchestration
        │      ├── cache lookup
        │      ├── selected provider
        │      ├── structured-output validation
        │      ├── retry-on-retryable failure
        │      └── rules fallback
        ├── persistence
        └── 201 response
```

The actual implementations come later; Milestone 1 only fixes the boundary.

## C4. Error contract

At minimum, agree that:

- validation failures are field-level and return `400`;
- missing complaint IDs return `404`;
- invalid status transitions return `409` and explicitly identify the attempted transition;
- rate-limit rejection returns `429` and includes `Retry-After`;
- readiness failure returns `503` and identifies the failed dependency.

Keep the error envelope consistent so the frontend can handle it once.

### Acceptance criteria

- [ ] All ten endpoints are listed with method/path/behavior.
- [ ] Request and response models exist or are explicitly scaffolded.
- [ ] Error behavior is documented.
- [ ] Pagination limit `page_size <= 100` is fixed.
- [ ] OpenAPI can be generated once the route scaffolds are present.

---

# 6. Workstream D — Triage Provider Contract

The AI layer is designed around replaceability. The rest of the application depends on the interface, not a vendor SDK.

## D1. `TriageResult`

Define the shared output model:

```python
class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)
```

This model is the validation boundary for all triage implementations.

## D2. `TriageProvider` protocol

Target contract:

```python
class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult:
        ...
```

Keep the interface small. The caller should not know whether the provider is remote, local, deterministic, or rule based.

## D3. Provider implementations to reserve

Create the provider module structure now; implementation follows later.

```text
backend/app/providers/triage/
├── base.py
├── llm.py
├── ollama.py
├── rules.py
├── simulated.py
└── factory.py
```

Required implementations:

| Provider | Role | Determinism |
|---|---|---|
| `LLMTriage` | Hosted production path | Probabilistic |
| `OllamaTriage` | Local/offline path | Model-dependent |
| `RuleBasedTriage` | Fallback / deterministic path | Deterministic |
| `SimulatedTriage` | CI/test path | Deterministic |

## D4. Provider selection

Use:

```text
TRIAGE_PROVIDER
```

The factory selects the configured implementation. Suggested values:

```text
llm
ollama
rules
simulated
```

The exact provider string persisted in `triaged_by` is a separate concern. Assignment-compatible values include:

```text
llm:groq
llm:ollama
rules
rules:fallback
```

Do not let the frontend choose the provider per request unless explicitly required by a future contract. Provider selection is deployment/application configuration.

## D5. AI failure semantics to freeze now

Even though implementation is later, the following behavior must be fixed:

```text
provider call
   │
   ├── success + valid schema → accept
   │
   ├── timeout / 429 / 5xx → one jittered retry
   │
   ├── 400 → no retry
   │
   ├── malformed model output → reject safely / fallback path
   │
   └── provider failure after retry → RuleBasedTriage
```

Required limits/behaviors:

- hard timeout: **10 seconds**;
- one retry only for timeout, `429`, or `5xx`;
- no retry for `400`;
- fallback records `triaged_by = "rules:fallback"`;
- triage results are later cacheable by content hash for 24 hours;
- API keys are never logged;
- complaint text is untrusted data and requires a prompt-injection guardrail;
- CI uses `SimulatedTriage` rather than live network inference.

### Acceptance criteria

- [ ] `TriageResult` exists.
- [ ] `TriageProvider` exists.
- [ ] Factory/selection contract is documented.
- [ ] Four provider implementation slots exist.
- [ ] Retry/fallback semantics are written down before coding them.
- [ ] No provider-specific types leak into route contracts.

---

# 7. Workstream E — Frontend Runtime Configuration

## E1. Decision: nginx `/api` proxy

Use the preferred architecture:

```text
Browser
   │
   │ same-origin request: /api/...
   ▼
nginx
   │
   │ proxy_pass /api
   ▼
backend service
```

### Why this is the project default

- the frontend image does not contain an environment-specific absolute backend URL;
- the browser uses one stable path (`/api`);
- the same image can be used across environments;
- runtime routing is handled by nginx rather than Vite build-time variables;
- it directly supports the assignment's build-once-deploy-many requirement.

The assignment also permits startup-generated `/config.js`, but the project default is nginx proxy. Record the decision in:

```text
docs/adr/0002-frontend-runtime-config.md
```

## E2. Frontend boundary rule

React owns:

- presentation;
- user interaction;
- client-side validation mirroring server constraints;
- loading/error states;
- rendering backend responses.

React does **not** own:

- authoritative complaint categories;
- authoritative priorities;
- status-transition legality;
- AI fallback logic;
- persistence rules.

## E3. API client direction

Target flow:

```text
FastAPI + Pydantic
       ↓
OpenAPI
       ↓
Typed client / checked types
       ↓
React + TypeScript
```

Choose the client generation/checking tool during implementation, but keep OpenAPI as the source of truth.

### Acceptance criteria

- [ ] Runtime-config decision is documented in ADR 0002.
- [ ] No absolute backend URL is required inside the frontend bundle.
- [ ] `/api` is the browser-facing API path.
- [ ] Frontend/domain ownership boundaries are documented.

---

# 8. Workstream F — Compose & Kubernetes Architecture

The deployment topology must be fixed before Dockerfiles/manifests are written.

## F1. Compose service topology

The assignment expects five cooperating containers:

```text
frontend
backend
postgres
redis
ollama
```

### Compose networks

Use two networks:

```text
edge
internal (internal: true)
```

Membership:

| Service | `edge` | `internal` |
|---|---:|---:|
| frontend | yes | no |
| backend | yes | yes |
| postgres | no | yes |
| redis | no | yes |
| ollama | no | yes |

This creates the intended segmentation:

```text
Internet/browser
       │
   frontend
       │ edge
    backend
    │      │
 internal  │ edge outbound
  ┌───┴──┐  │
  │      │  └── hosted LLM
Postgres Redis
      │
    Ollama
```

## F2. Hosted-LLM + `internal: true` decision

The important consequence is that `internal: true` prevents the internal-only services from using that network for outbound internet access.

Therefore:

- PostgreSQL, Redis, and Ollama remain internal-only;
- backend joins both `edge` and `internal`;
- hosted `LLMTriage` outbound traffic leaves through the backend's `edge` attachment;
- Ollama is reached by the backend over the internal network;
- frontend never receives direct access to the database/cache/LLM network.

This satisfies the security/network-segmentation requirement while leaving the hosted LLM path usable.

Document the final implementation in `docs/ENGINEERING-NOTES.md`, especially the answer to the assignment's internal-network question.

## F3. Compose persistence

Reserve three named volumes:

```text
pgdata
redisdata
ollama_models
```

Purpose:

| Volume | Purpose |
|---|---|
| `pgdata` | PostgreSQL durable data |
| `redisdata` | Redis AOF persistence |
| `ollama_models` | Prevent repeated model downloads |

Development may use source bind mounts for hot reload. Production must not use source bind mounts.

## F4. Compose files

### `compose.yaml`

Development-oriented configuration:

- `build:` allowed;
- bind mounts allowed where useful;
- hot reload allowed;
- all five services represented;
- health checks and dependency conditions defined later.

### `compose.prod.yaml`

Production-oriented configuration:

- `image: ${IMAGE_TAG}`;
- **no `build:` keys**;
- pinned image tags/references;
- no published PostgreSQL port;
- no published Redis port;
- no deployment of `:latest`;
- named volumes only for persistent data;
- resources/restart policies later.

---

## F5. Kubernetes topology

Use:

- `kind` or `k3d` for local/ephemeral clusters;
- Kustomize with `base/` + `overlays/dev` + `overlays/prod`;
- namespace `civicpulse`.

Required objects:

```text
Namespace
Deployment: backend (>= 2 replicas)
Deployment: frontend (>= 2 replicas)
StatefulSet: postgres + persistent storage
Deployment: redis + PVC
Service: backend (ClusterIP)
Service: frontend (ClusterIP)
Service: postgres (ClusterIP)
Service: redis (ClusterIP)
Ingress
ConfigMap
Secret
HPA
VPA
PDB
```

PostgreSQL must be a **StatefulSet**, not a Deployment.

## F6. Ingress contract

One host with:

```text
/     → frontend
/api  → backend
```

The frontend should therefore use the same `/api` path in the browser regardless of whether it runs in Compose or Kubernetes.

## F7. Probe contract

Freeze these endpoint responsibilities now:

| Probe | Endpoint | DB access? | Purpose |
|---|---|---:|---|
| Startup | `/health` | no | Allow slow startup without restart loop |
| Liveness | `/health` | no | Process health / restart decision |
| Readiness | `/ready` | yes | Service eligibility / dependency readiness |

Backend startup probe target:

```text
failureThreshold: 30
periodSeconds: 2
```

The liveness/readiness distinction must remain intact through implementation.

## F8. Production rollout contract

Backend/frontend deployments should later support:

```text
maxSurge: 1
maxUnavailable: 0
terminationGracePeriodSeconds: configured
preStop: connection-draining sleep
```

This is required for the later zero-downtime rollout demonstration.

## F9. Autoscaling contract

Reserve HPA/VPA architecture now, but implement and tune later.

HPA target:

```text
backend
minReplicas: 2
maxReplicas: 10
CPU target: 60%
scaleDown stabilization: 300s
scaleUp stabilization: 0s
```

Mandatory CPU/memory `requests` and `limits` are part of the eventual Deployment contract because HPA CPU utilization requires a request denominator.

VPA:

```text
backend
updateMode: Off
```

Reason to freeze now: VPA in Auto and HPA using CPU utilization would modify the same resource-request signal HPA depends on. The assignment requires recommender mode for this work.

### Acceptance criteria

- [ ] Five-container Compose topology is documented.
- [ ] Frontend cannot reach DB/cache in the intended topology.
- [ ] Backend has the necessary outbound path for hosted LLM access.
- [ ] Ollama remains private/internal.
- [ ] PostgreSQL persistence is represented as StatefulSet + PVC in the architecture plan.
- [ ] Kubernetes ingress, probes, replica counts, HPA and VPA contracts are recorded.
- [ ] Compose dev/prod responsibilities are distinct.

---

# 9. Workstream G — Configuration & Secret Boundaries

Define configuration ownership now so later code does not invent ad-hoc environment variables.

## G1. Application configuration categories

### CivicPulse configuration to define

The configuration contract should be finalized here rather than introduced ad hoc during implementation. At minimum, reserve the assignment-relevant categories below; the exact final variable names should be consistent across `.env.example`, Compose, Kubernetes ConfigMap/Secret, and application settings.


Configuration categories that must be named consistently include:

```text
TRIAGE_PROVIDER
LLM_API_KEY
LLM_MODEL
OLLAMA_BASE_URL
REDIS_URL
DATABASE_URL / DB_DSN (choose one project-wide name)
```

The exact final set should be captured in `.env.example` and the ADR/config documentation. Do not create unrelated configuration variables unless a later requirement actually needs them.

## G2. Secret classification

| Configuration | Public in frontend? | Secret storage |
|---|---:|---|
| backend URL | no secret | runtime routing / nginx |
| LLM API key | no | `.env` locally / Kubernetes Secret / GitHub Secrets |
| DB password | no | `.env` locally / Kubernetes Secret / GitHub Secrets |
| JWT secret | no | secret store |
| non-secret provider/model settings | no | environment / ConfigMap |

Never put secrets into the frontend bundle.

Never commit real values into Kubernetes YAML. Committed manifests contain placeholders only.

---

# 10. Workstream H — Developer Tooling

The purpose of Milestone 1 tooling is to make broken conventions visible before implementation grows.

## H1. Backend

Configure:

- Python project metadata in `backend/pyproject.toml`;
- Ruff for linting/formatting;
- mypy for type checking;
- pytest for tests;
- pytest coverage configuration targeting `app/`.

Initial commands should be easy to remember, for example:

```text
ruff check .
ruff format --check .
mypy app
pytest
pytest --cov=app
```

The final commands may differ, but they must be documented and runnable locally.

## H2. Frontend

Configure:

- TypeScript;
- ESLint;
- TypeScript compiler checking with `tsc --noEmit`;
- Vitest;
- a component-test setup suitable for at least five meaningful tests later.

Initial commands:

```text
npm run lint
npm run typecheck
npm test
```

## H3. Contract-test strategy

Milestone 1 should add a small number of tests that verify the foundation rather than implementation behavior, such as:

- enum serialization is stable;
- invalid status transitions are represented by the transition table;
- `TriageResult` rejects invalid category/priority/confidence/summary values;
- provider factory rejects unknown `TRIAGE_PROVIDER` values.

Do not pad the test suite with trivial tests solely to increase test count.

---

# 11. Workstream I — ADRs & Architecture Documentation

Create these ADRs during Milestone 1 because later implementation depends on them.

## ADR 0001 — Provider Interface

Must explain:

- why the application depends on `TriageProvider` rather than a vendor SDK;
- why `LLM`, `Ollama`, `Rules`, and `Simulated` share the same interface;
- what `TriageResult` guarantees;
- why provider selection is configuration-driven.

Path:

```text
docs/adr/0001-provider-interface.md
```

## ADR 0002 — Frontend Runtime Configuration

Record:

- chosen option: nginx `/api` proxy;
- why Vite build-time API variables are not used for the backend endpoint;
- how the same image works in different environments;
- nginx request routing boundary.

Path:

```text
docs/adr/0002-frontend-runtime-config.md
```

## ADR 0003 — Deploy by SHA

Record the future deployment invariant:

```text
build once → push immutable image → deploy exact SHA/digest
```

Explain why `latest` may be pushed but must never be the deployment target.

Path:

```text
docs/adr/0003-deploy-by-sha.md
```

## ADR 0004 — PII & Data Governance

Define the decision boundary for complaint text and contact/location data:

- what data may leave the machine;
- which hosted provider receives it;
- why that exposure is acceptable or what minimization/redaction is required;
- what stays local when using Ollama;
- what must never be logged.

The assignment explicitly requires this decision because complaints may contain names, addresses, and phone numbers.

Path:

```text
docs/adr/0004-pii-and-data-governance.md
```

---

# 12. Milestone 1 Documentation Set

Create or reserve these project-state documents:

```text
docs/ARCHITECTURE.md
 docs/DEPENDENCIES.md
 docs/TASKS.md
 docs/DECISIONS.md
 docs/progress.md
```

Suggested roles:

| File | Purpose |
|---|---|
| `ARCHITECTURE.md` | Stable system architecture / source of truth |
| `DEPENDENCIES.md` | Which components depend on which contracts |
| `TASKS.md` | Current implementation queue / next actionable work |
| `DECISIONS.md` | Short index of decisions and links to ADRs |
| `progress.md` | What has been completed, current blockers, next milestone |

For Claude Code, keep `CLAUDE.md` short and stable. Put changing task state in `TASKS.md`/`progress.md` rather than repeatedly injecting the assignment into every session.

---

# 13. Milestone 1 Dependency Graph

```text
Repository + branch rules
          │
          ├───────────────┐
          ▼               ▼
   Domain contract    Deployment topology
          │               │
          ├──────┬────────┤
          ▼      ▼        ▼
      API       Triage   Runtime config
    contract   contract      │
          │      │           │
          └──────┴──────┬────┘
                         ▼
                 Tooling + ADRs
                         │
                         ▼
                 Milestone 1 Done
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        Backend      Frontend      DevOps
        Milestone 2  Milestone 5   Milestones 6–9
```

### Key principle

**Contracts are upstream dependencies.** Implementation should not silently redefine them.

---

# 14. Recommended Task Breakdown

## Phase 1 — Repository bootstrap

- [ ] Create repository.
- [ ] Create `dev` and protected `main`.
- [ ] Configure PR/review rules.
- [ ] Add `.gitignore` and `.env.example`.
- [ ] Add required directory structure.
- [ ] Add short `CLAUDE.md` and project-state files if using Claude Code.

## Phase 2 — Domain contracts

- [ ] Define category enum.
- [ ] Define priority enum.
- [ ] Define status enum.
- [ ] Define explicit transition table.
- [ ] Define complaint input validation.
- [ ] Define complaint persistence model.
- [ ] Define API error envelope.

## Phase 3 — API contract

- [ ] Write all ten endpoint contracts.
- [ ] Define request/response models.
- [ ] Define filters/pagination.
- [ ] Define exact success/error status codes.
- [ ] Define `/health` vs `/ready` semantics.
- [ ] Define `/metrics` and `/api/meta/providers` output responsibilities.

## Phase 4 — AI contract

- [ ] Create `TriageResult`.
- [ ] Create `TriageProvider` protocol.
- [ ] Create provider module skeletons.
- [ ] Define `TRIAGE_PROVIDER` selection.
- [ ] Define timeout/retry/fallback semantics.
- [ ] Define `triaged_by` values.
- [ ] Define deterministic CI strategy.

## Phase 5 — Runtime/deployment decisions

- [ ] Record nginx `/api` proxy decision.
- [ ] Record Compose network topology.
- [ ] Record hosted-LLM outbound path.
- [ ] Record persistent volumes.
- [ ] Record Compose dev/prod split.
- [ ] Record Kubernetes object topology.
- [ ] Record ingress/probes/replicas/HPA/VPA contracts.

## Phase 6 — Tooling

- [ ] Configure Ruff.
- [ ] Configure mypy.
- [ ] Configure pytest + coverage.
- [ ] Configure ESLint.
- [ ] Configure TypeScript checking.
- [ ] Configure Vitest.
- [ ] Confirm commands run locally.

## Phase 7 — Documentation/ADR review

- [ ] Write ADR 0001.
- [ ] Write ADR 0002.
- [ ] Write ADR 0003.
- [ ] Write ADR 0004.
- [ ] Update architecture/dependency/task/progress docs.
- [ ] Review for contradictions.

---

# 15. Definition of Done

Milestone 1 is **DONE** only when every item below is true.

### Repository

- [ ] Repository structure exists and matches the agreed architecture.
- [ ] `dev` → feature branches → `main` workflow is being used.
- [ ] `main` is protected and direct pushes are disabled.
- [ ] `.env`/secrets are excluded from Git.

### Contracts

- [ ] Domain enums are fixed.
- [ ] Validation rules are fixed.
- [ ] Complaint model is fixed.
- [ ] Status transition table is explicit.
- [ ] API endpoints and error behavior are fixed.
- [ ] Pagination contract is fixed.

### AI

- [ ] `TriageResult` is fixed.
- [ ] `TriageProvider` is fixed.
- [ ] Provider selection mechanism is fixed.
- [ ] Retry/fallback/cache/determinism semantics are documented.

### Frontend

- [ ] nginx `/api` proxy is the recorded runtime configuration decision.
- [ ] Backend remains the domain source of truth.
- [ ] OpenAPI → typed frontend client direction is fixed.

### Deployment

- [ ] Five-container Compose architecture is fixed.
- [ ] `edge`/`internal` network segmentation is fixed.
- [ ] Hosted LLM outbound path is explicitly resolved.
- [ ] Named persistence volumes are fixed.
- [ ] Kubernetes object topology is fixed.
- [ ] Probe responsibilities are fixed.
- [ ] HPA/VPA contracts are fixed.

### Tooling

- [ ] Backend lint/type/test commands work locally.
- [ ] Frontend lint/type/test commands work locally.
- [ ] Foundation tests exist for the most important contracts.

### Documentation

- [ ] Four required ADRs exist.
- [ ] `ARCHITECTURE.md`, `DEPENDENCIES.md`, `TASKS.md`, and `progress.md` are consistent.
- [ ] Every major decision has one authoritative location.
- [ ] No unresolved architectural contradiction remains between backend, frontend, Compose, and Kubernetes plans.

---

# 16. Review Checklist Before Starting Milestone 2

Ask these questions in the final Milestone 1 review:

1. **Can the frontend be implemented without inventing backend domain rules?**
2. **Can a backend developer implement all API routes without deciding new response shapes?**
3. **Can an AI-provider developer implement a provider without changing route/service contracts?**
4. **Can the same frontend image use `/api` in every environment?**
5. **Can the backend reach PostgreSQL, Redis, Ollama, and a hosted LLM without violating the network design?**
6. **Is it obvious which configuration is secret and which belongs in a ConfigMap/environment variable?**
7. **Can CI run deterministic triage without a live API key?**
8. **Would a new Claude Code session understand the current architecture by reading the repository docs rather than the full conversation?**
9. **Can both partners explain every Milestone 1 decision in the viva?**
10. **Does the repository contain any duplicate source of truth that should be removed now?**

If any answer is unclear, fix the contract/decision before beginning implementation-heavy work.

---

# 17. Handoff to Milestone 2

Milestone 2 starts from the following frozen inputs:

```text
Domain enums + validation
        ↓
Complaint model
        ↓
API contract
        ↓
Repository interfaces
        ↓
Service interfaces
        ↓
TriageProvider interface
        ↓
Runtime configuration
        ↓
Compose/Kubernetes topology
```

The next milestone can therefore implement PostgreSQL, Alembic, repositories, backend services, API routes, logging, health endpoints, seed data, and the core complaint lifecycle without reopening foundational architecture unless a genuine implementation constraint is discovered.

### Rule for later changes

If implementation reveals that a Milestone 1 decision must change:

```text
Identify constraint
      ↓
Update ADR / architecture
      ↓
Update contract-dependent files
      ↓
Review with partner
      ↓
Continue implementation
```

Do not silently change a contract in implementation code.
