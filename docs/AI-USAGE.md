# AI Usage Disclosure

Required by the course's AI-assistance policy (`docs/assignment/17-viva-and-ai-usage.md` §5.5): name the tools, say which parts they wrote or shaped, and say what was changed afterwards and why. Specific disclosure carries no penalty.

**Status of this file.** Parts marked **[AUTHORS TO COMPLETE]** are facts only the two team members know (what they personally rewrote, the partner's tools). They are left visibly open rather than guessed. Fill them in before submission; `python scripts/check_submission.py` does not check them.

## Tools

| Tool | Used by | For |
|---|---|---|
| **Claude Code** (Anthropic's command-line coding agent, Claude models) | Asad Ahmed | Most of the implementation, documentation and repository tooling, described below. `CLAUDE.md` at the repository root is the project-instruction file it reads on every session. |
| **Impeccable** (a design skill loaded inside Claude Code; its local config is `.impeccable/config.local.json`) | Asad Ahmed | Frontend visual design and accessibility pass (commit "enhance UI with dark theme and improved accessibility"). |
| **[AUTHORS TO COMPLETE]** | tawassulAkbr | The partner's tools, if any. The commits for Docker verification, HPA/VPA and load testing, and Trivy/CI fixes are theirs; state which parts were AI-assisted. |

## What AI wrote or shaped

Stated at the level the repository record supports. Where the record cannot show who wrote a line, it says so.

- **Architecture and planning documents.** `docs/architecture/*.md`, `docs/Milestones*`, `docs/Todo.md`, `docs/progress.md`, the split of the assignment into `docs/assignment/`, and the four ADRs in `docs/adr/` were drafted with Claude Code from the assignment text, then used as the working spec for the implementation.
- **Backend (Milestones 1–4).** The four-layer FastAPI service, the domain contract and status transition table, repositories, the three triage providers, the retry/fallback pipeline, Redis cache and rate limiter, and the test suite were generated with Claude Code against those documents.
- **Frontend (Milestone 5).** The React views, typed API client and component tests were generated with Claude Code; the visual design pass used the Impeccable skill.
- **Containers, Compose and Kubernetes (Milestones 6–8).** Dockerfiles, `compose*.yaml`, the Kustomize manifests, `scripts/k8s/*` and the manifest invariants checker were written with AI assistance. Live verification and the load-test runs were carried out on real Docker and k3d installs, and their outputs are committed under `docs/evidence/` and `load/results/`.
- **CI/CD (Milestone 9).** `.github/workflows/ci.yml`, `cd.yml`, `release.yml` and `docs/CI-CD-SETUP.md`.
- **Audit and hardening pass (2026-09-29, Claude Code).** Against the assignment rubric, it produced: the `release.yml` test gate; action version pins; stricter CI integration assertions and pinning the integration job to the simulated provider; `.mailmap`; the seed idempotency test (`backend/tests/integration/test_seed.py`); the React 18 downgrade; `docs/RUNBOOK.md`; `scripts/check_submission.py`; the README problem statement, badges, Mermaid diagram and API table; and drafts of engineering-note answers Q1–Q4, Q7 and Q8.

## What was checked, corrected or overridden afterwards

Things that were wrong in the AI-assisted work and had to be fixed, with how each was found:

| What was wrong | How it was found | Fix |
|---|---|---|
| `nginx.conf` sent every `/api/...` request to a bare `/api/` on the backend (a variable in `proxy_pass` disables prefix rewriting). | Live Compose run, not static checks. | Removed the trailing URI from `proxy_pass` (`frontend/nginx.conf`). |
| Frontend `HEALTHCHECK` always failed (`localhost` resolved to IPv6 while nginx listened on IPv4). | `docker compose ps` never reached `healthy`. | Probe `127.0.0.1` (`frontend/Dockerfile`). |
| The `migrate` Job crashed because Kubernetes injected `BACKEND_PORT=tcp://…`. | First live k3d deploy. | `enableServiceLinks: false`, enforced by the invariants script. |
| `create-secrets.sh` used process substitution that `kubectl.exe` cannot read on Windows. | Run on Windows. | Real temp file. |
| `BACKEND_PORT` in Compose was inert (nothing consumed it). | Re-verification pass. | Made the published host port follow it. |
| Frontend image 74.5 MB against a ~60 MB target. | Measured with `docker images`. | Switched to `nginx:1.27-alpine-slim` (20.3 MB). |
| CI integration job ran the LLM/rules provider, not the simulated one, after `.env.example` changed its default. | Audit against the assignment's "deterministic CI" requirement. | Job now sets `TRIAGE_PROVIDER: simulated`. |
| `release.yml` published images with no `needs:` gate; several actions were below `@v4`. | Audit against the assignment's CI/CD non-negotiables. | Reused `ci.yml` as a gate; bumped action versions. |

**[AUTHORS TO COMPLETE]** Add, in your own words, the changes you made by hand to AI-generated code and why (for example design decisions you overruled, code you rewrote to understand it, or prompts that produced something you rejected). The viva asks you to defend every line regardless of who wrote it, so list the parts you are ready to explain and modify live.

## Honest limits

- AI-generated tests passing does not by itself show the behaviour is right; the live runs above are what caught the real bugs.
- Documentation written by AI from the repository record (for example the engineering-note drafts for Q2 and Q8) carries a note asking the authors to confirm details only they can know.
- Secrets: `.env` is untracked and a pattern scan of the full git history found no keys (`scripts/check_submission.py`). The scan says nothing about what a local AI tool can read from an untracked file in the working directory, so treat any key that has been in a local `.env` while an AI tool was running as exposed to that tool and rotate it if that matters to you. **[AUTHORS TO COMPLETE]** State your practice.
