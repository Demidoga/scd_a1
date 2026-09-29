#!/usr/bin/env bash
# Build the backend and frontend images locally and load them into the k3d
# cluster (a local cluster can't pull images that only exist on your machine).
#
# Images are tagged with the git SHA (plus a timestamp if the tree is dirty),
# never `latest` — see docs/adr/0003-deploy-by-sha.md. The tag is saved to
# .k8s-image-tag so `deploy.sh` can pick it up.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd docker k3d git

tag="$(image_tag)"

log "Building images tagged '$tag'"
docker build -t "civicpulse-backend:$tag" "$REPO_ROOT/backend"
docker build -t "civicpulse-frontend:$tag" "$REPO_ROOT/frontend"

log "Loading images into k3d cluster '$CLUSTER_NAME'"
k3d image import "civicpulse-backend:$tag" "civicpulse-frontend:$tag" --cluster "$CLUSTER_NAME"

printf '%s\n' "$tag" > "$IMAGE_TAG_FILE"
log "Done. Image tag: $tag (saved to .k8s-image-tag)"
