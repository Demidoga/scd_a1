<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 76-113 (§2.2 (Stack, Layering, API contract)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Backend: stack, layering, API contract, probe rationale. Source: §2.2 (Stack, Layering, API contract). Index: [INDEX.md](INDEX.md). Related: [04-backend-domain-rules.md](04-backend-domain-rules.md), [rubric/C-backend.md](rubric/C-backend.md).

# **2.2 Backend layer** 

**Stack:** FastAPI + Pydantic v2 (recommended) or Flask (permitted; say so in the README). FastAPI is recommended because its OpenAPI schema is what your frontend client is typed against, and because Pydantic models give you the same validation machinery for HTTP input _and_ for LLM output — one mental model, two uses. 

# **Layering** 

Four layers, and the dependency arrows point one way only: 

routes/      HTTP only — parse, validate, serialise, status codes. No business rules. services/    Business rules — triage orchestration, state machine, statistics. repositories/  Persistence — all SQL lives here, and nowhere else. 

providers/   Outbound integrations — LLM, cache. Behind interfaces. 

A route that opens a database session is a design failure worth marks. This is Lecture 01's Era 3 and Era 5 material — decomposition and abstraction — applied to something you actually wrote. 

# **API contract** 

|**Metho**|**Path**|**Behaviour**|
|---|---|---|
|**d**|||
|POST|/api/complaints|Validate → triage → persist. 201. 400 with a|
|||field-level error body. 429 when the caller|
|||exceeds the rate limit.|
|GET|/api/complaints/{id}|200 / 404|



|GET|/api/complaints|Filter by category, priority, status; paginate (page,<br>page_size ≤ 100); return total.|
|---|---|---|
|PATCH|/api/complaints/{id}/status|Enforce the state machine. Invalid transition →<br>409 naming the attempted transition.|
|GET|/api/stats|Aggregates, Redis-cached, TTL 30 s, `X-Cache:<br>HIT|
|GET|/api/meta/providers|Which triage provider is active, and the last 20<br>triage outcomes (provider, latency ms, fallback<br>y/n). This is your observability surface.|
|GET|/health|Liveness. Process is alive.**Must not touch the**<br>**database.**|
|GET|/ready|Readiness. 200 only if Postgres and Redis are<br>both<br>reachable;<br>503<br>naming<br>the<br>failed<br>dependency.|
|GET|/metrics|Prometheus text format: request count, request<br>latency histogram, triage latency, fallback counter.|



/health and /ready are separate because Kubernetes uses them for different decisions: a failing liveness probe **restarts your pod** , a failing readiness probe **removes it from the Service** . Wire them backwards and a slow database becomes a restart loop across your entire deployment. This is Lecture 04's depends_on lesson, promoted to production consequences. 
