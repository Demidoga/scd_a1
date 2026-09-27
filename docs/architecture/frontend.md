# Frontend Architecture

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).

## Purpose

The frontend accepts citizen complaints (submission UI + `POST /api/complaints`) and lets operators work the queue (dashboard: filter, paginate, transition status; stats view with cache-state display).

## 1. Responsibilities

The frontend is a presentation and interaction layer only.

It is responsible for:

- collecting complaint text, location, and optional contact;
- client-side validation mirroring server validation;
- loading/error states;
- rendering category, priority, AI summary, and provider after submission;
- displaying the paginated operator dashboard;
- filters for category, priority, and status;
- status transition actions;
- rendering server-provided 409 messages verbatim;
- rendering statistics and the `X-Cache` state;
- handling unexpected UI failures with an error boundary;
- calling the backend through a typed API client.

It is **not** responsible for:

- deciding category or priority;
- deciding which status transitions are legal;
- enforcing backend rate limits;
- holding secrets;
- connecting to PostgreSQL or Redis directly;
- embedding environment-specific API URLs into the build artifact.

## 2. Frontend pages

### Submit view

Inputs:

- complaint text: 10–2000 characters;
- location: 3–200 characters;
- optional reporter contact.

Submission flow:

```text
Form
  → client validation
  → POST /api/complaints
  → honest loading state
  → 201 response
  → render category + priority + summary + provider
```

### Dashboard view

```text
GET /api/complaints
  ?category=...
  &priority=...
  &status=...
  &page=...
  &page_size=...
```

The UI must use the server's pagination metadata rather than maintaining a second dataset locally. Default ordering from the backend is `created_at DESC` (newest first) — see [`backend.md`](backend.md).

Status updates:

```text
PATCH /api/complaints/{id}/status
  → backend validates transition
  → success: update UI
  → 409: display backend message verbatim
```

The frontend must not duplicate the backend's status transition table (see [`backend.md`](backend.md) §Status State Machine); it renders actions based on backend responses or backend-provided state.

### Stats view

```text
GET /api/stats
  → response body with aggregates
  → X-Cache: HIT | MISS
  → display aggregate data + cache state
```

## 3. Frontend runtime configuration

The frontend image must be environment-independent. A Vite build bakes `import.meta.env` values into static JavaScript at *build* time — if the API URL is baked in, the image becomes environment-specific and build-once-deploy-many breaks for the frontend.

**Resolved choice: nginx `/api` proxy.**

```text
Browser
  → same-origin `/api/...`
  → nginx
  → backend service
```

This allows the same static frontend image to operate in development, Compose production, and Kubernetes without rebuilding because an API hostname changed. It's preferred over the alternative permitted by the assignment (startup-generated `/config.js`) because it avoids exposing an absolute backend URL to frontend code. Recorded in `docs/adr/0002-frontend-runtime-config.md`.

Note the split between environments: in Kubernetes, the Ingress (see [`kubernetes.md`](kubernetes.md)) routes `/api` directly to the backend Service, bypassing the frontend pod's nginx for API traffic; in Docker Compose (no Ingress), the frontend's own nginx proxies `/api` to the backend container. Both paths are same-origin from the browser's perspective, which is what actually matters for this architecture.

## 4. Typed API boundary

The backend's OpenAPI schema is the source for the frontend API types/client.

```text
FastAPI routes + Pydantic models
             ↓
        OpenAPI schema
             ↓
     generated/checked client
             ↓
       React TypeScript
```

This creates a single contract instead of independently hand-maintained request/response types.

## 5. Frontend container

Build stages:

```text
node:22-alpine
    ↓ build
static assets
    ↓ copy only built assets
nginx:1.27-alpine
```

The final image must not contain:

- Node.js;
- `node_modules`;
- the TypeScript source tree;
- build tooling.

Target: approximately 60 MB or less, with actual stage sizes reported in engineering evidence.

## 6. Testing

At least 5 meaningful component tests (Vitest) are required — see [`testing.md`](testing.md) for the full coverage list (validation, loading state, triage rendering, dashboard filters/pagination, 409 rendering, stats/cache state).

## 7. Invariants checklist

- [ ] Frontend owns presentation, not domain rules.
- [ ] Submit view works.
- [ ] Honest loading state.
- [ ] Category/priority/summary/provider shown.
- [ ] Dashboard filters + pagination.
- [ ] 409 message shown verbatim.
- [ ] Stats show cache state.
- [ ] Runtime API configuration is not baked into the image.
- [ ] Typed API client tracks OpenAPI.
- [ ] Error boundary exists.
- [ ] No secrets in bundle.

