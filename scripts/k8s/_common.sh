#!/usr/bin/env bash
# Shared settings and helpers for the scripts in this directory.
# Source it (`source "$(dirname "$0")/_common.sh"`); don't execute it.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
K8S_DIR="$REPO_ROOT/k8s"

CLUSTER_NAME="${CLUSTER_NAME:-civicpulse}"
NAMESPACE="civicpulse"
SECRET_NAME="civicpulse-secrets"

# Where the k3d load balancer is published on the host (see create-cluster.sh).
INGRESS_URL="${INGRESS_URL:-http://localhost:8080}"

# Remembers the tag load-images.sh last built, so deploy.sh can default to it.
# Git-ignored — it is a local convenience, not project state.
IMAGE_TAG_FILE="$REPO_ROOT/.k8s-image-tag"

# Placeholder tag used in the committed manifests; deploy.sh replaces it.
IMAGE_TAG_PLACEHOLDER="REPLACE_WITH_SHA"

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# require_cmd docker k3d ... — abort with an install hint if a tool is missing.
require_cmd() {
  local missing=0 cmd
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      printf 'ERROR: required command not found: %s\n' "$cmd" >&2
      missing=1
    fi
  done
  [[ $missing -eq 0 ]] || die "install the missing tool(s) above (see README 'Kubernetes' section)"
}

# Immutable-ish image tag for local builds: the short git SHA. If the working
# tree has uncommitted changes the same SHA would describe different content,
# so a UTC timestamp is appended to keep every build's tag unique.
image_tag() {
  local sha
  sha="$(git -C "$REPO_ROOT" rev-parse --short=12 HEAD)"
  if [[ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    printf '%s-dirty-%s' "$sha" "$(date -u +%Y%m%d%H%M%S)"
  else
    printf '%s' "$sha"
  fi
}
