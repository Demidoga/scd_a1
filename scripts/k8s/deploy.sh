#!/usr/bin/env bash
# Deploy an overlay to the current cluster, by immutable image tag.
#
#   scripts/k8s/deploy.sh <dev|prod> [image-tag]
#
# The tag defaults to whatever load-images.sh last built (.k8s-image-tag). In
# CD (Milestone 9) pass the exact commit SHA that was built and scanned.
# DRY_RUN=1 renders the final manifests to stdout and exits without touching
# the cluster (no cluster needed).
#
# Order (docs/architecture/database.md §2, cicd.md §3):
#   1. delete any previous Job/migrate  (a Job's pod template is immutable, so
#      re-applying it with a new image would fail instead of re-running)
#   2. apply the overlay with the image tag substituted
#   3. wait for Job/migrate to reach Complete  — BEFORE waiting on the backend
#   4. wait for every workload's rollout
#
# The committed manifests carry the placeholder tag REPLACE_WITH_SHA. Rather
# than editing a committed file, the tag is injected through a throwaway
# kustomization in a temp directory that wraps the chosen overlay.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd kubectl python3

overlay="${1:-}"
[[ "$overlay" == "dev" || "$overlay" == "prod" ]] || die "usage: $0 <dev|prod> [image-tag]"
overlay_dir="$K8S_DIR/overlays/$overlay"

tag="${2:-}"
if [[ -z "$tag" && -f "$IMAGE_TAG_FILE" ]]; then
  tag="$(<"$IMAGE_TAG_FILE")"
fi
[[ -n "$tag" ]] || die "no image tag: pass one, or run scripts/k8s/load-images.sh first"
[[ "$tag" != "latest" ]] || die "'latest' is never a deployment target (ADR 0003) — use an immutable SHA tag"

# --- Build the throwaway kustomization that pins the tag -----------------
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Every image in the rendered overlay that still carries the placeholder tag
# gets the real one, whatever registry/name the overlay gave it.
placeholder_images="$(kubectl kustomize "$overlay_dir" \
  | grep -oE "image: *[^ ]+:${IMAGE_TAG_PLACEHOLDER}" \
  | sed -E "s/^image: *//; s/:${IMAGE_TAG_PLACEHOLDER}\$//" \
  | sort -u)"
[[ -n "$placeholder_images" ]] || die "no '${IMAGE_TAG_PLACEHOLDER}' images found in overlay '$overlay'"

# kustomize refuses absolute paths for `resources` directories, so point at the
# overlay relative to the temp directory.
overlay_rel="$(python3 -c 'import os, sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$overlay_dir" "$work")"

{
  echo "apiVersion: kustomize.config.k8s.io/v1beta1"
  echo "kind: Kustomization"
  echo "resources:"
  echo "  - $overlay_rel"
  echo "images:"
  while read -r image_name; do
    echo "  - name: $image_name"
    echo "    newTag: \"$tag\""
  done <<<"$placeholder_images"
} > "$work/kustomization.yaml"

# Fail closed: refuse to apply anything that still has a placeholder or latest.
rendered="$(kubectl kustomize "$work")"
if grep -q "$IMAGE_TAG_PLACEHOLDER" <<<"$rendered"; then die "unresolved ${IMAGE_TAG_PLACEHOLDER} in rendered manifests"; fi
if grep -qE 'image: *[^ ]+:latest' <<<"$rendered"; then die "rendered manifests reference a :latest image"; fi

# DRY_RUN=1 prints the final manifests and stops before touching the cluster.
if [[ "${DRY_RUN:-}" == "1" ]]; then
  printf '%s\n' "$rendered"
  exit 0
fi

kubectl -n "$NAMESPACE" get secret "$SECRET_NAME" >/dev/null 2>&1 \
  || die "Secret '$SECRET_NAME' not found in namespace '$NAMESPACE' — run scripts/k8s/create-secrets.sh first"

# --- Deploy ---------------------------------------------------------------
log "Deploying overlay '$overlay' at image tag '$tag'"

log "Removing any previous Job/migrate"
kubectl delete job/migrate -n "$NAMESPACE" --ignore-not-found

log "Applying manifests"
kubectl apply -k "$work"

# Equivalent to `kubectl wait --for=condition=complete job/migrate`, but also
# stops early if the Job reports Failed instead of waiting out the timeout.
log "Waiting for Job/migrate to complete"
deadline=$((SECONDS + ${MIGRATE_TIMEOUT_SECONDS:-300}))
migrated=false
while (( SECONDS < deadline )); do
  complete="$(kubectl get job/migrate -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' 2>/dev/null || true)"
  failed="$(kubectl get job/migrate -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Failed")].status}' 2>/dev/null || true)"
  if [[ "$complete" == "True" ]]; then migrated=true; break; fi
  if [[ "$failed" == "True" ]]; then break; fi
  sleep 2
done
if [[ "$migrated" != "true" ]]; then
  echo "Job/migrate did not complete. Logs:" >&2
  kubectl logs job/migrate -n "$NAMESPACE" --tail=50 >&2 || true
  die "migration failed or timed out — not waiting on the backend rollout"
fi
echo "Job/migrate: Complete"

log "Waiting for rollouts"
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/redis -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=300s

log "Deployed. Current state:"
kubectl get pods,svc,ingress,pvc,pdb -n "$NAMESPACE"
echo
echo "Next: scripts/k8s/smoke-test.sh   (app is at $INGRESS_URL)"
