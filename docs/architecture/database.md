# Database Architecture

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

PostgreSQL 16 durably persists complaints and is the system's sole source of truth. Schema is managed exclusively through Alembic migrations, never through application startup code.

## 1. Complaint entity

Required persisted fields:

| Field | Type / rule |
|---|---|
| `id` | server-generated UUID |
| `text` | 10–2000 chars; enforce in app and DB |
| `location` | 3–200 chars |
| `reporter_contact` | nullable |
| `category` | `water`, `electricity`, `sanitation`, `roads`, `streetlights`, `other` |
| `priority` | `high`, `normal`, `low` |
| `status` | `open`, `in_progress`, `resolved`, `rejected`; default `open` |
| `ai_summary` | nullable; max 140 chars |
| `triaged_by` | `llm:groq`, `rules`, `rules:fallback` |
| `triage_latency_ms` | integer |
| `created_at` | UTC `timestamptz` |
| `updated_at` | UTC `timestamptz` |

Status transition rules live in [`backend.md`](backend.md) §Status State Machine — the state machine is application logic, not a schema constraint.

## 2. Migration strategy

Schema changes are managed exclusively through Alembic. Never create schema objects as part of application startup, and never run migrations implicitly from the backend's own startup path — a migration is a versioned, reviewable, reversible step with its own success/failure signal, not something silently folded into `CMD`.

```text
code change
   ↓
Alembic revision
   ↓
CI/test migration
   ↓
deployment migration process
```

**Migration runner: a dedicated job in every environment, never the application process.**

- **Docker Compose** (`compose.yaml` and `compose.prod.yaml`): a one-off `migrate` service, built from the same backend image, with `command: alembic upgrade head`. The `backend` service depends on it via `depends_on: { migrate: { condition: service_completed_successfully } }`, so the app container never starts against an unmigrated schema. `migrate` runs once per `up` and exits; it is not a long-running service. See [`docker-compose.md`](docker-compose.md).
- **Kubernetes** (`k8s/base/migrate-job.yaml`): a `batch/v1` `Job` running the same backend image with `command: ["alembic", "upgrade", "head"]`, using the same `ConfigMap`/`Secret` as the backend Deployment for DB credentials, and `ttlSecondsAfterFinished: 300` so completed runs are garbage-collected. A `Job`'s pod template is immutable, so `cd.yml`'s migrate step deletes any existing `job/migrate` (`kubectl delete job/migrate -n civicpulse --ignore-not-found`) before applying the new one — otherwise re-applying the same Job name on a second deploy fails outright rather than re-running with the new image. It then waits for the fresh Job to reach `Complete` (`kubectl wait --for=condition=complete job/migrate`) **before** waiting on the backend Deployment's rollout status. See [`kubernetes.md`](kubernetes.md) and [`cicd.md`](cicd.md).
- A `Job` (not an `initContainer` on the backend pod) is used deliberately: with ≥2 backend replicas, per-pod `initContainer`s would race each other to apply the same revision concurrently. A single `Job` runs the migration exactly once, with one clear success/failure signal the pipeline can wait on, decoupled from pod lifecycle and rollout count.

The application process itself must not silently issue `CREATE TABLE`/DDL during startup, and must not run `alembic upgrade head` itself either — schema readiness is guaranteed by the `migrate` service/Job completing first, not by the backend.

## 3. Required indexes

1. `(status, priority)` — supports dashboard filtering by operational state and priority.
2. `created_at` — supports chronological listing/order (`created_at DESC`, the dashboard's default) and recent-record access.

Each index must have a named query/explanation in `docs/ENGINEERING-NOTES.md`.

## 4. Seed data

Seed requirements: at least 30 realistic complaints; Urdu-influenced English style; spread across categories; idempotent.

Running the seed twice must leave the database with no duplicate seed rows.

## 5. Persistence invariant

The database must survive:

- `docker compose down` followed by `up`;
- deletion of the PostgreSQL Kubernetes pod.

Compose uses the `pgdata` volume; Kubernetes uses a StatefulSet with a persistent volume claim (see [`kubernetes.md`](kubernetes.md) — a plain Deployment without persistent storage is explicitly a marked failure in the assignment).

## 6. Caching, database, and request consistency

A complaint mutation has two durable/derived outputs:

1. PostgreSQL is the source of truth for complaint data.
2. Redis contains derived/temporary values such as stats and triage cache entries (see [`cache.md`](cache.md)).

The consistency rule is:

```text
PostgreSQL commit succeeds
        ↓
derived stats cache invalidated
        ↓
next stats request recomputes from PostgreSQL
```

The Redis cache must never become the source of truth for complaint records. Similarly, a cached AI result may avoid repeated inference, but the final complaint row in PostgreSQL remains authoritative for what the application returned and stored.

## 7. Invariants checklist

- [ ] PostgreSQL 16.
- [ ] Alembic migrations.
- [ ] No startup DDL; backend process never runs migrations itself.
- [ ] Migrations run via dedicated `migrate` Compose service / k8s `Job/migrate`, gated before the app receives traffic.
- [ ] Required schema constraints and indexes exist.
- [ ] Seed is idempotent and ≥30 records.
- [ ] PostgreSQL data survives restarts/pod deletion.
