# CivicPulse

Municipal complaint intake + AI triage platform. Backend: FastAPI +
PostgreSQL + Redis. Frontend: React + Vite + TypeScript.

## Backend

Requires Python 3.12+, [`uv`](https://docs.astral.sh/uv/), PostgreSQL 16+,
Redis 7+ running locally.

```bash
cd backend
uv sync

# one-time: create the app role/databases
sudo -u postgres psql \
  -c "CREATE ROLE civicpulse WITH LOGIN PASSWORD 'civicpulse';" \
  -c "CREATE DATABASE civicpulse OWNER civicpulse;" \
  -c "CREATE DATABASE civicpulse_test OWNER civicpulse;"

cp ../.env.example .env

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

## More

Full docs, architecture, and milestone checklist live in `docs/` — see
`CLAUDE.md` for the map.
