# Kubernetes Architecture

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

The same application, packaged in [`docker-compose.md`](docker-compose.md)'s images, runs as a scaled, probed, autoscaling workload on an ephemeral **k3d** cluster in CI (chosen over kind — see root index for the resolved-decisions table — because k3d ships Traefik as its built-in Ingress controller, removing a separate install/wait step from CI/CD).

## 1. Namespace

All resources live in the `civicpulse` namespace. Nothing should be deployed into `default`.

## 2. Workload topology

```text
Namespace civicpulse
│
├── Ingress
│    ├── /     → frontend Service
│    └── /api  → backend Service
│
├── Job/migrate                (runs alembic upgrade head; must reach Complete
│                                before backend rollout is awaited — see database.md, cicd.md)
│
├── Deployment/backend        replicas >= 2
│    ├── /health
│    ├── /ready
│    ├── /metrics
│    └── CPU requests + limits
│
├── Deployment/frontend       replicas >= 2
│
├── StatefulSet/postgres
│    └── PVC / volumeClaimTemplates
│
├── Deployment/redis
│    ├── strategy: Recreate    (see §5 — avoids RWO-PVC rollout deadlock)
│    └── PVC
│
├── Services (ClusterIP ×4)
│    ├── frontend
│    ├── backend
│    ├── postgres
│    └── redis
│
├── ConfigMap
├── Secret
├── HPA/backend
├── VPA/backend
└── PDB/backend
```

## 3. PostgreSQL must be a StatefulSet

PostgreSQL is stateful and requires persistent storage.

```text
StatefulSet
  ↓
volumeClaimTemplates / PVC
  ↓
PersistentVolume
```

A plain Deployment without persistent storage is explicitly a marked failure in the assignment.

`serviceName: postgres` names the Service that governs the StatefulSet's network identity. The manifest reuses the ordinary ClusterIP `postgres` Service for this instead of a headless one, so all four Services are literally `ClusterIP` with a cluster IP. With a single replica nothing relies on per-pod DNS names, so this costs nothing. `PGDATA` points at a subdirectory of the mounted volume because Postgres refuses to initialise into a directory that already contains `lost+found`.

## 4. Services

All four application/data Services are `ClusterIP`. No database Service may be `NodePort` or `LoadBalancer`. No production Compose host port should expose PostgreSQL or Redis either.

## 5. Redis rollout strategy

Redis is a `Deployment` with a PVC, not a `StatefulSet` — this matches the assignment's own required-object table exactly. But a `Deployment`'s default `RollingUpdate` strategy assumes pods are interchangeable and don't hold exclusive state. Redis's PVC is `ReadWriteOnce`: under `RollingUpdate`, Kubernetes tries to start the replacement pod before terminating the old one (to satisfy `maxUnavailable`), but the replacement can't schedule because the old pod still holds the RWO volume, and the old pod won't terminate until the new one is `Ready` — a deadlock that only clears with manual intervention (e.g. `kubectl delete pod`).

**Resolution:** the Redis `Deployment` sets `strategy: { type: Recreate }`. The existing pod is terminated first, releasing the PVC, before the replacement is scheduled. This costs a few seconds of Redis unavailability on a Redis image update or config change — acceptable because Redis is derived/cache state (never the source of truth — see [`database.md`](database.md)), and Redis updates are far rarer than backend rollouts (which correctly stay `RollingUpdate`/`maxUnavailable: 0`, since backend pods are stateless and interchangeable).

## 6. Ingress

One host with `/` → frontend, `/api` → backend. This supports the same-origin frontend API strategy (see [`frontend.md`](frontend.md)) and keeps the browser-facing API stable across deployments.

### Ingress controller

A K8s `Ingress` object is only routing configuration — it does nothing without a running controller to implement it. k3d resolves this cleanly: it ships **Traefik** as its built-in Ingress controller by default, so no separate `ingress-nginx` install/wait step is needed in `ci.yml`/`cd.yml`. The `Ingress` manifest in `k8s/base/ingress.yaml` targets the default `IngressClass` k3d registers.

