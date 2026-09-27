# Milestone 2 — Database & Backend Core

## 1. Milestone Overview

**Goal:** Implement the CivicPulse backend core so it works end-to-end with PostgreSQL and satisfies the required four-layer backend structure.

This milestone covers only the **database, persistence, backend service layer, complaint lifecycle, health/readiness, observability, graceful shutdown, and seed system** requirements defined in Assignment 1.

### Assignment 1 requirements covered

- PostgreSQL 16 with Alembic migrations.
- Required complaint schema, enums, constraints, timestamps, and indexes.
- Repository layer containing all SQL access.
- Backend service layer containing business rules.
- Complaint creation, retrieval, listing, filtering, pagination, and status transitions.
- Required backend API endpoints and status codes.
- `/health` and `/ready` semantics.
- Structured JSON logging and request IDs.
- SIGTERM graceful shutdown.
- Idempotent complaint seed data.
- Deterministic backend testing and the required backend coverage target.

> **Out of scope for this milestone:** frontend implementation, Docker/Compose, Kubernetes, CI/CD, Redis cache/rate limiting, LLM provider implementations, and ADRs/architecture decisions. Those requirements belong to other parts of Assignment 1.

---

## 2. Required Backend Structure

The backend must follow the four layers required by Assignment 1:

```text
app/
├── routes/
├── services/
├── repositories/
└── providers/
```

The dependency responsibilities are:

| Layer | Responsibility |
|---|---|
| `routes/` | HTTP concerns: parse input, validate, call services, serialize responses, and return correct HTTP status codes |
| `services/` | Business rules: complaint workflow, triage orchestration, state transitions, and statistics-related business logic |
| `repositories/` | Persistence: all SQL/database access |
| `providers/` | Outbound integrations, including the interfaces used for external capabilities |

### Layering acceptance criteria

- No SQL is written in route handlers.
- Routes do not open database sessions directly.
- Business rules are not implemented in route handlers.
- Database operations required by the backend are accessed through repositories.
- HTTP-specific concerns remain in the route layer.
- Service-layer behavior can be tested without coupling business rules to HTTP handlers.

These requirements directly support the Assignment 1 backend rubric requirement for **four-layer separation**. fileciteturn0file0L76-L88

---

# 3. PostgreSQL and Alembic

## 3.1 PostgreSQL

Use **PostgreSQL 16** as the backend database.

The database must persist complaint records across application restarts.

The database schema must be managed through **Alembic migrations**.

### Required migration behavior

- Create the complete complaint schema through versioned Alembic migrations.
- Do not create application tables through application startup code.
- Migrations must represent reviewable, versioned schema changes.
- The application must be able to start against a database whose schema has been established by the migrations.

Assignment 1 explicitly requires Alembic migrations and prohibits `CREATE TABLE` in application startup code. fileciteturn0file0L123-L149

## 3.2 Migration deliverables

```text
backend/
└── alembic/
    └── versions/
        └── <migration files>
```

The milestone is complete only when the schema can be created and upgraded using the project's migration process rather than application startup DDL.

---

# 4. Database Schema

Implement the minimum complaint schema specified by Assignment 1.

## 4.1 Complaint fields

| Field | Required behavior |
|---|---|
| `id` | UUID, server-generated |
| `text` | 10–2000 characters; enforce in both application validation and database constraints |
| `location` | 3–200 characters |
| `reporter_contact` | Nullable |
| `category` | Enum: `water`, `electricity`, `sanitation`, `roads`, `streetlights`, `other` |
| `priority` | Enum: `high`, `normal`, `low` |
| `status` | Enum: `open`, `in_progress`, `resolved`, `rejected`; default `open` |
| `ai_summary` | Nullable; one line; maximum 140 characters |
| `triaged_by` | `llm:groq`, `llm:ollama`, `rules`, or `rules:fallback` |
| `triage_latency_ms` | Integer |
| `created_at` | UTC `timestamptz` |
| `updated_at` | UTC `timestamptz` |

