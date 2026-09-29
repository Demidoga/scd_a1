<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 503-517 (§4 I). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric I: CI/CD (20). Source: §4 I. Index: [../INDEX.md](../INDEX.md). Related: [../13-cicd.md](../13-cicd.md).

# **I · CI/CD — 20** 

- ci.yml running lint, type check, backend and frontend tests on every PR, configured as required checks — **4** 

- Compose integration smoke job asserting a real request path end to end — **3** 

- Trivy image scan and kubeconform manifest validation in CI — **3** 

- cd.yml with needs: gating publish, images pushed to GHCR tagged by commit SHA — **4** 

- Kubernetes deploy job on an ephemeral cluster, waiting on rollout status and smoke-testing the Ingress — **3** 

- Secrets from GitHub Secrets with a scoped token and a least-privilege permissions: block — **2** 

- Evidence of a red pipeline blocking a merge, then green — **1** 
