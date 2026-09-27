# Cache & Rate-Limiter Architecture (Redis)

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

Redis 7 has two distinct application responsibilities, deliberately: read-through caching for `/api/stats`, and a distributed rate limiter protecting the AI/free-tier budget on `POST /api/complaints`. The triage content-hash cache is also Redis-backed but is documented in [`ai.md`](ai.md) since it's part of the triage reliability pipeline.

## 1. Responsibility A — stats cache

Endpoint: `GET /api/stats`.

Policy:

- read-through cache;
- TTL: 30 seconds;
- return `X-Cache: HIT` when served from Redis;
- return `X-Cache: MISS` when data was computed and populated;
- explicitly invalidate after a complaint write/status change that changes aggregates.

Flow:

```text
GET /api/stats
   ↓
Redis lookup
   ├── HIT → return cached aggregate + X-Cache:HIT
   └── MISS
        ↓
      SQL aggregate query
        ↓
      Redis set EX 30
        ↓
      X-Cache:MISS
```

Write path:

```text
successful complaint/status mutation
   ↓
repository transaction
   ↓
invalidate stats key
```

The cache therefore provides both TTL-based recovery and immediate correctness after writes. Full source-of-truth reasoning: [`database.md`](database.md) §Caching, database, and request consistency.

## 2. Responsibility B — distributed IP rate limiter

Target endpoint: `POST /api/complaints`. Key: client IP.

**Algorithm and threshold:** fixed-window, **10 requests per 60 seconds per client IP**. Fixed-window is simpler to implement and to explain at viva than token-bucket, and the assignment permits either. The threshold is generous enough that a real citizen submitting a couple of complaints never notices it, and tight enough that a single misbehaving client can't exhaust Groq's shared, org-wide free-tier quota on its own. This is invoked as the routes-level rate-limiter dependency described in [`backend.md`](backend.md)'s named exception, not through `services/`.

**Atomicity.** A plain `INCR` followed by a separate `EXPIRE` is not safe: a crash or connection drop between the two commands leaves the key with no TTL, permanently locking that IP out. Use a single atomic operation instead — a Lua script executed via `EVAL` (increment, and set the expiry only on the request that creates the key, in one round trip):

```lua
local count = redis.call("INCR", KEYS[1])
if count == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return count
```

A `MULTI`/`EXEC` pipeline is *not* sufficient on its own (a pipeline is not conditional — it would reset the TTL on every request, turning the fixed window into a sliding one). The Lua script is the correct, single-round-trip, race-free implementation and is the standard pattern Redis's own documentation recommends for exactly this use case.

Required result when exceeded: HTTP `429 Too Many Requests`; `Retry-After` header; no AI invocation should occur after rate-limit rejection.

The limiter must live in Redis rather than process memory because the backend is horizontally scalable. With two or more backend replicas, an in-process counter would create independent limits per pod.

### Rate-limit failure mode

```text
Redis limiter → limit exceeded → 429 + Retry-After
```

No AI call and no complaint write should occur for the rejected request.

### When Redis itself is unreachable: fail closed

`POST /api/complaints` returns `503` rather than proceeding without a rate check. This matches the limiter's actual purpose — protecting the shared Groq free-tier quota — an outage window is exactly when unlimited traffic is least affordable. In Kubernetes this is a narrow window in practice, since `/ready` is already pulling the pod from the Service the moment Redis becomes unreachable (see [`backend.md`](backend.md)); in Compose, where there is no readiness-based routing, this is the only protection during a Redis outage.

Contrast this with the stats cache above and the triage cache ([`ai.md`](ai.md)), which degrade gracefully to direct PostgreSQL reads / direct provider calls on a Redis miss or outage — those are pure optimizations with no cost-control role, so failing open there is correct and does not need the same fail-closed treatment.

## 3. Redis persistence

Redis uses AOF on a named volume (`redisdata` in Compose).

The engineering notes should explicitly justify why AOF persistence is useful even though Redis is used primarily as a cache/rate-limiter store.

## 4. Kubernetes rollout note

Redis is a `Deployment` (not `StatefulSet`) with a PVC in Kubernetes, and uses `strategy: Recreate` to avoid a rollout deadlock on the ReadWriteOnce volume — full reasoning in [`kubernetes.md`](kubernetes.md).

## 5. Invariants checklist

- [ ] Stats cache TTL = 30s.
- [ ] `X-Cache` exposes HIT/MISS.
- [ ] Stats cache invalidates on writes.
- [ ] Distributed rate limiter uses Redis (atomic Lua increment, not INCR+EXPIRE).
- [ ] 429 includes `Retry-After`.
- [ ] Rate limiter fails closed (503) when Redis is unreachable.
- [ ] Stats/triage caches fail open (degrade to direct query/provider call) when Redis is unreachable.
- [ ] AOF persistence is enabled and justified.