**Reaching the Ingress from the CI runner.** The k3d cluster is created with a host port mapping so the runner (and the smoke-test step) can reach Traefik without going through `kubectl port-forward`:

```text
k3d cluster create civicpulse --port "8080:80@loadbalancer"
```

The smoke test then hits `http://localhost:8080/` (frontend) and `http://localhost:8080/api/stats` (backend, through the Ingress) directly from the GitHub Actions runner — both share one host/port, matching the same-origin design the frontend relies on. No `/etc/hosts` entry or DNS is needed: `ingress.yaml` deliberately has no `host:` field, so its single rule set answers on any `Host` header.

> **Why `/api/stats`, not a health endpoint.** The backend's `/health` and `/ready` are mounted at the root, not under `/api`, and the Ingress only sends `/api/*` to the backend — so `GET /health` through the Ingress lands on the *frontend*, whose SPA fallback answers `200` with HTML (a false positive). `/api/stats` touches both PostgreSQL and Redis, so a `200 application/json` proves the whole chain. The probes reach `/health` and `/ready` directly on the pod port (not through the Ingress). `scripts/k8s/smoke-test.sh` also checks the `Content-Type` so an accidental route to the frontend can't pass.

**Frontend nginx in Kubernetes.** `frontend/nginx.conf` contains an `/api` proxy block with Docker's embedded resolver (`127.0.0.11`). That block is a Compose-only convenience: in Kubernetes the Ingress sends `/api` straight to the backend Service, so nginx never proxies. The same frontend image runs unchanged in both environments (build once, deploy many).

## 7. Configuration

### ConfigMap

Non-secret values such as: provider selection; service hostnames; non-sensitive runtime settings; environment-specific flags.

### Secret

Sensitive values such as: database password; LLM API key. Committed manifests contain placeholders only. Never treat base64-encoded Kubernetes Secret data as safe to commit when it contains a real credential.

### Secret provisioning

`k8s/base/secret.yaml` (`civicpulse-secrets`, keys `POSTGRES_PASSWORD` and `LLM_API_KEY`, every value `REPLACE_ME`) documents the Secret's shape, but it is never what runs in a cluster. A plain `kubectl apply -k` of a placeholder Secret would overwrite the real credentials on every deploy, so both overlays include the shared component `k8s/components/external-secret`, which removes that placeholder from the rendered output. The real Secret is created out-of-band:

| Where | How |
|---|---|
| Local k3d | `scripts/k8s/create-secrets.sh` reads `POSTGRES_PASSWORD` / `LLM_API_KEY` from the gitignored `.env` and applies the Secret. Values go through a process substitution, never argv, and are never printed. |
| CD (Milestone 9) | The workflow creates the same Secret from GitHub Secrets before applying the overlay. |

`scripts/k8s/deploy.sh` refuses to run if the Secret doesn't exist yet. Two consequences worth knowing: pods read Secret values only at start-up (after changing one, `kubectl rollout restart`), and PostgreSQL reads `POSTGRES_PASSWORD` only when it first initialises an empty volume — changing the Secret later does not change the password of an existing database.

`DATABASE_URL` is assembled in the pod spec from the ConfigMap's `POSTGRES_USER`/`POSTGRES_DB` and the Secret's `POSTGRES_PASSWORD` using `$(VAR)` expansion (which only sees variables defined earlier in the same `env:` list). The password is embedded in a URL, so `create-secrets.sh` rejects passwords containing URL-special characters.

## 8. Resource requests and limits

The assignment requires `resources.requests`/`limits` on **every** container, not just backend. HPA is the reason backend's are load-bearing (§11), but every container needs a starting value regardless. These are deliberately treated as **initial guesses**, per the assignment's own VPA workflow (§12: "record the requests you guessed when you wrote the manifest," then correct them from measured VPA recommendations) — the numbers below are a reasonable starting point, not a tuned result.