The schema must preserve the distinctions between application-level validation and database-level enforcement. In particular, complaint text length must be enforced by the database as well as by the application. fileciteturn0file0L127-L145

## 4.2 Enumerations

The following values are fixed by Assignment 1:

### Category

```text
water
electricity
sanitation
roads
streetlights
other
```

### Priority

```text
high
normal
low
```

### Status

```text
open
in_progress
resolved
rejected
```

### Triage provider value

```text
llm:groq
llm:ollama
rules
rules:fallback
```

Do not introduce additional domain values that conflict with the Assignment 1 contract.

---

# 5. Constraints

Implement database constraints corresponding to the required domain rules.

## 5.1 Complaint text

`text` must accept only values within the required range:

```text
minimum: 10 characters
maximum: 2000 characters
```

This must be enforced at the database level as required by Assignment 1.

## 5.2 Location

`location` must satisfy:

```text
minimum: 3 characters
maximum: 200 characters
```

## 5.3 AI summary

`ai_summary` is nullable, but when present it must not exceed:

```text
140 characters
```

## 5.4 Status

`status` must contain only one of the four defined status values.

New complaints default to:

```text
open
```

## 5.5 Category and priority

`category` and `priority` must be restricted to their Assignment 1 enum values.

## 5.6 Timestamps

`created_at` and `updated_at` must use UTC-capable `timestamptz` values.

---

# 6. Indexes

Create the two required indexes specified by Assignment 1:

1. An index on:

```text
(status, priority)
```

2. An index on:

```text
created_at
```

Each index must have a documented query purpose in the project's engineering notes.

Assignment 1 specifically requires these indexes and requires the query served by each index to be explained. fileciteturn0file0L145-L151

### Required verification

The implementation should make it possible to demonstrate that:

- status/priority filtering can use the `(status, priority)` index;
- complaint ordering/time-based retrieval can use the `created_at` index.

Do not add unexplained indexes as part of this milestone.

---

# 7. Repository Layer

All SQL access must be implemented through repositories.

Repositories are responsible for persistence operations such as:

- creating complaints;
- retrieving a complaint by ID;
- listing complaints;
- applying category filters;
- applying priority filters;
- applying status filters;
- applying pagination;
- obtaining the total result count required by the API;
- persisting status changes;
- supporting the data required by backend statistics.

## 7.1 Repository expectations

Repository methods should expose persistence operations to the service layer without moving business rules into SQL or route handlers.

The route layer must never contain direct SQL access.

## 7.2 Required complaint persistence operations

The complaint repository must support at least:

```text
create complaint
get complaint by ID
list complaints with filters and pagination
count matching complaints
update complaint status
```

The exact method names are an implementation detail and are not prescribed by Assignment 1.

---

# 8. Backend Service Layer

The service layer owns backend business rules.

At minimum, it must coordinate:

- complaint creation;
- complaint retrieval;
- complaint listing;
- filtering;
- pagination;
- status transition validation;
- persistence of valid state changes;
- the complaint information returned by the API.

The service layer must not turn route handlers into business-rule implementations.

---

# 9. Complaint Creation

Implement:

```http
POST /api/complaints
```

## Required behavior

The creation flow must:

1. Validate the incoming complaint.
2. Triage the complaint through the backend's triage abstraction.
3. Persist the complaint.
4. Return the created complaint.
5. Return HTTP `201` on successful creation.

Assignment 1 defines this endpoint as:

```text
Validate → triage → persist
```

and requires `201` for successful creation. fileciteturn0file0L90-L108

## Validation failure

Invalid input must return:

```text
400
```

with a **field-level error body**.

Validation must cover the server-side rules required by the complaint schema.

The frontend may mirror these rules later, but backend validation remains authoritative.

---

# 10. Complaint Retrieval

Implement:

```http
GET /api/complaints/{id}
```

