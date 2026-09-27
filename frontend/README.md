# CivicPulse frontend

React 18 + Vite + TypeScript, styled with Tailwind CSS. Milestone 5 of the
CivicPulse assignment — see `../docs/architecture/frontend.md` for the
architecture (runtime configuration, typed API boundary, container build)
and `../docs/Milestones.md` (Milestone 5) for the task checklist.

## Quickstart

Requires the backend running locally (`../backend`, see its README) — the
dev server proxies `/api/*` to `http://localhost:8000`, the same
same-origin shape used by the nginx proxy in Compose/Kubernetes
(`docs/architecture/frontend.md` §3).

```bash
npm install
npm run dev        # http://localhost:5173, proxies /api -> :8000
```

## Commands

```bash
npm run build          # tsc -b && vite build -> dist/
npm run lint           # oxlint
npm run test           # vitest run
npm run test:coverage  # vitest run --coverage
```

## Structure

```text
src/
  api/          typed client + request/response types mirroring the backend contract
  components/   presentational, reusable pieces (badges, filters, pagination, error boundary)
  pages/        SubmitPage, DashboardPage, StatsPage
tests/          Vitest + Testing Library component tests
```

The frontend never encodes the backend's status transition table or
category/priority classification — see `../docs/architecture/backend.md` §4.
It renders based on backend responses only, including 409 conflict messages
shown verbatim.
