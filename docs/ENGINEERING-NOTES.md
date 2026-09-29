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

---

## Milestone 8 — HPA, VPA & Operational Testing

### `replicas: 2` had to come off `backend.yaml`, not just be left alone

Milestone 7's note above already flagged this as required future work. Done
now: `k8s/base/backend.yaml`'s Deployment spec no longer sets `replicas` at
all — `k8s/base/hpa.yaml` (`minReplicas: 2`, `maxReplicas: 10`) is the only
source of truth for replica count from Milestone 8 onward. Leaving the field
in would have meant every `kubectl apply -k` silently reset replicas to 2,
fighting whatever count the HPA had scaled to.
`scripts/k8s/check_manifest_invariants.py::check_backend` was updated to
match: it now fails if `Deployment/backend` sets `replicas` at all, and
separately asserts `HorizontalPodAutoscaler/backend` exists with
`minReplicas >= 2` — the same invariant, enforced through the new owner.

### `kubeconform` has no schema for the VPA CRD

`VerticalPodAutoscaler` (`autoscaling.k8s.io/v1`) is not a built-in Kubernetes
API, so `kubeconform -strict` fails closed on it with "could not find schema"
once `vpa.yaml` is in the base (`k8s/base/kustomization.yaml`).
`scripts/k8s/validate-manifests.sh` now passes `-ignore-missing-schemas`;
`-strict` still applies to every resource kubeconform does recognize
(everything except the VPA object itself), and
`check_manifest_invariants.py` already asserts the structural things that
matter about our own manifests, so nothing is unchecked, just not
schema-checked for that one CRD.

### The default rate limit makes k6 load testing impossible unless it's raised first

`RATE_LIMIT_REQUESTS=10` / `RATE_LIMIT_WINDOW_SECONDS=60`
(`k8s/base/configmap.yaml`) is keyed per client IP
(`app/routes/dependencies.py::enforce_rate_limit`) and only guards
`POST /api/complaints` — confirmed by reading `app/routes/complaints.py` and
`app/routes/stats.py`, where only `create_complaint` carries
`dependencies=[Depends(enforce_rate_limit)]`. Milestone 7's note "Client IP
on k3d" already recorded that every request arriving through the k3d Ingress
shares one source IP once k3d's load balancer rewrites it — so a k6 run
against `http://localhost:8080`, at any VU count, hits the 429 wall inside
the first ~10 POSTs of the whole test, not per VU. `load/k6-script.js`
therefore deliberately keeps the write-traffic scenario to 2 constant VUs on
a 2s pace (still far above 10/60s) and documents in its header comment that
`RATE_LIMIT_REQUESTS` must be raised (e.g. `kubectl patch configmap
civicpulse-config -n civicpulse --type merge -p
'{"data":{"RATE_LIMIT_REQUESTS":"100000"}}'`, then `kubectl rollout restart
deployment/backend` so the new env is picked up — `envFrom` is not live) for
the duration of the load test, and reverted afterward. Most of the offered
load comes from the unthrottled GET scenario (`/api/stats`, `/api/complaints`)
for this reason.

### Live run: scale-out, scale-down, VPA recommendation, resize, re-run

Executed end-to-end on a local k3d cluster (k3d v5.9.0, k3s v1.35.5) with
metrics-server (bundled) and the VPA CRDs (`cowboysysop/vertical-pod-autoscaler`
Helm chart, `kube-system`), per the operational guide. Raw `kubectl get hpa`
samples: `load/results/hpa-watch.log` (Run 1), `load/results/hpa-watch-2.log`
(Run 2); replicas-vs-load charts rendered from them:
`load/results/hpa-run1-replicas-vs-load.png`,
`load/results/hpa-run2-replicas-vs-load.png`
(`load/results/plot_hpa.py`). k6 summaries: `load/results/k6-output.log` /
`k6-summary.json` (Run 1), `k6-rollout-output.log` /
`k6-rollout-summary.json` (zero-downtime demo), `k6-resized-output.log` /
`k6-resized-summary.json` (Run 2).

