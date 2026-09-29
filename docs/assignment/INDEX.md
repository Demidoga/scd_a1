# CivicPulse Assignment 1 — Spec Index (start here)

This folder is the **assignment specification** (CS4032 Software Construction and Design, Assignment 01 — CivicPulse), split into focused files.

- Every file's body is a **verbatim excerpt** of the original: `docs/Software Construction and Design -  Assignment 1.md` (PDF alongside). Nothing was reworded, summarized, or reinterpreted. Each file's first line is an HTML comment giving the exact source line range.
- This is **not** the architecture documentation. `docs/architecture.md` and `docs/architecture/*.md` are the project's *design decisions* (how we chose to satisfy the assignment). This folder is *what the assignment requires and how it is graded*. When they seem to differ, the assignment text here is the requirement; the architecture docs record decisions (e.g. the instructor-approved removal of Ollama noted in `CLAUDE.md`).
- The original had no §5.6; numbering here follows the source.

## How to use

1. Find your task in the routing table below.
2. Read the listed spec file(s). For any implementation task, also read the matching **rubric** file (that is how the work is graded) and check [16-automatic-deductions.md](16-automatic-deductions.md).
3. Then read the matching `docs/architecture/*.md` file for how this project implements it.

## Routing by task

| If your task involves... | Read (spec) | Then check (grading) |
|---|---|---|
| Understanding the product, goals, "what done means" | [00-overview.md](00-overview.md) | [rubric/README.md](rubric/README.md) |
| Overall component diagram | [01-system-architecture.md](01-system-architecture.md) | — |
| React app, views, runtime config, typed client, error boundary | [02-frontend.md](02-frontend.md) | [rubric/B-frontend.md](rubric/B-frontend.md) |
| Backend layering, endpoints, status codes, `/health` vs `/ready`, `/metrics` | [03-backend-layering-and-api.md](03-backend-layering-and-api.md) | [rubric/C-backend.md](rubric/C-backend.md) |
| Status state machine, SIGTERM shutdown, JSON logging / `request_id` | [04-backend-domain-rules.md](04-backend-domain-rules.md) | [rubric/C-backend.md](rubric/C-backend.md) |
| PostgreSQL schema, Alembic, indexes, seed script, persistence | [05-data-layer.md](05-data-layer.md) | [rubric/D-data-layer.md](rubric/D-data-layer.md) |
| Redis stats cache, rate limiter, AOF | [06-cache-layer.md](06-cache-layer.md) | [rubric/E-cache-layer.md](rubric/E-cache-layer.md) |
| `TriageProvider` interface, provider implementations, Groq/Gemini/Ollama, PII ADR | [07-ai-interface-and-providers.md](07-ai-interface-and-providers.md) | [rubric/F-ai-layer.md](rubric/F-ai-layer.md) |
| LLM timeout/retry/fallback/cache, prompt injection, deterministic tests, the fallback test | [08-ai-reliability-and-testing.md](08-ai-reliability-and-testing.md) | [rubric/F-ai-layer.md](rubric/F-ai-layer.md) |
| Dockerfiles, `.dockerignore`, image sizes | [09-container-images.md](09-container-images.md) | [rubric/G-docker-and-compose.md](rubric/G-docker-and-compose.md) |
| Compose files, networks, volumes, healthchecks, prod vs dev | [10-docker-compose.md](10-docker-compose.md) | [rubric/G-docker-and-compose.md](rubric/G-docker-and-compose.md) |
| Kubernetes objects, Kustomize, probes, rolling updates | [11-kubernetes-manifests-and-probes.md](11-kubernetes-manifests-and-probes.md) | [rubric/H-kubernetes.md](rubric/H-kubernetes.md) |
| HPA, VPA, load test, scaling evidence | [12-kubernetes-autoscaling.md](12-kubernetes-autoscaling.md) | [rubric/H-kubernetes.md](rubric/H-kubernetes.md) |
| GitHub Actions (`ci.yml`, `cd.yml`, `release.yml`), secrets, rollback | [13-cicd.md](13-cicd.md) | [rubric/I-cicd.md](rubric/I-cicd.md) |
| Git workflow, branches, PRs, commits, merge conflict, branch protection | [rubric/A-collaboration-and-version-control.md](rubric/A-collaboration-and-version-control.md) | — |
| README, ADRs, RUNBOOK, demo video, engineering notes | [rubric/J-documentation-and-reflection.md](rubric/J-documentation-and-reflection.md), [15-engineering-notes-questions.md](15-engineering-notes-questions.md) | — |
| Bonus items | [rubric/K-bonus.md](rubric/K-bonus.md) | — |
| Prioritizing work when behind, team-size variants | [14-scope-and-priorities.md](14-scope-and-priorities.md) | — |
| Answering `docs/ENGINEERING-NOTES.md` (the eight questions) | [15-engineering-notes-questions.md](15-engineering-notes-questions.md) | [rubric/J-documentation-and-reflection.md](rubric/J-documentation-and-reflection.md) |
| Penalties to avoid | [16-automatic-deductions.md](16-automatic-deductions.md) | — |
| Viva, `AI-USAGE.md` disclosure | [17-viva-and-ai-usage.md](17-viva-and-ai-usage.md) | — |
| Where files/folders must live | [18-repository-layout.md](18-repository-layout.md) | — |
| What to submit, `check_submission.py` | [19-submission.md](19-submission.md) | — |

