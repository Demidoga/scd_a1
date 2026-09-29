#!/usr/bin/env bash
# Smoke test through the Ingress — the same path a browser takes.
#
#   scripts/k8s/smoke-test.sh            # against http://localhost:8080
#   INGRESS_URL=http://host:port scripts/k8s/smoke-test.sh
#
# Note the backend's /health and /ready are NOT routed through the Ingress
# (only /api is), so `/api/stats` is the backend probe here: it touches both
# PostgreSQL and Redis, so a 200 proves the whole chain works.
# docs/architecture/kubernetes.md §6.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd curl

fail() { printf '  FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf '  ok:   %s\n' "$*"; }

# request METHOD PATH [JSON_BODY] -> sets $status, $content_type, $body
request() {
  local method="$1" path="$2" data="${3:-}" out
  local args=(-sS -X "$method" -o - -w '\n%{http_code} %{content_type}' "$INGRESS_URL$path")
  [[ -n "$data" ]] && args+=(-H 'Content-Type: application/json' -d "$data")
  out="$(curl "${args[@]}")"
  local trailer="${out##*$'\n'}"
  body="${out%$'\n'*}"
  status="${trailer%% *}"
  content_type="${trailer#* }"
}

log "Frontend through Ingress ($INGRESS_URL/)"
request GET /
[[ "$status" == "200" ]] || fail "GET / returned $status"
grep -q 'id="root"' <<<"$body" || fail "GET / did not return the React app shell"
pass "GET / -> 200, React app shell"

log "Backend through Ingress (/api)"
request GET /api/stats
[[ "$status" == "200" ]] || fail "GET /api/stats returned $status"
[[ "$content_type" == application/json* ]] || fail "GET /api/stats returned '$content_type' (Ingress routing /api to the frontend?)"
pass "GET /api/stats -> 200 JSON (PostgreSQL + Redis reachable)"

request GET /api/meta/providers
[[ "$status" == "200" ]] || fail "GET /api/meta/providers returned $status"
pass "GET /api/meta/providers -> 200"

log "Complaint round trip"
request POST /api/complaints '{"text":"Smoke test: street light outside the school has been broken for a week","location":"Main Boulevard, Gulberg"}'
[[ "$status" == "201" ]] || fail "POST /api/complaints returned $status: $body"
id="$(grep -oE '"id" *: *"[0-9a-f-]{36}"' <<<"$body" | head -n 1 | grep -oE '[0-9a-f-]{36}')"
[[ -n "$id" ]] || fail "could not read complaint id from response: $body"
pass "POST /api/complaints -> 201 (id $id)"

request GET "/api/complaints/$id"
[[ "$status" == "200" ]] || fail "GET /api/complaints/$id returned $status"
pass "GET /api/complaints/$id -> 200"

log "Smoke test passed"