**Run 1 — original guessed requests (`cpu: 100m`, `memory: 128Mi`).**
`k6 run load/k6-script.js` against `http://localhost:8080`
(`load/results/k6-output.log`, `hpa-watch.log`): 0% `http_req_failed`,
p95=89ms, 36,010 requests. `kubectl get events` (`SuccessfulRescale`,
timestamps below are UTC) shows the HPA scaling the full range on real CPU
pressure:

```
05:27:13Z  New size: 5   (cpu resource utilization above target)
05:27:28Z  New size: 7   (cpu resource utilization above target)
05:27:58Z  New size: 10  (cpu resource utilization above target)  <- maxReplicas, CPU still 130-248%/60% here
05:42:46Z  New size: 6   (All metrics below target)
05:43:01Z  New size: 2   (All metrics below target)               <- minReplicas
```

CPU stayed pinned well above the 60% target (up to 248%) even at 10/10
replicas — real proof that the original `100m` request was too small a
denominator: at maxReplicas the fleet's total CPU *budget* (10 × 100m = 1
core) was smaller than what the offered load actually needed, so the HPA
correctly maxed out but the deployment still couldn't hold 60%.

**VPA recommendation, captured after this run** (`kubectl describe vpa
backend-vpa`):

```
Lower Bound:  cpu: 106m   memory: 250Mi
Target:       cpu: 296m   memory: 250Mi
Upper Bound:  cpu: 25517m memory: 12469491841   (wide — short observation window)
```

`k8s/base/backend.yaml`'s `resources.requests` was updated from `100m/128Mi`
to `300m/256Mi` (rounded up from Target) to match, with `limits` raised to
`750m/384Mi` to keep proportionate headroom; redeployed with
`scripts/k8s/deploy.sh dev`.

**Run 2 — resized requests (`cpu: 300m`, `memory: 256Mi`)**, same k6 script
against the same cluster (`load/results/k6-resized-output.log`,
`hpa-watch-2.log`):

```
05:45:46Z  New size: 3   (cpu resource utilization above target)
05:46:01Z  New size: 4   (cpu resource utilization above target)
05:46:16Z  New size: 6   (cpu resource utilization above target)
05:46:31Z  New size: 9   (cpu resource utilization above target)
```

**What changed:** the HPA never reached `maxReplicas` this time (peaked at
9/10, CPU settling to 30-50%/60% instead of pinning above 100%) — tripling
the per-pod request means the same absolute k6 load now represents a much
smaller percentage of each pod's budget, and the fleet's total real-CPU
ceiling at `maxReplicas` went from 10×100m=1 core to 10×300m=3 cores. The
guessed request wasn't just "a number the HPA needs" — it was silently
capping how much real traffic the deployment could ever absorb, independent
of `maxReplicas`. (This run also logged a 0.64% `http_req_failed` — see "The
rate-limit patch doesn't survive a redeploy" below; it's a rate-limiter
artifact of the resize's own redeploy step, not an HPA/VPA effect, and GET
traffic — the load driving the CPU signal being measured — was unaffected.)

**Zero-downtime rolling update under load:** with the fleet at 10/10
replicas and a second k6 run in flight, `kubectl set image
deployment/backend backend=civicpulse-backend:rollout-demo-1 -n civicpulse`
replaced all 10 pods (05:33:14Z → 05:34:40Z, ~86s, paced by
`maxSurge: 1`/`maxUnavailable: 0`). That k6 run finished with **0.00%
`http_req_failed`** across 36,294 requests
(`load/results/k6-rollout-output.log`) — the `preStop` sleep +
`maxUnavailable: 0` combination worked as designed.

### The rate-limit patch doesn't survive a redeploy

