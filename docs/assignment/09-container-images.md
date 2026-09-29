<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 234-244 (§3 heading, §3.1). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — DevOps: container images. Source: §3 heading, §3.1. Index: [INDEX.md](INDEX.md). Related: [rubric/G-docker-and-compose.md](rubric/G-docker-and-compose.md).

# **3. DevOps pipeline** 

# **3.1 Container images** 

Two images, both multi-stage, both pinned, both non-root. 

**Backend** — python:3.12-slim base, dependencies installed in a builder stage, cache-friendly COPY order (requirements before source), non-root USER, CMD in exec form, HEALTHCHECK declared. Pin by digest for the bonus. 

**Frontend** — node:22-alpine builds, nginx:1.27-alpine serves. The final image contains no Node, no node_modules, no source. Report both stage sizes; a frontend image over ~60 MB means the multi-stage split is not doing its job. 

**.dockerignore in each build context** — .git, node_modules, .venv, __pycache__, .env, test fixtures. Report build-context size before and after, with numbers. 
