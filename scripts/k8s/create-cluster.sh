#!/usr/bin/env bash
# Create (or reuse) the local k3d cluster.
#
# k3d runs a small Kubernetes cluster (k3s) inside Docker containers. It ships
# with Traefik (the Ingress controller), a default StorageClass (`local-path`,
# used by our PersistentVolumeClaims) and metrics-server, so nothing extra has
# to be installed for Milestone 7.
#
# `--port 8080:80@loadbalancer` publishes the cluster's Ingress on
# http://localhost:8080 so you (and the smoke test) can reach it directly.
# docs/architecture/kubernetes.md §6.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd docker k3d kubectl

if k3d cluster list "$CLUSTER_NAME" >/dev/null 2>&1; then
  log "k3d cluster '$CLUSTER_NAME' already exists — reusing it"
else
  log "Creating k3d cluster '$CLUSTER_NAME'"
  k3d cluster create "$CLUSTER_NAME" --port "8080:80@loadbalancer" --agents 0 --wait
fi

kubectl config use-context "k3d-$CLUSTER_NAME" >/dev/null

log "Cluster is up"
kubectl get nodes
echo
kubectl get storageclass
echo
kubectl get ingressclass