`RATE_LIMIT_REQUESTS` was raised imperatively
(`kubectl patch configmap ... RATE_LIMIT_REQUESTS=100000`) before Run 1, but
`k8s/base/configmap.yaml` still commits the real default (`"10"`).
Redeploying for the resize (`scripts/k8s/deploy.sh dev`, which does
`kubectl apply -k`) reapplied that committed ConfigMap and silently reset
the live value back to `10` — this is exactly what `kubectl apply`'s
declarative model is supposed to do (the cluster converges to the committed
spec), but it means the patch has to be reapplied after *every* redeploy,
not just once per cluster lifetime. This is what produced Run 2's 0.64%
`POST /api/complaints` failure rate (247/297 write-scenario iterations
hit `429`) — confirmed by checking `kubectl get configmap civicpulse-config
-o jsonpath='{.data.RATE_LIMIT_REQUESTS}'` after the resize deploy and
finding `10`, not `100000`. Not fixed by making the bump durable (that would
mean committing a load-test-only rate limit as the real default, which is
worse) — noted here so the operational guide's ordering (patch → restart →
*then* run k6) is understood as "immediately before load testing," not
"once."

### Q5 — HPA scaling lag

Where the lag comes from, in order, for our stack specifically:

1. **Metrics Server scrape interval (~15s default, k3d ships it built in —
   `scripts/k8s/create-cluster.sh`'s comment on this).** The HPA controller
   can only ever act on the most recent scrape kubelet has reported; a CPU
   spike that starts right after a scrape waits out almost a full interval
   before it's visible at all.
2. **HPA controller sync period (`--horizontal-pod-autoscaler-sync-period`,
   default 15s).** Even after the metric is fresh, the controller only
   re-evaluates on its own timer, not on metric arrival — a second
   independent ~0–15s wait stacked on top of (1).
3. **`scaleUp.stabilizationWindowSeconds: 0`** (`k8s/base/hpa.yaml`) removes
   what would otherwise be a third deliberate delay here — this is exactly
   why it's set to 0 for scale-up and not left at the (also fine) default.
4. **Pod scheduling + image pull + container start.** `civicpulse-backend`'s
   image is already resident on every k3d node once
   `scripts/k8s/load-images.sh` has run, so this step is scheduling +
   process boot, not a registry pull.
5. **`startupProbe` (`k8s/base/backend.yaml`): `periodSeconds: 2`,
   `failureThreshold: 30`.** The new pod is not Ready, and therefore not
   receiving traffic or counted as "up" capacity, until this probe first
   succeeds — at minimum one 2s probe interval after the process starts
   answering `/health`, structurally bounded above by 60s.
6. **`readinessProbe` (`periodSeconds: 5`) gates traffic separately from
   `livenessProbe`** once the startup probe hands off — a pod can be
   "started" (per Kubernetes) before it is "ready" (per this probe, which
   checks PostgreSQL + Redis, `docs/architecture/kubernetes.md` §9), adding
   up to one more 5s interval before the Service actually routes to it.

Steps 1–3 are the *decision* lag (load rising → HPA decides to add a
replica); steps 4–6 are the *capacity* lag (decision → replica actually
serving traffic). The second half is the larger, harder-to-shrink one for
this workload, because it's dominated by our own startup probe's
`periodSeconds`/`failureThreshold`, not by Kubernetes scheduling.

**Measured, from Run 2's `SuccessfulRescale` + pod events (both from
`kubectl get events -n civicpulse`, UTC):**

```
05:45:46Z  SuccessfulRescale New size: 3
05:45:48Z  Pod backend-79cd845d5c-hlptl: Created/Pulled/Started   (+2s: scheduling + container start; image
                                                                    already resident, so no pull time — this
                                                                    step is scheduling-bound only, per
                                                                    scripts/k8s/load-images.sh)
05:45:57Z  Pod backend-79cd845d5c-hlptl: startupProbe Unhealthy   (+9s after Started: still booting,
                                                                    expected — first probe fires at
                                                                    periodSeconds: 2, so this is really the
                                                                    ~5th failed attempt)
```

The probe's first *success* isn't itself a logged event (Kubernetes only
emits `Unhealthy` on failure), but it's bounded: `periodSeconds: 2` means it
lands within 2s of whenever the process actually finishes booting, and no
run exhausted `failureThreshold: 30` (which would show as
`CrashLoopBackOff`/pod never Ready), so every new pod went Ready comfortably
under the 60s ceiling that threshold implies. Taking the decision timestamp
(05:45:46Z) through to a conservative Ready estimate (~05:46:00Z, a few
seconds past the last observed `Unhealthy`) gives a **decision-to-serving
lag of roughly 12-16 seconds per new pod** for this deployment specifically
— small because the image is already on every node and the app boots fast
under `TRIAGE_PROVIDER=simulated`; a cold image pull or a slower boot path
(e.g. `TRIAGE_PROVIDER=llm`, which does a real network round-trip in some
code paths) would stretch step 4 and, if it altered readiness timing,
step 6.

