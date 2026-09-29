#!/usr/bin/env bash
# Create/update the real Kubernetes Secret from your local, git-ignored .env.
#
# The committed k8s/base/secret.yaml holds placeholders only, and both
# overlays remove it, so this script (locally) or the CD workflow (in CI, from
# GitHub Secrets) is the only thing that ever puts real values in the cluster.
# Values are passed through a process substitution (not command-line
# arguments) so they never show up in `ps` output or shell history, and are
# never printed.
#
# Reads from .env:   POSTGRES_PASSWORD  (required)
#                    LLM_API_KEY        (optional — without it triage falls back to rules)
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"

require_cmd kubectl

ENV_FILE="${ENV_FILE:-$REPO_ROOT/.env}"
[[ -f "$ENV_FILE" ]] || die "$ENV_FILE not found — copy .env.example to .env and fill it in"

# Read NAME=value from the env file without `source`-ing it (no code execution,
# last assignment wins, surrounding quotes stripped).
read_env() {
  local value
  value="$(grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
  value="${value%\"}"; value="${value#\"}"
  value="${value%\'}"; value="${value#\'}"
  printf '%s' "$value"
}

postgres_password="$(read_env POSTGRES_PASSWORD)"
llm_api_key="$(read_env LLM_API_KEY)"

[[ -n "$postgres_password" ]] || die "POSTGRES_PASSWORD is empty in $ENV_FILE"

# The password is interpolated into DATABASE_URL (a URL), so characters with
# special meaning in URLs would break the connection string.
if [[ "$postgres_password" =~ [^A-Za-z0-9._~-] ]]; then
  die "POSTGRES_PASSWORD contains URL-special characters; use only letters, digits and . _ ~ - (it is embedded in DATABASE_URL)"
fi

log "Ensuring namespace '$NAMESPACE' exists"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

log "Creating/updating Secret '$SECRET_NAME' (values not shown)"
# A real temp file, not process substitution: on Windows, kubectl is a native
# binary and can't read the /proc/self/fd/N path Git Bash's <(...) produces.
env_tmp="$(mktemp)"
trap 'rm -f "$env_tmp"' EXIT
printf 'POSTGRES_PASSWORD=%s\nLLM_API_KEY=%s\n' "$postgres_password" "$llm_api_key" >"$env_tmp"
kubectl create secret generic "$SECRET_NAME" \
  --namespace "$NAMESPACE" \
  --from-env-file="$env_tmp" \
  --dry-run=client -o yaml | kubectl apply -f -
rm -f "$env_tmp"

if [[ -z "$llm_api_key" ]]; then
  echo "Note: LLM_API_KEY is empty — triage will use the rule-based fallback until you set it."
fi
echo
echo "Pods read Secrets at start-up. If the backend/postgres pods are already"
echo "running and you changed a value, restart them: kubectl rollout restart deployment/backend -n $NAMESPACE"