## Required behavior

- Return `200` when the complaint exists.
- Return `404` when the complaint does not exist.
- Return the complaint representation required by the API contract.

Assignment 1 explicitly requires `200 / 404` behavior for this endpoint. fileciteturn0file0L95-L104

---

# 11. Complaint Listing

Implement:

```http
GET /api/complaints
```

The endpoint must support:

- category filtering;
- priority filtering;
- status filtering;
- pagination;
- total result count.

## 11.1 Filters

Supported filters:

```text
category
priority
status
```

The filters must correspond to the defined database enums.

## 11.2 Pagination

The endpoint must accept:

```text
page
page_size
```

`page_size` must not exceed:

```text
100
```

The response must include the total number of matching records.

Assignment 1 requires a paginated, filterable complaint list with `page_size ≤ 100` and a returned total. fileciteturn0file0L102-L104

## 11.3 Expected query behavior

The repository must apply filters and pagination at the database level rather than loading the complete complaint table and filtering it in application memory.

---

# 12. Complaint Status State Machine

Status transitions are a required business rule.

## 12.1 Allowed transitions

```text
open
 ├──→ in_progress
 └──→ rejected

in_progress
 ├──→ resolved
 └──→ rejected

resolved
 └── terminal

rejected
 └── terminal
```

Equivalent transition table:

| Current status | Allowed next status |
|---|---|
| `open` | `in_progress`, `rejected` |
| `in_progress` | `resolved`, `rejected` |
| `resolved` | none |
| `rejected` | none |

Assignment 1 requires this state machine and explicitly states that `resolved` and `rejected` are terminal states. fileciteturn0file0L115-L119

## 12.2 Invalid transitions

Implement:

```http
PATCH /api/complaints/{id}/status
```

Invalid transitions must:

- return HTTP `409`;
- name the attempted transition in the error response;
- leave the complaint status unchanged.

The transition logic must be represented as an **explicit transition table**, not an unstructured chain of conditional statements.

## 12.3 Valid transitions

Valid transitions must:

- update the persisted status;
- update `updated_at`;
- return the resulting complaint/status representation according to the API contract.

---

# 13. Backend API Contract

The milestone must implement the backend endpoints required by Assignment 1 that belong to the database/backend core.

| Method | Path | Required behavior |
|---|---|---|
| `POST` | `/api/complaints` | Validate → triage → persist; `201`; validation failures `400`; rate limiting is handled by the cache/rate-limit milestone |
| `GET` | `/api/complaints/{id}` | `200` / `404` |
| `GET` | `/api/complaints` | Category, priority, and status filters; pagination; `page_size ≤ 100`; total |
| `PATCH` | `/api/complaints/{id}/status` | Enforce state machine; invalid transition `409` naming attempted transition |
| `GET` | `/health` | Liveness; must not touch PostgreSQL |
| `GET` | `/ready` | Readiness; PostgreSQL and Redis reachability determine readiness |
| `GET` | `/api/stats` | Backend endpoint contract exists; Redis caching belongs to the cache milestone |
| `GET` | `/api/meta/providers` | Provider/triage observability endpoint; full provider behavior belongs to the AI milestone |
| `GET` | `/metrics` | Prometheus-format metrics; bonus/observability work may extend this later |

The complete endpoint contract is defined in Assignment 1. fileciteturn0file0L90-L109

---

# 14. Health and Readiness

Implement the two endpoints as separate concepts.

## 14.1 `/health`

```http
GET /health
```

Purpose:

```text
Liveness
```

Required behavior:

- confirms that the backend process is alive;
- must **not** access PostgreSQL.

A database outage must not cause `/health` to become a database query.

## 14.2 `/ready`

```http
GET /ready
```

Purpose:

```text
Readiness
```

Required behavior:

- return `200` only when PostgreSQL and Redis are reachable;
- return `503` when a required dependency is unavailable;
- identify the failed dependency in the response.

