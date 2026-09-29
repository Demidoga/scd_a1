#!/usr/bin/env bash
# Prove PostgreSQL data survives deletion of the database pod.
#
# Creates a complaint, deletes pod postgres-0, waits for the StatefulSet to
# recreate it, and confirms the same complaint is still there. It works
# because the StatefulSet's volumeClaimTemplates PVC outlives the pod.
# docs/architecture/database.md §5.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd curl kubectl

pod_uid() { kubectl get pod/postgres-0 -n "$NAMESPACE" -o jsonpath='{.metadata.uid}'; }

log "Creating a complaint through the Ingress"
response="$(curl -sS -X POST "$INGRESS_URL/api/complaints" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Persistence check: drain overflowing onto the road near the market","location":"Anarkali Bazaar, Lahore"}' \
  -w '\n%{http_code}')"
code="${response##*$'\n'}"
[[ "$code" == "201" ]] || die "POST /api/complaints returned $code: ${response%$'\n'*}"
id="$(grep -oE '"id" *: *"[0-9a-f-]{36}"' <<<"$response" | head -n 1 | grep -oE '[0-9a-f-]{36}')"
[[ -n "$id" ]] || die "could not read complaint id from response"
echo "Created complaint $id"

old_uid="$(pod_uid)"
log "Deleting pod postgres-0 (uid $old_uid)"
kubectl delete pod/postgres-0 -n "$NAMESPACE"

log "Waiting for the StatefulSet to recreate it"
until kubectl get pod/postgres-0 -n "$NAMESPACE" >/dev/null 2>&1; do sleep 1; done
kubectl wait --for=condition=ready pod/postgres-0 -n "$NAMESPACE" --timeout=180s
new_uid="$(pod_uid)"
[[ "$old_uid" != "$new_uid" ]] || die "pod was not replaced (same uid) — nothing was proven"
echo "New pod uid: $new_uid"

log "Fetching the complaint again (retrying while the backend reconnects)"
for attempt in $(seq 1 30); do
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$INGRESS_URL/api/complaints/$id" || true)"
  if [[ "$code" == "200" ]]; then
    log "PASS: complaint $id survived the deletion of postgres-0"
    exit 0
  fi
  echo "  attempt $attempt: HTTP $code"
  sleep 2
done
die "complaint $id not retrievable after the database pod was recreated"
