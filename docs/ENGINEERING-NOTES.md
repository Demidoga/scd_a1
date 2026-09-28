# Engineering Notes

Running log of decisions, discrepancies, and justifications that don't
belong in the frozen `docs/architecture/*.md` spec files but need to be
on record for review/viva. Organized by milestone.

---

## Milestone 1 — Foundation

### Assignment brief's "10 endpoints" vs. the actual 9

`docs/architecture/backend.md` §3 already flags this: the assignment brief's
API contract table lists 9 endpoints (`POST /api/complaints`,
`GET /api/complaints/{id}`, `GET /api/complaints`,
`PATCH /api/complaints/{id}/status`, `GET /api/stats`,
`GET /api/meta/providers`, `GET /health`, `GET /ready`, `GET /metrics`), but
rubric Part C references "all ten endpoints to contract." No tenth endpoint
appears anywhere else in the assignment text. Treated as a counting slip in
the brief; all 9 documented endpoints are implemented
(`backend/app/routes/`). Noting it here so it reads as noticed-and-resolved
at viva, not an oversight.

### No-Ollama scope reduction

`docs/architecture/ai.md` §0 already documents the instructor-approved
decision to implement a single live triage path (hosted Groq) instead of
both hosted and local (Ollama) paths. `TriageProvider` has 3 implementations
(`LLMTriage`, `RuleBasedTriage`, `SimulatedTriage`), satisfying the rubric's
"≥ 3 implementations" requirement. Flagging again here because
`docs/Milestones/milestone-3.md` (written before this decision) still lists
`OllamaTriage` as required — that milestone doc is superseded by
`docs/architecture/ai.md` §0 and `CLAUDE.md` on this point.

## Milestone 2 — Database & Backend Core

### Required indexes and the queries they serve

1. **`ix_complaints_status_priority` on `(status, priority)`** — serves the
   operations dashboard's primary filter query,
   `GET /api/complaints?status=...&priority=...`
   (`app/repositories/complaints.py::list_complaints`), which filters on
   both columns together. A composite index lets Postgres satisfy that
   WHERE clause with a single index scan instead of two separate scans
   merged in memory.
2. **`ix_complaints_created_at` on `created_at`** — serves the default list
   ordering (`ORDER BY created_at DESC`, `docs/architecture/backend.md` §3.2)
   and any "most recent N complaints" query, including
   `GET /api/meta/providers`'s "last 20 triage outcomes"
   (`ComplaintRepository.recent`).

Verified via `EXPLAIN`-style reasoning rather than a captured plan in this
document: both indexes exist on the live schema (see
`backend/alembic/versions/0001_create_complaints.py`) and `alembic check`
confirms the migration matches the ORM model with zero drift.

### `triaged_by` allows `simulated`, not just the three values database.md lists

`docs/architecture/database.md` §1 lists `triaged_by` as
`llm:groq | rules | rules:fallback`. That table predates the Milestone 1
no-Ollama scope decision and was never updated to account for
`TRIAGE_PROVIDER=simulated` being the CI/dev default — under a strict
reading, a successful `simulated` triage would have nowhere valid to record
itself. The `ck_complaints_triaged_by_enum` CHECK constraint
(`app/repositories/models.py`) therefore allows
`('llm:groq', 'rules', 'rules:fallback', 'simulated')`. This is a resolved
documentation gap, not a silent deviation — noted here and in
`app/repositories/models.py`'s module docstring.

### PostgreSQL version note

The architecture doc specifies PostgreSQL 16. This dev sandbox's `apt`
repository only offered PostgreSQL 17 (Debian's current default at the time
of implementation), so local development and the test database
(`civicpulse_test`) run against 17. This has no observed effect on the
schema (no version-16-specific or version-17-specific SQL is used — plain
`timestamptz`, `VARCHAR`, `CHECK`, and standard B-tree indexes throughout).
The production-shaped artifacts built in Milestone 6+ (`compose.yaml`,
`compose.prod.yaml`, `k8s/base/postgres.yaml`) pin `postgres:16` explicitly,
as the assignment requires — this note only concerns the local dev
environment.

