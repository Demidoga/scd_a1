# CivicPulse

Municipal complaint intake + AI triage platform. Backend: FastAPI +
PostgreSQL + Redis. Frontend: React + Vite + TypeScript.

## Backend

Requires Python 3.12+, [`uv`](https://docs.astral.sh/uv/), PostgreSQL 16+,
Redis 7+ running locally.

### macOS / Linux

```bash
cd backend
uv sync

# one-time: create the app role/databases
sudo -u postgres psql \
  -c "CREATE ROLE civicpulse WITH LOGIN PASSWORD 'civicpulse';" \
  -c "CREATE DATABASE civicpulse OWNER civicpulse;" \
  -c "CREATE DATABASE civicpulse_test OWNER civicpulse;"

# copy the env template INTO backend/ — the app reads backend/.env, not
# the repo-root one
cp ../.env.example .env
# then edit backend/.env: DATABASE_URL should match the role/db you just
# created, e.g. postgresql+psycopg://civicpulse:civicpulse@localhost:5432/civicpulse

uv run alembic upgrade head      # apply schema
uv run python -m app.seed        # seed sample data

uv run uvicorn app.main:app --reload --port 8000
```

### Windows

PostgreSQL on Windows runs as a native service, not via a Linux user — there
is no `sudo -u postgres`. Use `psql.exe` directly instead, from PowerShell.

```powershell
cd backend
uv sync

# Find where PostgreSQL is installed if it's not on PATH — check the
# service definition:
# (Get-WmiObject Win32_Service -Filter "Name='postgresql-x64-16'").PathName
# psql.exe lives in the sibling bin\ folder, e.g. C:\Program Files\PostgreSQL\16\bin
# or a custom install dir like D:\postgres\bin.

# one-time: create the app role/databases (password-prompts unless
# $env:PGPASSWORD is set first)
$env:PGPASSWORD = "<your postgres superuser password>"
& "<path-to-bin>\psql.exe" -U postgres -h localhost -c "CREATE ROLE civicpulse WITH LOGIN PASSWORD 'civicpulse';"
& "<path-to-bin>\psql.exe" -U postgres -h localhost -c "CREATE DATABASE civicpulse OWNER civicpulse;"
& "<path-to-bin>\psql.exe" -U postgres -h localhost -c "CREATE DATABASE civicpulse_test OWNER civicpulse;"
Remove-Item Env:\PGPASSWORD

# copy the env template INTO backend/ — the app reads backend/.env, not
# the repo-root one
Copy-Item ..\.env.example .env
# then edit backend\.env: DATABASE_URL should match the role/db you just
# created, e.g. postgresql+psycopg://civicpulse:civicpulse@localhost:5432/civicpulse

# Redis has no native Windows build. Easiest option is Docker Desktop:
docker run -d --name civicpulse-redis -p 6379:6379 redis:7
# REDIS_URL in backend\.env should then be redis://localhost:6379/0

uv run alembic upgrade head      # apply schema
uv run python -m app.seed        # seed sample data

uv run uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

Tests: `uv run pytest tests/unit -q` (no DB needed) or
`uv run pytest tests/ --cov=app -q` (full suite, needs DB + Redis).

## Frontend

Requires the backend running on `:8000`.

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173` (proxies `/api` to the backend)

Tests: `npm run test`

## Docker Compose

Requires Docker + Docker Compose. Brings up the whole system (frontend,
backend, PostgreSQL, Redis) as four cooperating containers, plus a one-off
`migrate` job that applies Alembic migrations before the backend starts.

```bash
cp .env.example .env
# edit .env: at minimum POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB, and
# LLM_API_KEY if you want TRIAGE_PROVIDER=llm instead of the simulated/rules
# fallback providers.

docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend directly (dev convenience only): `http://localhost:8000`
- `backend/app` is bind-mounted for hot reload in this dev file.

Production-shaped stack (no `build:`, pre-built immutable images by commit
SHA, no dev bind mounts):

```bash
BACKEND_IMAGE=ghcr.io/<org>/civicpulse-backend \
FRONTEND_IMAGE=ghcr.io/<org>/civicpulse-frontend \
IMAGE_TAG=<commit-sha> \
docker compose -f compose.prod.yaml up -d
```

`compose.prod.yaml` refuses to run meaningfully without `IMAGE_TAG` set (an
empty tag produces an invalid image reference rather than silently falling
back to `:latest`) — see `docs/adr/0003-deploy-by-sha.md`.

Network isolation check (should fail — the frontend has no route to
PostgreSQL):

```bash
docker compose exec frontend wget -qO- --timeout=2 postgres:5432
```

Persistence check:

```bash
docker compose down
docker compose up -d
# data in `pgdata`/`redisdata` volumes survives the cycle
```

## Kubernetes (local k3d cluster)

Runs the same images on a local Kubernetes cluster. Needs Docker,
[`k3d`](https://k3d.io) (runs a small Kubernetes cluster inside Docker) and
`kubectl` (the Kubernetes command-line client). `.env` must have
`POSTGRES_PASSWORD` set (letters, digits and `. _ ~ -` only, because it is
embedded in a URL).

```bash
scripts/k8s/create-cluster.sh    # k3d cluster; app will be on http://localhost:8080
scripts/k8s/load-images.sh       # build both images, tag with the git SHA, load into the cluster
scripts/k8s/create-secrets.sh    # real Secret from .env (never committed)
scripts/k8s/deploy.sh dev        # apply k8s/overlays/dev, wait for migrate Job + rollouts

scripts/k8s/smoke-test.sh        # frontend + API + complaint round trip via the Ingress
scripts/k8s/verify-persistence.sh  # delete the Postgres pod, prove the data survives

# only if postgres/redis pods sit in ImagePullBackOff (cluster can't reach Docker Hub):
#   scripts/k8s/load-base-images.sh

# optional: load the 36 sample complaints
kubectl exec deploy/backend -n civicpulse -- python -m app.seed
```

Static check of the manifests (no cluster needed; needs `kubectl` and
`kubeconform`): `scripts/k8s/validate-manifests.sh`. Design and the reasons
behind each choice: `docs/architecture/kubernetes.md`.

### Autoscaling (HPA/VPA) & load testing

`k8s/base/hpa.yaml` scales `backend` 2–10 replicas on 60% CPU utilization;
`k8s/base/vpa.yaml` runs the VPA in recommender-only mode (`updateMode: "Off"`
— it never evicts a pod itself). Needs Metrics Server (k3d ships it already),
the VPA CRDs (not bundled by k3d — e.g.
`helm install vpa cowboysysop/vertical-pod-autoscaler -n kube-system`), and
[`k6`](https://k6.io) on the cluster/host before `deploy.sh` and the load
test will work. On Windows, `winget install GrafanaLabs.k6`'s MSI can fail
silently in a non-interactive shell (exit 1602, "You cancelled the
installation") — the portable `k6-*-windows-amd64.zip` from the
[GitHub releases page](https://github.com/grafana/k6/releases) works without
that installer.

```bash
# The backend rate-limits POST /api/complaints at 10 req/60s per client IP,
# and every request through the k3d Ingress shares one source IP — raise it
# before load testing or k6 hits 429s in the first few seconds:
kubectl patch configmap civicpulse-config -n civicpulse --type merge \
  -p '{"data":{"RATE_LIMIT_REQUESTS":"100000"}}'
kubectl rollout restart deployment/backend -n civicpulse

kubectl get hpa backend -n civicpulse -w   # separate terminal
k6 run load/k6-script.js                   # ramps 5-50 VUs against /api/stats,
                                            # /api/complaints (GET+POST)

kubectl describe vpa backend-vpa -n civicpulse   # Target/Lower/Upper Bound recommendations

# revert once done:
kubectl patch configmap civicpulse-config -n civicpulse --type merge \
  -p '{"data":{"RATE_LIMIT_REQUESTS":"10"}}'
```

Status: verified live on a local k3d cluster — HPA scaled 2→10 replicas
under k6 load, VPA produced a Target recommendation that
`resources.requests` was then updated to match, a re-run at the new size
topped out at 9/10 instead of pinning CPU above 100% at max replicas, and a
`kubectl set image` rollout under load completed with 0% failed requests.
Replicas-vs-load charts: `load/results/hpa-run1-replicas-vs-load.png` /
`hpa-run2-replicas-vs-load.png`. Full data and analysis (including measured
HPA lag numbers for engineering-notes Q5) in `docs/ENGINEERING-NOTES.md`
Milestone 8; `docs/progress.md` has the summary.

## More

Full docs, architecture, and milestone checklist live in `docs/` — see
`CLAUDE.md` for the map.
