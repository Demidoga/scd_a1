#!/usr/bin/env bash
# OPTIONAL: pull the third-party images (postgres, redis) with your host
# Docker and load them into the k3d cluster.
#
# Use this only if `kubectl get pods -n civicpulse` shows postgres-0 or redis
# stuck in ImagePullBackOff. Some setups (seen on Docker Desktop) let the host
# Docker reach Docker Hub while the cluster's own DNS/egress can't
# ("lookup auth.docker.io: Try again"), so the cluster can't pull by itself.
#
# Only the image variant for your machine's architecture is exported: Docker
# Desktop's containerd image store otherwise exports an incomplete multi-arch
# image and `k3d image import` fails with "content digest ... not found".
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd docker k3d

# Keep in sync with the image tags in k8s/base/postgres.yaml and redis.yaml.
IMAGES=(postgres:16-alpine redis:7-alpine)
arch="$(docker version --format '{{.Server.Arch}}')"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

for image in "${IMAGES[@]}"; do
  log "Pulling $image (linux/$arch)"
  docker pull --platform "linux/$arch" "$image"
  docker save --platform "linux/$arch" "$image" -o "$work/${image//[:\/]/_}.tar"
done

log "Loading into k3d cluster '$CLUSTER_NAME'"
for tarball in "$work"/*.tar; do
  k3d image import "$tarball" --cluster "$CLUSTER_NAME"
done

echo
echo "Done. Pods stuck in back-off retry on their own; to skip the wait:"
echo "  kubectl delete pod postgres-0 -n $NAMESPACE"
echo "  kubectl delete pod -n $NAMESPACE -l app.kubernetes.io/name=redis"