### `id` generation: DB-side default, app-side override

`Complaint.id` has `server_default=gen_random_uuid()` (native to PostgreSQL
13+, no `pgcrypto` extension needed) — genuinely DB-generated for any insert
that doesn't specify one. In practice, `ComplaintService.create()` generates
the UUID in Python *before* calling the triage pipeline, so a triage
fallback's WARNING log line can include the complaint's real ID even though
triage happens before the row is persisted (validate → triage → persist
ordering, `docs/architecture/backend.md` §3.1). The server-side default
remains as a safety net for any future direct-SQL insert path.

## Milestone 3 — AI Triage & Redis

### Retry/fallback lives in the service layer, not inside each provider

`docs/architecture/ai.md`'s pipeline diagram shows the "one jittered retry"
arrow originating from the provider-call step in the overall pipeline, not
from inside a specific provider implementation. `TriageService`
(`app/services/triage.py`) owns retry-once-then-fallback as one policy
applied uniformly to whichever live provider is configured — `LLMTriage`
itself makes exactly one HTTP attempt per `triage()` call and raises a
classified error on failure. This keeps retry/fallback/jitter/caching
testable once, via `SimulatedTriage(force_failure=...)`, instead of
duplicated per provider.

### Triage cache stores provenance, not just the result

The content-hash cache (`app/providers/redis/cache.py::TriageCache`) stores
`{result, triaged_by}`, not a bare `TriageResult`. A cache hit reports the
`triaged_by` marker that actually produced the cached classification,
rather than whatever provider happens to be active at hit time — relevant
if `TRIAGE_PROVIDER` changes while a still-live 24h cache entry exists.

### Triage cache hit rate

Measured via Prometheus counters `triage_cache_hits_total` /
`triage_cache_misses_total` (`app/core/metrics.py`), exposed on `/metrics`.
Hit rate = `hits / (hits + misses)`. Verified functionally in
`backend/tests/integration/test_triage_cache.py` (repeated identical
`(text, location)` input causes exactly one provider call across two
`triage()` invocations).

### Redis AOF justification

Redis is used for two responsibilities (stats cache, rate limiter) plus the
triage content-hash cache — all three are, in principle, rebuildable: stats
recompute from PostgreSQL, triage cache entries just cost one re-inference,
and the rate limiter's worst case on data loss is a temporarily under-
enforced limit, not incorrect enforcement. AOF is still enabled
(`appendonly yes`, named volume `redisdata`) because:

1. **Rate-limiter continuity matters within its own outage window.** If
   Redis restarts mid-burst without AOF, every IP's counter resets to zero,
   handing a clean rate-limit window to exactly the traffic pattern (a
   burst) the limiter exists to catch.
2. **It costs nothing extra to demonstrate the required persistence
   behavior** (`docs/architecture/cache.md` §3) — the assignment explicitly
   asks for AOF on a named volume, and the operational cost of enabling it
   on a single-instance Redis at this scale is negligible.
3. Without AOF, a container recreate (not just a process restart) loses all
   three data sets simultaneously; with it, only the fail-open caches
   (stats, triage) would need to naturally repopulate on next use, and even
   the rate limiter recovers its exact prior counters instead of resetting.

### Fail-open vs. fail-closed, restated

`docs/architecture/cache.md` §2 already documents this, restated here for
visibility: the stats cache and triage cache fail **open** on a Redis
outage (degrade to a direct PostgreSQL query / direct provider call — pure
optimizations, no cost-control role). The rate limiter fails **closed**
(`503`) — it exists specifically to protect the shared Groq free-tier
quota, and an outage window is exactly when unlimited traffic is least
affordable. Both behaviors are unit-tested directly against a
`redis.RedisError`-raising mock client in
`backend/tests/unit/test_redis_fail_modes.py`, independent of whether a
real Redis outage can be reproduced in this environment.

