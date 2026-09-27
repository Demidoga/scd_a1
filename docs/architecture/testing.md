# Testing Architecture

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

CI must be deterministic and green on every run, including for the AI layer, which is probabilistic in production. This is achieved by design (dependency injection, `SimulatedTriage`), not by luck or retries.

## 1. Backend unit tests

Cover at minimum: domain validation; transition table ([`backend.md`](backend.md)); rate-limit behavior ([`cache.md`](cache.md)); triage provider factory ([`ai.md`](ai.md)); malformed AI output; retry classification; fallback logic; content-hash cache behavior; stats cache hit/miss; request ID behavior; readiness/liveness semantics.

## 2. Backend integration tests

Verify the actual component path with PostgreSQL/Redis where appropriate.

Important end-to-end contract:

```text
POST complaint
  → triage
  → persist
  → 201
GET complaint
  → same persisted result
```

Required high-value test:

```text
provider always raises
  → POST still returns 201
  → triaged_by == rules:fallback
```

## 3. Frontend component tests

At least five meaningful tests, including behavior around: form validation; loading state; successful triage result rendering; dashboard filters/pagination; 409 message rendering; stats cache state. See [`frontend.md`](frontend.md).

## 4. Deterministic CI

No CI test should depend on: a real hosted LLM; external rate limits; variable latency; time-based waiting hacks.

Use `SimulatedTriage` and dependency injection for failure scenarios (see [`ai.md`](ai.md) §Deterministic CI).

## 5. Where these run

Both suites run in `ci.yml` on every PR to `main` and every push to `dev`, and again in `cd.yml`'s `test` job on the merged result before publishing. Coverage gate: ≥65% on backend `app/`. Full pipeline: [`cicd.md`](cicd.md).
