<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 343-393 (§3.4). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — DevOps: CI/CD workflows, non-negotiables, rollback. Source: §3.4. Index: [INDEX.md](INDEX.md). Related: [rubric/I-cicd.md](rubric/I-cicd.md).

# **3.4 CI/CD** 

Three workflows. Two branches: dev for work, main for deployable software, main protected with required checks and one approval. 

# **ci.yml — on pull request to main, on push to dev** 

|**Job**|**Steps**|
|---|---|
|lint-and-type|ruff + mypy on the backend; eslint + tsc --noEmit on the frontend|
|test-backend|pytest with coverage ≥ 65% on app/, TRIAGE_PROVIDER=simulated|
|test-frontend|Vitest component tests, ≥ 5 meaningful tests|
|build|Build both images.**Do not push.**A PR must not publish artifacts.|
|scan|Trivy on both images, failing on HIGH/CRITICAL with a fixed version<br>available|
|manifests|kustomize build overlays/prod piped to kubeconform — catches a broken<br>manifest in 20 seconds instead of on the cluster|
|integration|docker compose up -d, wait for /ready, POST a complaint, GET it back, assert<br>the category, check X-Cache goes MISS → HIT, docker compose down -v|



The integration job is the direct answer to Lecture 03's question — _does my code work with everybody else's code?_ — and it is the job that will catch your localhost bug before a human does. 

# **cd.yml — on push to main** 

|**Job**|**Steps**|
|---|---|
|test|The full suite again, on the merged result|
|build-pus|needs: test. Build both images, push to**GHCR**tagged ${{ github.sha }} and latest.|
|h|Emit an SBOM with Syft. Capture the image**digest**as a job output.|
|deploy-k|needs: build-push. Spin up a kind/k3d cluster in the runner, apply overlays/prod|
|8s|with the SHA tag, wait for kubectl rollout status, run a smoke test against the<br>Ingress, print kubectl get hpa.|



**release.yml — on tag v*** — build, push semver tags, generate release notes. 

# **Non-negotiables.** 

- needs: on every publishing and deploying job. Without it you publish artifacts from code you already know is broken. 

- Deploy by **immutable reference** — commit SHA, or the digest for the bonus. :latest may be pushed; it may never be deployed. "What is production running?" must have a one-word answer you can paste into git show. 

- All credentials from GitHub Secrets. A **scoped, revocable registry token** , never an account password. GITHUB_TOKEN with packages: write is the cleanest path for GHCR. 

- Least-privilege permissions: block on every workflow. The default is broader than you need. 

- Actions pinned — @v4 at minimum, a commit SHA for the bonus. 

- **Evidence the gate works:** a PR with a deliberately failing test, screenshot of the red check and the blocked merge button, fixed in the same PR, screenshot of green. 

**Rollback.** Two mechanisms, both demonstrated on video: kubectl rollout undo deployment/backend -n civicpulse (fast, imperative, the 3 a.m. answer), and re-applying the 

previous overlay with the previous SHA (declarative, auditable, the correct answer once the fire is out). Explain when you would use each. 
