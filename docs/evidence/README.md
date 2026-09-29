# Evidence index

Where each piece of assignment evidence lives. Files are kept where the tooling wrote them; this page is the map.

| Evidence | Location |
|---|---|
| Frontend cannot reach the database (network isolation failing) | `milestone-6/frontend-db-isolation.txt` |
| PostgreSQL data survives `docker compose down` / `up` | `milestone-6/postgres-persistence.txt` |
| Image sizes (frontend 74.5 MB → 20.3 MB) | `milestone-6/image-sizes.txt` |
| `.dockerignore` build-context sizes, before/after | `milestone-6/build-context.txt` |
| Volumes and their justification | `milestone-6/volumes-and-scope.txt` |
| `kubectl get hpa -w` captures (two load runs) | `../../load/results/hpa-watch.log`, `hpa-watch-2.log` |
| Replicas-vs-load charts | `../../load/results/hpa-run1-replicas-vs-load.png`, `hpa-run2-replicas-vs-load.png` |
| k6 output and summaries (ramp, resized, rollout) | `../../load/results/k6-*.log`, `k6-*-summary.json` |
| Zero-downtime rolling update under load (0.00% failed of 36,294) | `../../load/results/k6-rollout-output.log`, `k6-rollout-summary.json` |
| VPA Target / Lower Bound / Upper Bound, HPA lag analysis | `../ENGINEERING-NOTES.md` (Milestone 8, Q5, Q6) |
| Kubernetes Postgres pod deletion preserves data | Procedure `../../scripts/k8s/verify-persistence.sh`; result recorded in `../progress.md` (Milestone 7). **No output file committed yet.** |
| Fallback behavior | Test `../../backend/tests/integration/test_fallback_e2e.py`. **No captured run output yet.** |
| Cache MISS → HIT | Asserted by the `integration` job in `.github/workflows/ci.yml`; the run log on GitHub is the evidence. **Not captured here yet.** |

## Still to capture (cannot be produced from the repository alone)

Each needs GitHub or a live cluster, so it has to be done by hand. Save the file in this folder and add a row above.

- Branch protection settings screenshot (`docs/CI-CD-SETUP.md` §2).
- Deliberately failing PR: red check and disabled merge button, then green after the fix (`docs/CI-CD-SETUP.md` §4).
- A successful `cd.yml` run link, and the GHCR package pages showing SHA tags.
- The deliberate merge conflict: markers, resolution, and the merge commit.
- `kubectl rollout undo` and re-deploy of a previous SHA, with output.
- README screenshots of the submit, dashboard and stats views (`screenshots/`).
