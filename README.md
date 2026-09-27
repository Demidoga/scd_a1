# CivicPulse

Municipal complaint intake, AI-assisted triage, persistence, and operations
platform — CS4032 Software Construction and Design, Assignment 1.

A citizen submits a free-text complaint + location; the backend validates
it, classifies it through a replaceable AI triage provider (with
deterministic fallback), persists it in PostgreSQL, and exposes it to an
operations dashboard. Redis provides read-through stats caching and
distributed rate limiting.

## Current status

**Milestones 1–5 (backend foundation, database, AI triage + Redis, complete
API + tests, and the React frontend) are implemented.** Docker/Compose
(Milestone 6), Kubernetes (Milestone 7–8), and CI/CD (Milestone 9) are not
yet built — see `docs/Milestones.md` for the full build order and
`docs/architecture.md` for the complete system design (including the parts
not yet implemented).

Full architectural decisions, contracts, and rationale live in `docs/` — see
`CLAUDE.md` for the documentation map. This README is a practical
quickstart, not a spec.

## Backend quickstart

Requires: Python 3.12+, [`uv`](https://docs.astral.sh/uv/), a local
PostgreSQL 16+ and Redis 7+ (native install, or via Docker once Milestone 6
lands).

```bash
cd backend
uv sync                          # installs deps + creates .venv

# One-time: create the app role/databases (adjust to your local Postgres setup)
sudo -u postgres psql \
  -c "CREATE ROLE civicpulse WITH LOGIN PASSWORD 'civicpulse';" \
  -c "CREATE DATABASE civicpulse OWNER civicpulse;" \
  -c "CREATE DATABASE civicpulse_test OWNER civicpulse;"

cp ../.env.example .env          # defaults work as-is for local dev

uv run alembic upgrade head      # apply schema
uv run python -m app.seed        # idempotent seed, ≥30 complaints

uv run uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive OpenAPI UI.

### Tests

```bash
cd backend
uv run ruff check .              # lint
uv run mypy app                  # types
uv run pytest tests/unit -q      # no DB/Redis required
uv run pytest tests/ --cov=app --cov-report=term-missing -q   # full suite, needs civicpulse_test + Redis
```

Integration tests run against a real `civicpulse_test` PostgreSQL database
and Redis DB index 15 (both must be reachable at `localhost`; see
`backend/tests/conftest.py`). They flush/truncate their own state before and
after each test and never touch the `civicpulse` dev database.

### Configuration

All settings are environment variables, documented with safe placeholder
values in `.env.example` and loaded via `backend/app/core/config.py`.
Notably `TRIAGE_PROVIDER` (`llm` | `rules` | `simulated`) selects the active
AI triage implementation — CI and local dev default to `simulated`
(deterministic, no network, no API key needed). Setting it to `llm` requires
`LLM_API_KEY` (a [Groq](https://console.groq.com) API key).

## Frontend quickstart

Requires the backend above running on `:8000`.

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173, proxies /api -> http://localhost:8000
```

```bash
cd frontend
npm run lint          # oxlint
npm run build         # tsc -b && vite build
npm run test          # vitest run
```

See `frontend/README.md` and `docs/architecture/frontend.md` for the
runtime-configuration approach (same-origin `/api`, no backend URL baked
into the build) and the typed API client.

## Project layout

```text
backend/app/{routes,services,repositories,providers/{redis,triage},domain,core}/
backend/alembic/versions/       — schema migrations
backend/tests/{unit,integration}/
frontend/src/{api,components,pages}/
frontend/tests/                 — Vitest + Testing Library component tests
docs/architecture/              — the binding technical spec, one file per domain
docs/adr/                       — architecture decision records
docs/Milestones*                — the working implementation checklist
```

Full annotated tree: `docs/architecture/repository-layout.md`.

## License

Coursework project — see `LICENSE`.
