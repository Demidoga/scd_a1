<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 475-487 (§4 G). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric G: Docker and Compose (15). Source: §4 G. Index: [../INDEX.md](../INDEX.md). Related: [../09-container-images.md](../09-container-images.md), [../10-docker-compose.md](../10-docker-compose.md).

# **G · Docker and Compose — 15** 

- Both images multi-stage, pinned base, non-root USER, exec-form CMD, cache-correct layer order — **4** 

- .dockerignore per build context, with before/after context sizes reported — **2** 

- Two networks with internal: true; frontend provably cannot reach the database — **4** 

- Three named volumes, each justified; dev bind mount present and absent from prod — **2** 

- Healthchecks on all services with depends_on: condition: service_healthy — **2** 

- compose.prod.yaml uses image: ${IMAGE_TAG}, no build:, no published DB or cache port — **1** 