### Hosted-LLM / internal-network topology (decided, not yet built)

`docs/architecture/ai.md` §6 and `docs/Milestones/milestone-1.md` §F2 fix
the decision that the backend is the only service attached to both the
`edge` and `internal` Compose networks, so hosted Groq calls leave through
`edge` while PostgreSQL/Redis stay on `internal: true` with no outbound
internet path. This is recorded as decided during Milestone 1; the actual
`compose.yaml` implementing it is Milestone 6 scope and doesn't exist yet.

---

## Milestone 7 — Kubernetes Baseline

### The placeholder Secret is deleted by the overlays, not applied

The assignment requires a committed Secret manifest with placeholders only,
but `kubectl apply -k` of a placeholder Secret would silently overwrite the
real credentials on every deploy (and pods that restarted in between would
start with `REPLACE_ME` as their database password). Options considered:
apply the placeholder and re-patch afterwards (racy), or a kustomize
`secretGenerator` from a gitignored file (no Secret object is committed at
all, so a reviewer looking for the placeholder finds nothing). Chosen:
`k8s/base/secret.yaml` stays as the documented placeholder, and the shared
component `k8s/components/external-secret` deletes it from both overlays'
output; `scripts/k8s/create-secrets.sh` (local) and the CD workflow (CI)
create the real one. `scripts/k8s/check_manifest_invariants.py` enforces both
halves: the base Secret may only contain `REPLACE_ME`, and no overlay may
render a Secret.

### Client IP behind the Ingress: `FORWARDED_ALLOW_IPS`

The rate limiter keys on `request.client.host`
(`backend/app/routes/dependencies.py`). Behind Traefik every request reaches
the backend from the ingress controller's pod IP, so without correction all
users would share one 10 req/60s bucket. Uvicorn already rewrites the client
address from `X-Forwarded-For` for trusted proxies, and reads the trusted
list from the `FORWARDED_ALLOW_IPS` environment variable — so the fix is
configuration only (`FORWARDED_ALLOW_IPS: "*"` in the ConfigMap), no code
change. `*` is acceptable because the backend Service is ClusterIP-only: only
pods inside the cluster can reach it. **Known gap:** the Compose stack has
the same latent issue behind its nginx proxy (nginx sets `X-Forwarded-For`,
uvicorn ignores it). Not fixed in Milestone 7 to keep the Compose setup
untouched; the same one-line env var would fix it.

### `/api/health` does not exist; the smoke test uses `/api/stats`

`docs/architecture/kubernetes.md` originally said the smoke test hits
`/api/health` through the Ingress. The backend serves `/health` and `/ready`
at the root, and the Ingress only routes `/api/*` to the backend — so a
root-level request through the Ingress reaches the frontend, whose SPA
fallback returns `200` with HTML, a false positive. The doc was corrected:
the smoke test uses `/api/stats` (which touches PostgreSQL and Redis) and also
asserts `Content-Type: application/json`. Kubernetes probes are unaffected —
they call the pod port directly.

### Every Service is a plain ClusterIP, including the StatefulSet's governing Service

A StatefulSet's `serviceName` must name a Service governing its pods' network
identity; the conventional choice is a headless Service (`clusterIP: None`).
We reuse the normal ClusterIP `postgres` Service instead so the assignment's
"Service × 4, ClusterIP for all" holds literally. With `replicas: 1` nothing
uses per-pod DNS names, so nothing is lost.

### The migrate Job retries in place instead of using a wait-for-Postgres step

