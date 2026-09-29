# CivicPulse Runbook

How to deploy, roll back, read logs, and respond when AI triage starts failing. Written for whoever is on call, including someone who has never touched this system.

Terms used below:

- **`kubectl`** is the command-line client for Kubernetes (the system that runs the containers). Every `kubectl` command here targets the `civicpulse` namespace (a named group of resources); point it at the right cluster first with `kubectl config current-context`.
- **SHA** is the git commit ID. Every deployed image is tagged with the commit SHA it was built from, so "what is production running?" always has a one-word answer you can paste into `git show`.
- **Triage** is the step that classifies a complaint (category, priority, summary). **Provider** is the component that does it: `llm` (Groq hosted model), `rules` (deterministic keyword rules) or `simulated` (fixed fake used in tests).

Related: rationale in [`architecture/cicd.md`](architecture/cicd.md) and [`architecture/kubernetes.md`](architecture/kubernetes.md); GitHub setup in [`CI-CD-SETUP.md`](CI-CD-SETUP.md).

## 1. Deploy

### 1.1 Normal path: merge to `main`

Nobody deploys by hand in the normal case.

1. Open a pull request from a feature branch into `main`. `ci.yml` runs: lint, type check, backend and frontend tests, image build, Trivy scan, manifest validation, Compose integration test. All must be green and one teammate must approve.
2. Merge. That push to `main` triggers `cd.yml`, which re-runs the test suite, then builds both images, pushes them to GHCR (GitHub's container registry) tagged with the commit SHA, then deploys that exact SHA to an ephemeral k3d cluster and smoke-tests the Ingress.
3. Check the run on GitHub: **Actions → CD**. Green means tested, published and deployed.

`:latest` is pushed for convenience but is never deployed. `scripts/k8s/deploy.sh` refuses it.

### 1.2 Manual deploy to a cluster you control

Needs `kubectl` pointed at the cluster, and the Secret already created (see 1.3).

```bash
scripts/k8s/deploy.sh prod <commit-sha>     # or: dev <tag> for a local k3d cluster
scripts/k8s/smoke-test.sh
kubectl get pods -n civicpulse
```

`deploy.sh` deletes the previous `Job/migrate`, applies the overlay, waits for the migration Job to reach `Complete`, then waits for each rollout. The app receives traffic only after the schema is migrated. Migrations are never run from backend startup code.

### 1.3 First-time secrets (manual step)

Real credentials are never committed. Create them in the cluster:

```bash
# local k3d: builds the Secret from your untracked .env
scripts/k8s/create-secrets.sh
```

In CI, `cd.yml` builds the Secret from the GitHub repository secrets `POSTGRES_PASSWORD` (required) and `LLM_API_KEY` (optional). Set them under GitHub **Settings → Secrets and variables → Actions**.

## 2. Roll back

Two mechanisms. Use the fast one to stop the bleeding, then the declarative one to leave the repository and cluster in agreement.

### 2.1 Imperative rollback: fast, for an incident

```bash
kubectl rollout history deployment/backend -n civicpulse
kubectl rollout undo deployment/backend -n civicpulse
kubectl rollout status deployment/backend -n civicpulse
kubectl get deployment/backend -n civicpulse -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

Repeat for `deployment/frontend` if the frontend was part of the bad release. Add `--to-revision=<N>` to go back further than one step. This changes the live cluster only, not git, so follow up with 2.2.

### 2.2 Declarative rollback: auditable

Redeploy the previous known-good SHA through the same path CD uses.

```bash
git log --oneline main            # find the last good commit
scripts/k8s/deploy.sh prod <previous-good-sha>
scripts/k8s/smoke-test.sh
```

**Migrations are not undone by either method.** If the bad release included a schema change that the old code cannot run against, roll the schema back explicitly (`alembic downgrade`) before or with the code. Prefer additive migrations so a plain rollback is safe.

## 3. Read the logs

The backend writes one JSON object per line to stdout. Every request log carries a `request_id`. The same value is returned to the caller in the `X-Request-ID` response header, so a user reporting a problem can give you the ID and you can follow that one request.

```bash
# Kubernetes
kubectl logs deployment/backend -n civicpulse --tail=200
kubectl logs deployment/backend -n civicpulse -f            # follow live
kubectl logs job/migrate -n civicpulse                       # migration output
kubectl logs deployment/backend -n civicpulse --tail=1000 | grep '<request-id>'

# Docker Compose
docker compose logs backend --tail=200 -f
```

Backend pods restarting repeatedly? `kubectl describe pod <name> -n civicpulse` shows probe failures and the previous container's exit reason, and `kubectl get events -n civicpulse --sort-by=.lastTimestamp` shows recent cluster events.

Two health endpoints, deliberately different:

- `/health` (liveness): the process is up. It does not touch the database. If it fails, Kubernetes restarts the pod.
- `/ready` (readiness): PostgreSQL and Redis are both reachable. If it fails, the pod is taken out of the load balancer but not restarted, and the response is `503` naming the failed dependency. Backend pods that are `NotReady` with zero restarts usually mean a dependency is down, not a backend bug.

## 4. AI triage is failing

**What "failing" looks like.** Complaints are still accepted; a provider outage must never produce a `500`. Instead, complaints are triaged by the rule-based fallback and recorded with `triaged_by = rules:fallback`. Results are less precise but the service works.

### 4.1 Confirm it

```bash
# last 20 outcomes: provider, latency, and whether each used the fallback
curl -s http://<host>/api/meta/providers

# the fallback counter climbing is the alarm signal
curl -s http://<host>/metrics | grep -E 'triage_fallback_total|triage_duration_seconds_count|triage_cache_(hits|misses)_total'
```

If almost every recent outcome shows `rules:fallback` while `TRIAGE_PROVIDER` is `llm`, the hosted model is not being reached or is rejecting requests.

### 4.2 Find the cause

```bash
kubectl logs deployment/backend -n civicpulse --tail=500 | grep -i -E 'triage|llm|429|timeout'
```

| Symptom in logs | Likely cause | Action |
|---|---|---|
| Authentication or 401/403 errors from the provider | `LLM_API_KEY` missing, wrong or revoked | Replace the key (4.3). No key at all means the app quietly runs on rules. |
| `429` from the provider | Free-tier quota exhausted (the app retries once, then falls back) | Wait for the quota window to reset; check nobody is bypassing the IP rate limiter. The fallback keeps serving meanwhile. |
| Timeouts (the app allows 10 s, one jittered retry) | Provider slow or unreachable | Check the provider's status page; check the backend can reach the internet on the `edge` network (Compose) or via cluster egress (Kubernetes). |
| `5xx` from the provider | Provider outage | Nothing to fix on our side; the fallback covers it. |
| Malformed or invalid JSON from the model | Model returned output that failed validation | Rejected safely and falls back. If it is persistent, the model or prompt changed; see [`TRIAGE.md`](TRIAGE.md). |

Identical complaints are served from the triage cache for 24 hours, so a provider outage only affects text the system has not seen before.

### 4.3 Mitigate

Replace the API key (Kubernetes):

```bash
kubectl create secret generic civicpulse-secrets -n civicpulse \
  --from-literal=POSTGRES_PASSWORD='<existing password>' \
  --from-literal=LLM_API_KEY='<new key>' \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/backend -n civicpulse
```

Take the model out of the loop entirely (deterministic rules only) until it is fixed:

```bash
kubectl patch configmap civicpulse-config -n civicpulse --type merge -p '{"data":{"TRIAGE_PROVIDER":"rules"}}'
kubectl rollout restart deployment/backend -n civicpulse
```

Note this is an imperative change: the next `deploy.sh` re-applies the committed value (`llm` in the prod overlay). Restore afterwards by setting it back to `llm` and restarting. Under Compose, set `TRIAGE_PROVIDER` in `.env` and run `docker compose up -d backend`.

### 4.4 After the incident

Confirm `/api/meta/providers` shows recent outcomes with the `llm` provider again and `triage_fallback_total` has stopped rising. Complaints triaged by fallback in the meantime keep their `rules:fallback` label; they are not re-triaged automatically.

## 5. Other quick checks

| Situation | Check |
|---|---|
| Users get `429` on submit | Working as designed: 10 submissions per 60 s per IP. `Retry-After` says when to retry. Load tests must raise `RATE_LIMIT_REQUESTS` first (README, Autoscaling section). |
| Every request returns `503` | Redis down: the rate limiter fails closed on purpose (it protects the AI quota). `kubectl get pods -n civicpulse`; restart or restore Redis. Stats and triage caches fail open and do not cause this. |
| `/ready` says `postgres` failed | `kubectl get pod postgres-0 -n civicpulse`; data lives on a PersistentVolumeClaim and survives pod restarts. |
| Stats look stale | Cached 30 s and invalidated on every write; `X-Cache: HIT` on `/api/stats` is normal. |
