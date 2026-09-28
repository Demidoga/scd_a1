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

## More

Full docs, architecture, and milestone checklist live in `docs/` — see
`CLAUDE.md` for the map.
