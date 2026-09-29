# Deliberate merge conflict

Two branches cut from `dev` changed the same two lines of real code, the LLM retry-delay window in `backend/app/services/triage.py` (`_RETRY_JITTER_MIN_SECONDS` / `_RETRY_JITTER_MAX_SECONDS`):

- `feature/retry-jitter-shorter` set it to 0.1–0.3 s (users wait less).
- `feature/retry-jitter-wider` set it to 0.5–1.5 s (spread retries out).

Merging one into the other stopped with a content conflict.

| File | What it shows |
|---|---|
| `1-conflict-markers.txt` | The `git merge` failure, `git status`, and the `<<<<<<<` / `=======` / `>>>>>>>` markers in the file |
| `2-resolution.txt` | The diff of the resolved merge commit (`ec4dd89`) |
| `3-merge-history.txt` | `git log --graph` showing the two branches and the merge commit |

## Why the wider window won

The backend runs up to 10 pods under the HPA, all sharing one LLM quota, so a `429` reaches many pods at the same moment. A 0.2-second window barely separates their single retry, so they return together and hit the limit again. The extra second at most is only paid by a request that has already failed once and would otherwise fall back to the rules, so it costs little against the 10-second call timeout.