| Container | CPU request | CPU limit | Memory request | Memory limit |
|---|---:|---:|---:|---:|
| backend | 100m | 500m | 128Mi | 256Mi |
| frontend | 50m | 200m | 32Mi | 64Mi |
| postgres | 100m | 500m | 256Mi | 512Mi |
| redis | 50m | 250m | 64Mi | 128Mi |
| migrate (Job) | 100m | 500m | 128Mi | 256Mi |

Backend's request (100m) is the one HPA's 60%-utilization target is computed against; the others exist to satisfy the "every container" requirement and to give VPA something to observe and recommend against once load-testing starts.

## 9. Probes

### Startup probe

```text
GET /health
failureThreshold: 30
periodSeconds: 2
```

Purpose: allow slow initialization without immediate restart loops.

### Liveness probe

```text
GET /health
```

Must remain database-independent.

### Readiness probe

```text
GET /ready
```

Must depend on PostgreSQL + Redis availability.

Correct semantics:

```text
startup  = "has the process finished booting?"
liveness = "is the process alive?"
readiness = "should this pod receive traffic?"
```

Endpoint contracts: [`backend.md`](backend.md) §Health, Readiness, and Observability.

## 10. Rolling updates and graceful termination

Backend Deployment strategy:

```yaml
maxSurge: 1
maxUnavailable: 0
```

Additional controls: `terminationGracePeriodSeconds` configured; `preStop` sleep hook; graceful SIGTERM handling in application (see [`backend.md`](backend.md)).

Desired shutdown sequence:

```text
pod termination begins
    ↓
preStop gives Service endpoint propagation time
    ↓
application receives SIGTERM
    ↓
stop accepting new work
    ↓
finish in-flight requests
    ↓
close connection pools
    ↓
exit
```

Required demonstration: run traffic with k6/hey; trigger an image rollout; show zero failed requests for the bonus zero-downtime demonstration.

## 11. HPA Architecture

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
```

Required policy:

| Setting | Value |
|---|---:|
| `minReplicas` | 2 |
| `maxReplicas` | 10 |
| CPU target | 60% average utilization |
| scale-down stabilization | 300s |
| scale-up stabilization | 0s |

The backend pods must define CPU resource requests because HPA utilization is measured relative to the requested CPU. Without requests, utilization cannot be interpreted correctly.

### Load-test loop

```text
install metrics-server
       ↓
k6/hey generates load
       ↓
kubectl get hpa -w
       ↓
record replicas over time
       ↓
chart offered load vs replicas
       ↓
