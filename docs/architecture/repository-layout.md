# Repository Layout

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

```text
civicpulse/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── providers/
│   │       ├── redis/
│   │       │   ├── cache.py
│   │       │   └── rate_limiter.py
│   │       └── triage/
│   │           ├── base.py
│   │           ├── llm.py
│   │           ├── rules.py
│   │           ├── simulated.py
│   │           └── factory.py
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   ├── tests/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── nginx.conf
│   └── package.json
│
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── backend.yaml
│   │   ├── frontend.yaml
│   │   ├── postgres.yaml
│   │   ├── redis.yaml
│   │   ├── migrate-job.yaml
│   │   ├── ingress.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   ├── hpa.yaml
│   │   ├── vpa.yaml
│   │   ├── pdb.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/kustomization.yaml
│       └── prod/kustomization.yaml
│
├── load/
│   └── k6-script.js
│
├── docs/
│   ├── architecture.md              # index — this repository
│   ├── architecture/                # domain documents
│   ├── ENGINEERING-NOTES.md
│   ├── RUNBOOK.md
│   ├── AI-USAGE.md
│   ├── TRIAGE.md
│   ├── adr/
│   │   ├── 0001-provider-interface.md
│   │   ├── 0002-frontend-runtime-config.md
│   │   ├── 0003-deploy-by-sha.md
│   │   └── 0004-pii-and-data-governance.md
│   └── evidence/
│
├── scripts/
│   └── check_submission.py
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── release.yml
│
├── compose.yaml
├── compose.prod.yaml
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

Notes on entries that aren't self-explanatory:

- `backend/app/providers/redis/` — the stats-cache and rate-limiter Redis clients. See [`cache.md`](cache.md).
- `backend/app/providers/triage/` — 3 providers (no `ollama.py` — see [`ai.md`](ai.md) §Scope decision).
- `k8s/base/migrate-job.yaml` — the migration `Job`. See [`database.md`](database.md) and [`kubernetes.md`](kubernetes.md).
