<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 619-653 (§5.7). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Required repository layout. Source: §5.7. Index: [INDEX.md](INDEX.md).

# **5.7 Repository layout** 

civicpulse/ 

├── backend/ 

- │   ├── app/{routes,services,repositories,providers}/ 

- │   ├── app/providers/triage/{base,llm,ollama,rules,simulated,factory}.py 

- │   ├── alembic/versions/ 

- │   ├── tests/ 

- │   ├── Dockerfile · .dockerignore · pyproject.toml ├── frontend/ 

- │   ├── src/{components,pages,api}/ 

- │   ├── tests/ 

- │   ├── Dockerfile · .dockerignore · nginx.conf · package.json ├── k8s/ 

- │   ├── base/{namespace,backend,frontend,postgres,redis,ingress,configmap,secret}.yaml 

- │   ├── base/{hpa,vpa,pdb}.yaml · kustomization.yaml 

- │   └── overlays/{dev,prod}/kustomization.yaml 

├── load/k6-script.js ├── docs/ 

- │   ├── ENGINEERING-NOTES.md · RUNBOOK.md · AI-USAGE.md · TRIAGE.md 

- │   ├── adr/0001-provider-interface.md … 0004-pii-and-data-governance.md 

│   └── evidence/        # screenshots: protection, conflict, blocked merge, hpa -w, scaling chart ├── scripts/check_submission.py ├── .github/workflows/{ci.yml,cd.yml,release.yml} ├── compose.yaml · compose.prod.yaml · .env.example · .gitignore └── README.md · LICENSE 
