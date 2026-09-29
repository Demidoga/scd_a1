<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 579-603 (§5.3). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Automatic deductions. Source: §5.3. Index: [INDEX.md](INDEX.md).

# **5.3 Automatic deductions** 

- A .env, key, token or password **anywhere in Git history** — **−20** , plus you must rotate the credential and write an incident note 

- An LLM API key in a committed Kubernetes manifest, even base64-encoded (base64 is encoding, not encryption) — **−15** 

- Unpinned base image, or postgres / redis / node without a tag — **−8** 

- localhost used for service-to-service communication — **−8** 

- Frontend able to reach the database — network segmentation not implemented — **−8** 

- Published database or cache port in compose.prod.yaml, or a NodePort/LoadBalancer Service on the database — **−8** 

- Publishing or deploying job not gated by needs: — **−8** 

- Deploying :latest anywhere — **−8** 

- PostgreSQL as a Deployment with no PVC — **−8** 

- Commits pushed directly to main — **−5** 

- README quickstart that does not work from a clean clone — **−5** 

Per course policy: **late submissions are not accepted** , and there is no retake. Submit something imperfect on time. 