Assignment 1 explicitly separates liveness from readiness because they produce different operational consequences. fileciteturn0file0L107-L113

> Redis connectivity is part of the readiness contract even though Redis cache/rate-limiter implementation is outside the core database portion of this milestone. The readiness endpoint must follow the Assignment 1 contract.

---

# 15. Structured Logging

Implement structured logging in JSON format.

## Required behavior

- Logs must be written to **stdout**.
- Do not write application logs to files.
- Every log line must carry a `request_id`.
- The request ID must come from `X-Request-ID` when supplied.
- Generate a request ID when the request does not contain one.
- Propagate the request ID through the request lifecycle.

Assignment 1 requires JSON logs to stdout and request ID propagation through `X-Request-ID`. fileciteturn0file0L119-L121

## Triage fallback logging

For each triage fallback, emit one `WARNING` containing:

- complaint ID;
- provider;
- error class.

The fallback warning must not expose secrets such as an LLM API key.

---

# 16. Request IDs

The backend must establish a request ID for every request.

### Required behavior

```text
Incoming X-Request-ID
        ↓
use supplied value
```

or:

```text
No X-Request-ID
        ↓
generate request ID
```

The request ID must then be available to the backend logging context.

The behavior must be consistent across successful requests and error responses.

---

# 17. Graceful Shutdown

Handle `SIGTERM` gracefully.

The shutdown behavior must:

1. stop accepting new requests;
2. allow in-flight requests to finish;
3. close database pool connections;
4. exit cleanly.

Assignment 1 requires SIGTERM handling specifically to prevent live requests from being dropped during deployment/termination. fileciteturn0file0L117-L121

### Acceptance criteria

A shutdown test or demonstrable procedure should establish that:

- the process receives SIGTERM;
- existing work is allowed to drain;
- database connections are closed;
- the process exits rather than hanging indefinitely.

---

# 18. Idempotent Seed System

Create a seed command that loads realistic complaint data.

## Required seed data

The seed must contain:

- **at least 30 complaints**;
- realistic municipal complaint text;
- **Urdu-influenced English**;
- complaints distributed across the required categories.

The data should exercise the complaint domain rather than consisting of repetitive placeholder records.

Assignment 1 explicitly requires ≥30 realistic complaints spread across categories. fileciteturn0file0L149-L153

## Idempotency requirement

Running the seed command multiple times must not create duplicate complaint rows.

Required behavior:

```text
first run  → seed data inserted
second run → no duplicate seed rows
third run  → no duplicate seed rows
```

The seed operation must therefore be safe to execute repeatedly.

## Seed verification

Demonstrate that:

1. the database is initially empty or contains no seed records;
2. the seed command inserts at least 30 complaints;
3. running the same seed command again does not duplicate them;
4. the resulting complaint data remains usable by the listing/filtering endpoints.

---

# 19. Persistence Verification

The database must provide durable persistence.

## Required verification

The backend must preserve complaint records across the database lifecycle required by Assignment 1.

At minimum, verify the persistence requirement represented by:

```text
docker compose down
docker compose up
```

The complaint rows must remain available after the restart.

Assignment 1 also requires PostgreSQL data to survive deletion of the PostgreSQL pod when deployed to Kubernetes; that infrastructure demonstration belongs to the Kubernetes milestone, but the backend schema must be compatible with that persistence requirement. fileciteturn0file0L151-L153

---

# 20. Error Handling

Implement basic backend error handling consistent with the API contract.

## Required error cases

At minimum:

| Situation | HTTP status |
|---|---:|
| Invalid complaint input | `400` |
| Complaint not found | `404` |
| Invalid status transition | `409` |
| Readiness dependency failure | `503` |

### Error response requirements

- Validation errors should identify the relevant field(s).
- Invalid status transition errors must name the attempted transition.
- Dependency/readiness errors must identify the failed dependency.
- Errors must not expose credentials, API keys, database passwords, or other secrets.
- Unexpected internal errors must not be returned as raw stack traces to API clients.

