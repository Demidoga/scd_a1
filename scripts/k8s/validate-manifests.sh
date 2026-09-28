#!/usr/bin/env bash
# Static validation of the Kubernetes manifests — needs no cluster and no Docker.
#
#   scripts/k8s/validate-manifests.sh
#
# For the base and each overlay: render with `kubectl kustomize`, validate the
# result against the Kubernetes API schemas with kubeconform, then run
# check_manifest_invariants.py (the docs/architecture/kubernetes.md §16
# checklist as code). CI (Milestone 9) runs this same script.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd kubectl kubeconform uv

# Schemas to validate against. Pinned so results don't drift as new
# Kubernetes versions ship.
K8S_SCHEMA_VERSION="${K8S_SCHEMA_VERSION:-1.30.0}"

validate() {
  local name="$1" dir="$2" mode="$3" rendered
  log "Validating $name"
  rendered="$(kubectl kustomize "$dir")"
  kubeconform -strict -summary -kubernetes-version "$K8S_SCHEMA_VERSION" <<<"$rendered"
  uv run --quiet --with pyyaml python "$SCRIPT_DIR/check_manifest_invariants.py" "$mode" <<<"$rendered"
}

validate "base"         "$K8S_DIR/base"            base
validate "overlay: dev"  "$K8S_DIR/overlays/dev"    overlay
validate "overlay: prod" "$K8S_DIR/overlays/prod"   overlay

log "All manifests valid"