**Scale-down lag — the cleanest number this run produced.** Run 1's CPU was
last observed above the 60% target at `05:37:50Z` (143%,
`load/results/hpa-watch.log`); the first scale-down `SuccessfulRescale`
fired at `05:42:46Z` — a **296-second gap**, matching the configured
`scaleDown.stabilizationWindowSeconds: 300` (`k8s/base/hpa.yaml`) to within
this setup's ~5-6s sampling granularity. This is the cleanest measured
confirmation in this whole exercise: the behavior tuning does exactly what
it says, and the "expensive to flap, cheap to be a little slow" trade-off
described in the manifest's comment is real and measured, not aspirational.

**What would reduce the scale-up half:** lowering `startupProbe.periodSeconds`
(currently tuned for slow-boot tolerance, not scale-out speed, per the
comment in `backend.yaml`) and lowering the Metrics Server scrape interval
would both shrink their halves — at the cost of the properties they were
originally set to protect (slow-boot tolerance, and scrape/API-server load,
respectively). Autoscaling buys *elastic* capacity on a delay measured in
tens of seconds; it does not buy *instantaneous* capacity, which is why
capacity planning for foreseeable load (e.g. a known traffic pattern) still
has to happen ahead of time rather than being delegated to the HPA.

### Q6 — Why VPA runs in `Off` mode

`k8s/base/vpa.yaml` sets `updatePolicy.updateMode: "Off"` deliberately: it
makes the VPA recommender compute and expose Target/Lower Bound/Upper Bound
CPU and memory recommendations (`kubectl describe vpa backend-vpa`) without
ever evicting or restarting a backend pod to apply them. Applying them is a
human step — editing `k8s/base/backend.yaml`'s `resources.requests` by hand,
after reading the recommendation.

The reason it can't run in `Auto` mode alongside the HPA above is that both
would be closing feedback loops around the *same* signal — CPU utilization,
computed as `usage ÷ request` — from opposite ends:

1. VPA-Auto sees sustained CPU usage per pod and raises `resources.requests.cpu`
   on the backend pods to match it.
2. The HPA computes utilization as `usage ÷ request`. Raising the
   denominator (the request VPA just changed) drops the computed
   utilization percentage, even though real usage hasn't changed.
3. The HPA reads that drop as "we're now under the 60% target" and scales
   **in** — removes replicas.
4. Removing replicas concentrates the same total request load onto fewer,
   now-larger pods, so *per-pod* usage goes back up.
5. VPA-Auto (only able to change requests by evicting and recreating the
   pod at the new size — it has no in-place resize path here) sees usage
   climbing against the request again and raises the request further,
   re-triggering an eviction.

That loop — HPA scaling in exactly when VPA scaling up should be met with
*more* replicas, not fewer, and VPA evicting pods to fatten them right as
the HPA is trying to add thinner ones — never settles, because each
controller's "converged" state is the input the other reacts to. `Off` mode
breaks the loop at its only shared edge: VPA still watches and learns, but
only the CPU-based HPA is ever allowed to actually act, so there is exactly
one controller changing capacity in response to CPU at any time. The
recommendation loop (record current requests → load test → read
Target/Lower/Upper → update `resources.requests` by hand → re-run the load
test → compare HPA behavior at the new request size) is how VPA's judgment
still reaches production, just gated by a person instead of a second live
controller. Run end-to-end in this milestone (see "Live run" above):
`100m/128Mi` → VPA Target `296m/250Mi` → `resources.requests` updated to
`300m/256Mi` → re-run showed the HPA topping out at 9/10 replicas instead of
pinning at 10/10 with CPU still 2-4× over target.