---

# 21. Backend Testing

Testing is part of the milestone, not a follow-up task.

Assignment 1 requires:

- at least **14 backend tests**;
- unit and integration coverage;
- deterministic tests;
- coverage of at least **65% of `app/`**. fileciteturn0file0L423-L437

## 21.1 Required test areas

### Database and repositories

Test:

- complaint creation;
- retrieval by ID;
- missing complaint;
- listing;
- category filtering;
- priority filtering;
- status filtering;
- pagination;
- total count;
- status persistence.

### Service layer

Test:

- complaint creation orchestration;
- valid status transitions;
- invalid transitions;
- terminal statuses;
- appropriate error behavior.

### API

Test:

- successful complaint creation;
- invalid request validation;
- complaint retrieval;
- missing complaint;
- filtered listing;
- pagination;
- invalid status transition returning `409`;
- `/health`;
- `/ready` dependency failure behavior.

### Observability and lifecycle

Test or otherwise verify:

- request ID generation;
- preservation of a supplied `X-Request-ID`;
- structured logging behavior;
- graceful shutdown behavior.

---

# 22. Deterministic Backend Tests

Backend tests must not depend on a live, nondeterministic LLM provider.

Assignment 1 requires CI to use deterministic triage behavior and specifically requires testing fallback behavior with an injected failing provider. fileciteturn0file0L226-L232

## Mandatory fallback test

Implement the required test:

```text
Given a triage provider that always raises,
POST /api/complaints
→ returns 201
→ triaged_by == "rules:fallback"
```

This test must be deterministic and must not depend on network timing or an external provider.

---

# 23. Acceptance Criteria

Milestone 2 is complete when all of the following are true.

## Database

- [ ] PostgreSQL 16 is used.
- [ ] Alembic manages the schema.
- [ ] No application startup code creates database tables.
- [ ] Complaint schema contains every required field.
- [ ] Required enums are enforced.
- [ ] `text` is constrained to 10–2000 characters in the database and application.
- [ ] `location` supports the required 3–200 character range.
- [ ] `ai_summary` is nullable and limited to 140 characters.
- [ ] `status` defaults to `open`.
- [ ] `created_at` and `updated_at` use UTC `timestamptz`.
- [ ] `(status, priority)` index exists.
- [ ] `created_at` index exists.
- [ ] Each required index has a named query justification.

## Repositories and services

- [ ] All SQL access is in repositories.
- [ ] Complaint persistence operations are implemented.
- [ ] Service layer contains complaint business rules.
- [ ] Routes do not open database sessions directly.
- [ ] Routes do not contain business-rule implementations.

## Complaint API

- [ ] `POST /api/complaints` returns `201` on successful creation.
- [ ] Invalid complaint input returns `400` with field-level errors.
- [ ] `GET /api/complaints/{id}` returns `200` for an existing complaint.
- [ ] `GET /api/complaints/{id}` returns `404` for a missing complaint.
- [ ] `GET /api/complaints` supports category filtering.
- [ ] `GET /api/complaints` supports priority filtering.
- [ ] `GET /api/complaints` supports status filtering.
- [ ] Pagination supports `page` and `page_size`.
- [ ] `page_size` cannot exceed 100.
- [ ] Listing returns the total number of matching records.
- [ ] `PATCH /api/complaints/{id}/status` enforces the required state machine.
- [ ] Invalid transitions return `409`.
- [ ] Invalid transition errors identify the attempted transition.
- [ ] `resolved` and `rejected` are terminal.

## Health and lifecycle

- [ ] `/health` confirms process liveness.
- [ ] `/health` does not touch PostgreSQL.
- [ ] `/ready` checks PostgreSQL and Redis reachability.
- [ ] `/ready` returns `503` for a failed dependency.
- [ ] `/ready` identifies the failed dependency.
- [ ] SIGTERM stops new work, drains in-flight requests, closes database pools, and exits cleanly.