## Routing by layer / concern (quick lookup)

| Concern | Files |
|---|---|
| Frontend | 02, rubric/B |
| Backend | 03, 04, rubric/C |
| Database | 05, rubric/D |
| Redis (cache + rate limit) | 06, rubric/E |
| AI / triage | 07, 08, rubric/F |
| Docker / Compose | 09, 10, rubric/G |
| Kubernetes | 11, 12, rubric/H |
| CI/CD | 13, rubric/I |
| Docs, ADRs, evidence, video | 15, 17, 18, 19, rubric/J, rubric/A |
| Security-relevant rules | 02 (no secrets in bundle), 07 (PII ADR), 08 (API key, injection), 10 (networks), 13 (secrets, permissions), 16 |
| Anything graded | rubric/ (all), 16 |

## File list (in original order)

| File | Original section |
|---|---|
| [00-overview.md](00-overview.md) | Cover table, §1.1–§1.4 |
| [01-system-architecture.md](01-system-architecture.md) | §2 heading + diagram |
| [02-frontend.md](02-frontend.md) | §2.1 |
| [03-backend-layering-and-api.md](03-backend-layering-and-api.md) | §2.2 Stack, Layering, API contract |
| [04-backend-domain-rules.md](04-backend-domain-rules.md) | §2.2 Domain rules |
| [05-data-layer.md](05-data-layer.md) | §2.3 |
| [06-cache-layer.md](06-cache-layer.md) | §2.4 |
| [07-ai-interface-and-providers.md](07-ai-interface-and-providers.md) | §2.5 interface, providers, free endpoints |
| [08-ai-reliability-and-testing.md](08-ai-reliability-and-testing.md) | §2.5 engineering around the model, determinism |
| [09-container-images.md](09-container-images.md) | §3 heading, §3.1 |
| [10-docker-compose.md](10-docker-compose.md) | §3.2 |
| [11-kubernetes-manifests-and-probes.md](11-kubernetes-manifests-and-probes.md) | §3.3 objects, probes, rolling updates |
| [12-kubernetes-autoscaling.md](12-kubernetes-autoscaling.md) | §3.3 HPA, VPA |
| [13-cicd.md](13-cicd.md) | §3.4 |
| [rubric/](rubric/README.md) | §4 (A–J + Bonus, one file each; 150 marks + up to +15) |
| [14-scope-and-priorities.md](14-scope-and-priorities.md) | §5 heading, §5.1 |
| [15-engineering-notes-questions.md](15-engineering-notes-questions.md) | §5.2 |
| [16-automatic-deductions.md](16-automatic-deductions.md) | §5.3 |
| [17-viva-and-ai-usage.md](17-viva-and-ai-usage.md) | §5.4, §5.5 |
| [18-repository-layout.md](18-repository-layout.md) | §5.7 |
| [19-submission.md](19-submission.md) | §5.8 |

## Rubric files (marks)

| File | Section | Marks |
|---|---|---|
| [rubric/A-collaboration-and-version-control.md](rubric/A-collaboration-and-version-control.md) | A | 15 |
| [rubric/B-frontend.md](rubric/B-frontend.md) | B | 18 |
| [rubric/C-backend.md](rubric/C-backend.md) | C | 25 |
| [rubric/D-data-layer.md](rubric/D-data-layer.md) | D | 12 |
| [rubric/E-cache-layer.md](rubric/E-cache-layer.md) | E | 10 |
| [rubric/F-ai-layer.md](rubric/F-ai-layer.md) | F | 25 |
| [rubric/G-docker-and-compose.md](rubric/G-docker-and-compose.md) | G | 15 |
| [rubric/H-kubernetes.md](rubric/H-kubernetes.md) | H | 20 |
| [rubric/I-cicd.md](rubric/I-cicd.md) | I | 20 |
| [rubric/J-documentation-and-reflection.md](rubric/J-documentation-and-reflection.md) | J | 15 |
| [rubric/K-bonus.md](rubric/K-bonus.md) | Bonus | up to +15 |

## Known source quirks (preserved, not corrected)

- The architecture diagram in `01-system-architecture.md` is OCR text from a picture; the original PDF has the real figure.
- Some tables in the source are garbled by conversion (e.g. the API table's `Method` header and `X-Cache: HIT|MISS` cell, the CD job names `build-push` / `deploy-k8s`). Read them with the surrounding prose; the PDF is the tie-breaker.
- `<cite index=...>` tags in the Groq/Gemini text are artifacts of the source.