`restartPolicy: OnFailure` with `backoffLimit: 6` lets `alembic upgrade head`
simply fail and be retried until PostgreSQL accepts connections, so the Job
needs no initContainer or shell loop. The Job — not an initContainer on the
backend — is still the migration mechanism, for the reason in
`docs/architecture/database.md` §2 (≥2 backend replicas would race).
`deploy.sh` waits for `Complete` with a small poll that also stops early on
`Failed`, rather than `kubectl wait --for=condition=complete`, which would
sit out its whole timeout on a failed Job. The condition it checks is the same.

### Image tags are placeholders that fail closed

Committed manifests reference `civicpulse-backend:REPLACE_WITH_SHA` (and the
frontend equivalent); overlays rewrite the registry name and `deploy.sh`
injects the SHA through a throwaway kustomization. Forgetting to set a tag
therefore yields `ImagePullBackOff`, never an implicit `latest`
(`docs/adr/0003-deploy-by-sha.md`). For local builds an uncommitted working
tree gets a timestamp appended to the SHA, so two different builds never
share a tag.

### Service-link env vars broke the migrate Job (`enableServiceLinks: false`)

The first live deploy failed: `alembic` crashed with
`backend_port: Input should be a valid integer ... 'tcp://10.43.x.x:8000'`.
Kubernetes injects `<SERVICE>_PORT=tcp://...` (and `_HOST`, etc.) into every
pod for every Service in the namespace, and our Service named `backend`
therefore produced a `BACKEND_PORT` that collided with the app's integer
`BACKEND_PORT` setting. The backend Deployment only survived because its
ConfigMap (`envFrom`) also sets `BACKEND_PORT=8000` and explicit values win;
the migrate Job doesn't load the ConfigMap. Every pod template now sets
`enableServiceLinks: false` (discovery is by DNS name, so the injected
variables are unused) and `check_manifest_invariants.py` asserts it. Static
validation could not have caught this — it only showed up on a real cluster.

### Client IP on k3d, and how `FORWARDED_ALLOW_IPS` was verified

Through the k3d Ingress every external request is logged with client IP
`10.42.0.1`: k3d's built-in service load balancer rewrites the source address
before Traefik sees it, so on a local k3d cluster all browser/curl clients
share one rate-limit bucket regardless of our configuration. To verify that
the *backend* honours forwarded addresses, requests were sent from inside the
cluster with `X-Forwarded-For: 203.0.113.77`; the rate limiter then keyed on
that address (429 after 10 requests, `client_ip` logged as `203.0.113.77`).
On a real cluster with a source-IP-preserving load balancer this is what gives
each user their own bucket.

### The cluster could not pull from Docker Hub on the dev machine

On Docker Desktop the host Docker could reach Docker Hub but the k3d node
could not (`lookup auth.docker.io: Try again`), leaving `postgres-0` and
`redis` in `ImagePullBackOff`. The migrate Job's `OnFailure` retries kept
going until Postgres came up, which also confirmed that design. Workaround:
`scripts/k8s/load-base-images.sh` pulls the images with host Docker and imports
them. It exports only the host-architecture variant because Docker Desktop's
containerd image store otherwise writes an incomplete multi-arch image and
`k3d image import` fails with `content digest ... not found`.

### Not done in Milestone 7, on purpose

- HPA/VPA and metrics-server checks are Milestone 8 (the VPA CRDs aren't
  installed yet, so shipping `vpa.yaml` in the base would break
  `kubectl apply -k`). The backend Deployment sets `replicas: 2` for now;
  that line must be removed when the HPA is added so `kubectl apply` doesn't
  fight it.
- `runAsNonRoot` isn't set: both images declare a *named* user (`USER app`),
  which Kubernetes can't verify as non-root. Giving the Dockerfiles numeric
  UIDs would allow it. The backend, frontend and migrate containers do drop
  all capabilities and disable privilege escalation; postgres and redis don't
  (their entrypoints start as root to fix volume ownership, then drop
  privileges themselves).
- NetworkPolicies mirroring the Compose `internal: true` network are a
  possible hardening step; segmentation today relies on ClusterIP-only Services.