measure lag
```

Engineering notes must explain: when load increased; when HPA observed sustained demand; when new replicas became ready; where the lag came from; what could reduce the lag. Autoscaling is capacity adaptation, not instantaneous capacity.

## 12. VPA Architecture

VPA is used only in recommender mode:

```yaml
updatePolicy: { updateMode: "Off" }
```

Purpose: observe actual resource usage; produce recommendations; avoid automatic pod eviction/request changes during an HPA experiment.

Required workflow:

1. Record initially guessed CPU/memory requests (§8).
2. Run the load test.
3. Inspect VPA Target / Lower Bound / Upper Bound.
4. Commit the recommendations as evidence.
5. Update pod requests deliberately.
6. Re-run the load test.
7. Compare HPA behavior.

**Reason for `Off`:** HPA uses CPU utilization relative to CPU requests. VPA in Auto can modify those requests while HPA is simultaneously reacting to the same utilization signal. Changing the request changes the utilization denominator, which can change HPA behavior and create a feedback interaction. Therefore VPA is advisory here; humans apply recommendations after observing workload behavior.

## 13. PodDisruptionBudget

Backend PDB:

```yaml
minAvailable: 1
```

This protects against voluntary disruptions removing all backend capacity at once. It complements, rather than replaces, the backend Deployment's minimum replica count of 2.

## 14. Deployment and rollback model

### Deploy flow and scripts (`scripts/k8s/`)

Everything below is plain `kubectl`/`docker`/`k3d` wrapped in small scripts, so Milestone 9's CD workflow can reuse the same steps instead of re-inventing them.

| Script | What it does |
|---|---|
| `create-cluster.sh` | Creates (or reuses) the k3d cluster `civicpulse`, publishing the Ingress on `localhost:8080`. |
| `load-images.sh` | Builds both images, tags them with the git SHA (plus a timestamp if the tree is dirty — never `latest`), and imports them into the cluster. |
| `create-secrets.sh` | Creates the real Secret from `.env` (see §7 *Secret provisioning*). |
| `deploy.sh <dev\|prod> [tag]` | Pins the image tag through a throwaway kustomization (no committed file is edited), refuses `latest` or unresolved placeholders, deletes any old `Job/migrate`, applies, waits for the Job to be `Complete`, then waits for every rollout. `DRY_RUN=1` just prints the final manifests. |
| `load-base-images.sh` | Optional. Pulls `postgres`/`redis` with host Docker and loads them into the cluster, for setups where the cluster itself can't reach Docker Hub (pods stuck in `ImagePullBackOff`). |
| `smoke-test.sh` | Frontend + `/api/stats` + a complaint POST/GET through the Ingress. |
| `verify-persistence.sh` | Creates a complaint, deletes `postgres-0`, and confirms the complaint is still there. |
| `validate-manifests.sh` | No cluster needed: renders base + overlays, runs `kubeconform`, then `check_manifest_invariants.py` (the §16 checklist as code). |

Committed manifests carry the placeholder image tag `REPLACE_WITH_SHA`. Applying them without substituting a real tag fails closed (`ImagePullBackOff`) instead of silently running whatever `latest` happens to be (ADR 0003).

### Fast rollback (imperative)

```bash
kubectl rollout undo deployment/backend -n civicpulse
```

Use when immediate recovery is the priority.

### Declarative rollback

Re-apply the previous known-good Kustomize overlay/reference containing the previous image SHA. Use when restoring the declared configuration and leaving an auditable repository state is important.

Both rollback modes should be demonstrated/documented.

## 15. Operational runbook coverage

`docs/RUNBOOK.md` should cover at least: local Compose start/stop; production Compose startup; migrations; seed/reset behavior; checking `/health` and `/ready`; reading structured logs; tracing a request by `request_id`; checking Redis cache state; diagnosing triage provider failures; forcing/test-driving fallback; checking HPA; checking VPA recommendations; rollout status; rollback by `rollout undo`; rollback by previous SHA/Kustomize overlay; verifying persistence after database pod restart.

## 16. Invariants checklist

- [x] Namespace `civicpulse`.
- [x] Backend ≥2 replicas.
- [x] Frontend ≥2 replicas.
- [x] PostgreSQL is a StatefulSet + PVC.
- [x] Redis has a PVC and `strategy: Recreate`.
- [x] `Job/migrate` completes (`Complete`) before backend rollout is awaited. (enforced by `scripts/k8s/deploy.sh`; verified live)
- [x] Four ClusterIP Services.
- [ ] Ingress routes `/` and `/api`; k3d/Traefik reachable from CI runner. (routes verified live on local k3d via `smoke-test.sh`; reachability from the CI runner is confirmed in Milestone 9)
- [x] ConfigMap/Secret separation.
- [x] Committed secrets are placeholders only.
- [x] Startup/liveness/readiness probes are semantically correct. (verified live: with Redis at 0 replicas, backend pods go `NotReady` and leave the Service endpoints while `RESTARTS` stays 0)
- [x] Requests/limits set on every container.
- [ ] HPA v2 configured as required.
- [ ] Metrics Server installed for HPA evidence.
- [ ] VPA is `Off`/recommender mode.
- [x] Backend PDB has `minAvailable: 1`.
- [x] Rolling update is configured for no voluntary unavailable replicas.
