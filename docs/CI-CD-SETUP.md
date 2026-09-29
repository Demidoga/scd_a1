# CI/CD Setup Guide

> Part of the CivicPulse architecture. Design/rationale: [`docs/architecture/cicd.md`](architecture/cicd.md). This file is the operational "how to turn it on" companion — read `cicd.md` first if you want the *why*.

Three workflows live in `.github/workflows/`:

| Workflow | Trigger | Publishes? | Deploys? |
|---|---|---|---|
| `ci.yml` | PR → `main`, push → `dev` | No | No |
| `cd.yml` | push → `main` | Yes (GHCR, SHA + `latest`) | Yes (ephemeral k3d, by SHA) |
| `release.yml` | tag `v*` | Yes (GHCR, semver tag) | No |

## 1. Required repository Secrets

Settings → Secrets and variables → Actions → New repository secret:

| Secret | Required | Used for |
|---|---|---|
| `POSTGRES_PASSWORD` | Yes | Builds the real Kubernetes `civicpulse-secrets` Secret at deploy time (`cd.yml` → `deploy-k8s`). Letters/digits/`. _ ~ -` only — it is embedded in `DATABASE_URL`. |
| `LLM_API_KEY` | No | Groq key for `TRIAGE_PROVIDER=llm` (the prod overlay's default). If unset, the triage pipeline falls back to the rule-based provider automatically — never a 500. |

`GITHUB_TOKEN` needs no setup — GitHub injects it automatically, scoped by each workflow's own `permissions:` block (§3).

## 2. Branch protection on `main`

Settings → Branches → Add branch protection rule → branch name pattern `main`:

- [x] Require a pull request before merging
  - [x] Require approvals — **1**
- [x] Require status checks to pass before merging
  - Search for and require the `ci.yml` job names: `Lint & type check`, `Backend tests`, `Frontend tests`, `Build images`, `Trivy vulnerability scan`, `Validate Kubernetes manifests`, `Compose integration smoke test`
  - [x] Require branches to be up to date before merging
- [x] Do not allow bypassing the above settings (optional, recommended for the "red pipeline blocks merge" demonstration in §4)

This encodes the branch model in `docs/architecture/cicd.md` §1: `main` is deployable software, reached only through a reviewed, CI-passed PR — never a direct push.

## 3. Least-privilege token permissions

Two places this is enforced:

1. **Repo default** — Settings → Actions → General → Workflow permissions → **Read repository contents permission** (not "Read and write"). Individual workflows escalate explicitly where they need to (below), rather than relying on a broad default.
2. **Per-workflow `permissions:` block** — already declared at the top of each file, least-privilege per job's actual need:
   - `ci.yml`: `contents: read` only (never publishes).
   - `cd.yml`: `contents: read`, `packages: write` (GHCR push via `GITHUB_TOKEN`).
   - `release.yml`: `contents: write` (to create the GitHub Release), `packages: write`.

No long-lived account password or PAT is stored anywhere — every registry login uses the short-lived, per-run `GITHUB_TOKEN`.

## 4. Verifying a red pipeline blocks merge, then goes green

1. Create a branch off `dev`, introduce a deliberate failure (e.g. a Ruff violation in `backend/app/`, or an assertion the integration smoke test will catch), commit, push.
2. Open a PR into `main`. Watch the required checks run in the **Checks** tab — one should go red.
3. On the PR page, confirm the **Merge** button is disabled with "Required statuses must pass" (branch protection from §2 doing its job).
4. Push a fix commit to the same branch. The failed job re-runs; once every required check is green, the merge button re-enables.
5. Merge. `cd.yml` fires on the resulting push to `main`: full suite re-run → build/push/SBOM → migrate + deploy to an ephemeral k3d cluster → Ingress smoke test → HPA status printed. All green is your evidence.

Keep a screenshot of the red state (step 2–3) and the green state (step 5) — both are useful evidence artifacts for the assignment submission (`docs/evidence/`).

## 5. Rollback procedures

Both modes are described in `docs/architecture/kubernetes.md` §14; commands below assume `kubectl` is pointed at the target cluster (`kubectl config current-context`).

### 5.1 Imperative rollback (fast response)

Undo the most recent backend rollout immediately, without touching the Git history:

```bash
kubectl rollout undo deployment/backend -n civicpulse

# watch it come back
kubectl rollout status deployment/backend -n civicpulse

# confirm the running image
kubectl get deployment/backend -n civicpulse -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

To go back further than one revision:

```bash
kubectl rollout history deployment/backend -n civicpulse
kubectl rollout undo deployment/backend -n civicpulse --to-revision=<N>
```

Use this when restoring service is more urgent than restoring an auditable, declared state — it changes the live cluster but not the repository.

### 5.2 Declarative rollback (auditable)

Re-deploy the exact previous known-good commit SHA through the same path CD uses, so the repository and the cluster agree on what "current" means:

```bash
# find the previous good SHA, e.g. from `git log --oneline main` or the
# last known-good GHCR tag at ghcr.io/<owner>/civicpulse-backend
PREV_SHA=<previous-commit-sha>

scripts/k8s/deploy.sh prod "$PREV_SHA"
scripts/k8s/smoke-test.sh
```

`deploy.sh` refuses `latest` and any unresolved placeholder tag, deletes the previous `Job/migrate` before re-applying (a Job's pod template is immutable), waits for it to reach `Complete`, then waits for every rollout — the same sequence `cd.yml`'s `deploy-k8s` job runs. This is preferable when you want the rollback itself to be a reviewable, re-runnable step (e.g. via a manual `workflow_dispatch` re-run against an older SHA) rather than an undocumented cluster mutation.

**Note on migrations:** an imperative rollback does not undo a schema migration. If the previous SHA depended on a schema the new migration changed incompatibly, the declarative path (re-running `deploy.sh` at the old SHA, which re-triggers `Job/migrate`) only helps if the migration itself is backward-compatible or was written with a corresponding down-migration (`alembic downgrade`). Roll back application code and schema together, and prefer additive, backward-compatible migrations so `rollout undo` alone is sufficient in the common case.