## Logging

- [ ] Logs are structured JSON.
- [ ] Logs go to stdout.
- [ ] Every request has a request ID.
- [ ] Incoming `X-Request-ID` is preserved.
- [ ] Missing request IDs are generated.
- [ ] Triage fallback produces one warning with complaint ID, provider, and error class.
- [ ] Secrets are never logged.

## Seed

- [ ] Seed command creates at least 30 realistic complaints.
- [ ] Seed data uses Urdu-influenced English.
- [ ] Seed data spans the required categories.
- [ ] Running the seed twice does not duplicate rows.

## Tests

- [ ] At least 14 backend tests exist.
- [ ] Unit and integration tests are included.
- [ ] Tests are deterministic.
- [ ] `app/` coverage is at least 65%.
- [ ] The mandatory triage-fallback test passes.

---

# 24. Suggested Implementation Order

This order follows the dependencies between the required backend deliverables without introducing additional architecture decisions.

### Step 1 — Database foundation

- Define the complaint schema.
- Define enums and constraints.
- Create Alembic migration(s).
- Create the required indexes.
- Verify migration application.

### Step 2 — Repository operations

- Implement complaint creation.
- Implement complaint retrieval.
- Implement complaint listing.
- Implement filtering.
- Implement pagination and total count.
- Implement status persistence.

### Step 3 — Service behavior

- Implement complaint creation workflow.
- Implement retrieval and listing workflows.
- Implement explicit status transition validation.
- Implement terminal-state handling.

### Step 4 — HTTP API

- Implement complaint endpoints.
- Implement validation and error responses.
- Implement health and readiness endpoints.

### Step 5 — Observability and lifecycle

- Add request IDs.
- Add structured JSON logging.
- Add triage fallback warning behavior.
- Add graceful SIGTERM shutdown.

### Step 6 — Seed system

- Create realistic seed data.
- Make the seed operation idempotent.
- Verify repeated execution.

### Step 7 — Testing and verification

- Add repository tests.
- Add service tests.
- Add API integration tests.
- Add health/readiness tests.
- Add request-ID/logging tests.
- Add the mandatory fallback test.
- Verify coverage reaches at least 65%.
- Run the complete backend test suite against PostgreSQL.

---

# 25. Definition of Done

Milestone 2 is considered **done** only when a clean backend environment can:

```text
apply Alembic migrations
        ↓
start the backend
        ↓
connect to PostgreSQL
        ↓
seed ≥ 30 complaints idempotently
        ↓
create a complaint
        ↓
retrieve it by ID
        ↓
list/filter/paginate complaints
        ↓
transition its status according to the state machine
        ↓
reject invalid transitions with 409
        ↓
report correct health/readiness state
        ↓
produce structured logs with request IDs
        ↓
handle SIGTERM gracefully
        ↓
pass the deterministic backend test suite
```

The milestone must satisfy the backend and data-layer requirements of Assignment 1 without introducing architecture decisions that belong in the assignment's ADRs.

## Assignment 1 Traceability

| Milestone 2 area | Assignment 1 source |
|---|---|
| Four backend layers | §2.2 Backend layer |
| API endpoints | §2.2 API contract |
| Status state machine | §2.2 Domain rules |
| Health/readiness | §2.2 API contract + domain rules |
| Structured logging/request IDs | §2.2 Domain rules |
| Graceful shutdown | §2.2 Domain rules |
| PostgreSQL/Alembic | §2.3 Data layer |
| Complaint schema | §2.3 Data layer |
| Required indexes | §2.3 Data layer |
| Idempotent seed | §2.3 Data layer |
| Backend test requirements | Rubric §C |
| Alembic/schema/index/seed requirements | Rubric §D |

The authoritative requirements remain those in Assignment 1. fileciteturn0file0L423-L449
