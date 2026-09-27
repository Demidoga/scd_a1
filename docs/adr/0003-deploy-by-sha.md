# ADR 0003 — Deploy by Immutable SHA

## Status

Accepted. (Recorded during Milestone 1 as a binding invariant for the CI/CD
work built in Milestone 9 — noted now so it can't drift into "just use
`latest`" once the pipeline is actually written.)

## Context

Kubernetes deployments referencing a mutable tag (`:latest`, `:dev`) are a
well-known source of "it worked yesterday" failures: the same manifest can
resolve to a different image at different times, rollbacks become
guesswork (which `latest` was actually running an hour ago?), and a cluster
can silently drift from what was reviewed/approved in a PR. The assignment
requires build-once-deploy-many and a reproducible, auditable deployment
history — both are incompatible with mutable tags as the deploy target.

## Decision

```text
merge to main (post PR approval)
        ↓
ci.yml/cd.yml builds ONE image
        ↓
tag with the commit SHA (and optionally `latest` for convenience)
        ↓
Trivy scan + Syft SBOM against that SHA-tagged image
        ↓
push to GHCR
        ↓
k8s manifests are updated to reference the exact SHA digest
        ↓
kubectl apply / kustomize deploys that exact SHA
```

Rules that follow directly from this:

- **`latest` may be pushed, but is never a deployment target.** It exists
  purely as a convenience tag for someone pulling the image manually to
  poke at it — no Kubernetes manifest, Compose prod file, or CD step is
  allowed to reference it.
- **CI never publishes.** `ci.yml` runs on every PR/push and does lint,
  type-check, tests, a build (to prove it builds), Trivy/kubeconform — but
  does not push to GHCR. Only `cd.yml`, triggered by a push to `main` after
  PR approval, publishes an image.
- **One build, many deploys.** The same SHA-tagged image that passed CI is
  what gets deployed to `overlays/dev` and (eventually) `overlays/prod` —
  never a fresh build per environment. This is the same build-once
  principle ADR 0002 applies to the frontend bundle, extended to the whole
  container.
- **Migrations gate traffic, not the deploy step.** The `migrate` Job
  (`docs/architecture/database.md` §2) runs the same SHA-tagged backend
  image with `alembic upgrade head` and must reach `Complete` before the
  backend Deployment's rollout proceeds — so "deploy by SHA" also means
  "the schema that SHA expects is guaranteed present before it receives
  traffic," not just "the right binary is running."

## Consequences

- Rollback is "redeploy the previous SHA," a one-line, auditable operation —
  not "figure out what `latest` used to point at."
- Every running pod's image digest is traceable to exactly one commit, one
  PR, one set of CI results (including its Trivy scan and SBOM) — required
  for the assignment's security/traceability expectations
  (`docs/architecture/security.md`, `docs/architecture/cicd.md`).
- This costs nothing at CivicPulse's scale (a coursework project with one
  environment cadence), so there's no real tradeoff being accepted here —
  it's strictly better than tag-based deploys for both safety and the
  assignment's own build-once-deploy-many requirement.
