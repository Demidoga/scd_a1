# ADR 0002 — Frontend Runtime Configuration

## Status

Accepted. (Recorded during Milestone 1, per `docs/Milestones/milestone-1.md`
§7 — the frontend itself is built in Milestone 5, but the routing decision
has to be fixed before then so the backend/nginx/Kubernetes/CI layers that
depend on it aren't designed twice.)

## Context

The assignment requires build-once-deploy-many: the same frontend container
image must run unmodified in Compose and in every Kubernetes overlay
(dev/prod), against a backend whose network address differs per environment.
Vite, like most frontend build tools, normally bakes environment variables
into the JS bundle at *build* time (`import.meta.env.VITE_*`). If the API
base URL were one of those variables, every environment would need its own
image build — a direct violation of build-once-deploy-many, and the reason
CLAUDE.md calls this out as a cross-cutting rule.

Two options were on the table:

1. **Vite build-time env var** — bake `VITE_API_URL` into the bundle.
2. **nginx `/api` reverse proxy** — the browser always calls the same-origin
   path `/api/...`; nginx (serving the built frontend) proxies that path to
   whatever backend Service/hostname exists in that environment.
3. (Assignment-permitted alternative, not chosen) a startup-generated
   `/config.js` fetched by the SPA before rendering.

## Decision

**Use the nginx `/api` proxy (option 2).** The frontend's nginx config
(`frontend/nginx.conf`, built in Milestone 6) proxies `/api/*` to the backend
Service (`backend:8000` in Compose, the `backend` ClusterIP Service in
Kubernetes). The React app never constructs an absolute backend URL — every
API client call is a relative `/api/...` request against its own origin.

```text
Browser --same-origin /api/...--> nginx --proxy_pass--> backend Service
```

### Why this over a build-time variable

- The exact same built image (same digest) works in Compose, `overlays/dev`,
  and `overlays/prod` — routing is nginx configuration, not baked-in JS.
  This is a direct requirement of build-once-deploy-many.
- Kubernetes Ingress already routes `/` → frontend and `/api` → backend
  (`docs/Milestones/milestone-1.md` §F6) at the cluster edge; the frontend's
  own nginx layer mirrors that same path convention, so `/api` means the
  same thing whether the browser is hitting Ingress directly or the
  frontend's nginx is proxying it internally.
- No secret or environment-specific value ever needs to enter the frontend
  bundle, which is also a cross-cutting security rule (no environment
  config in frontend bundles).

### Why not the `/config.js` alternative

A startup-generated config file is a reasonable design too (and the
assignment permits it), but it adds a second moving part (something has to
generate and serve `/config.js` before the SPA boots, and the SPA has to
fetch-and-wait for it) for no benefit over an nginx proxy rule once the
answer is always the same path (`/api`) in every environment. The nginx
proxy is strictly simpler given CivicPulse never needs the frontend to talk
to more than one backend.

## Frontend/backend ownership boundary

This decision also fixes what the frontend is and isn't allowed to own
(`docs/Milestones/milestone-1.md` §E2), which downstream Milestone 5 work
must respect:

React owns presentation, interaction, client-side validation that *mirrors*
server constraints (never replaces them), loading/error states, and
rendering whatever the backend returned. React does **not** own complaint
categories/priorities, status-transition legality, AI fallback behavior, or
persistence rules — all of that is rendered from backend responses, never
recomputed client-side. The status state machine in particular
(`docs/architecture/backend.md` §4) must not be duplicated in frontend code.

## API client direction

```text
FastAPI + Pydantic → OpenAPI → typed client/checked types → React + TypeScript
```

FastAPI's generated OpenAPI document remains the single source of truth for
request/response shapes; the frontend's typed client (tool choice deferred
to Milestone 5) is generated or checked against it rather than hand-written
against assumptions.

## Consequences

- Kubernetes and Compose only need to get networking right (Service names,
  Ingress paths); no frontend rebuild is ever required to point at a
  different backend.
- Every frontend API call goes through one relative-path convention, which
  keeps the typed API client (Milestone 5) simple — one base path, no
  per-environment configuration to thread through.
- The frontend's nginx layer becomes a real dependency of the app working at
  all (not just a static file server), so its config is covered by the same
  scrutiny as backend code during Milestone 6/7 review.
