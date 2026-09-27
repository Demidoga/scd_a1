# Security Architecture

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

Two cross-cutting security properties: network segmentation (the frontend cannot reach the database) and secret handling (nothing sensitive in source, images, or committed manifests). AI-specific data governance (what leaves the machine and why) is documented in [`ai.md`](ai.md) §AI data governance, since it's specific to the triage provider call.

## 1. Network isolation

```text
Browser
   │
   ▼
frontend
   │ edge only
   ▼
backend ───── internal ───── PostgreSQL
      │                     Redis
      └──── edge → hosted LLM (Groq)
```

Invariant:

```text
frontend ┄X→ PostgreSQL
frontend ┄X→ Redis
```

Full network/volume detail: [`docker-compose.md`](docker-compose.md). Kubernetes equivalent (no public Service on the database, ClusterIP-only): [`kubernetes.md`](kubernetes.md).

## 2. Secret handling

Never commit: LLM API key; DB password; access tokens; `.env`.

Also treat Git history as part of the security boundary: a secret exposed and later deleted is still a leaked secret.

Where secrets actually live per environment (local `.env`, Kubernetes Secret, GitHub Secrets) and CI/CD-specific rules (scoped tokens, least-privilege `permissions:` blocks, no echoed secrets): [`cicd.md`](cicd.md) §CI/CD Security Boundaries.

## 3. Cross-cutting non-functional rules enforced here

- No secrets in source code, frontend bundles, or committed Kubernetes manifests.
- No `latest` deployment target — see [`cicd.md`](cicd.md) §Build Once, Deploy Many.
- No localhost-based service-to-service communication.
- No database/cache exposure through production host ports or public Kubernetes Services.

## 4. Automatic-deduction risks (assignment §5.3)

These map directly to rubric deductions if violated — worth keeping visible here rather than only in the assignment brief:

- `.env`/key/token/password anywhere in Git history.
- LLM API key in a committed Kubernetes manifest, even base64-encoded.
- Unpinned base image, or postgres/redis/node without a tag.
- `localhost` used for service-to-service communication.
- Frontend able to reach the database.
- Published database or cache port in `compose.prod.yaml`, or a NodePort/LoadBalancer Service on the database.
- Publishing or deploying job not gated by `needs:`.
- Deploying `:latest` anywhere.
- PostgreSQL as a Deployment with no PVC.
