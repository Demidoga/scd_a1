#!/usr/bin/env python3
"""Assert the Kubernetes invariants from docs/architecture/kubernetes.md §16
against rendered manifests (the output of `kubectl kustomize <dir>`).

    kubectl kustomize k8s/base         | python check_manifest_invariants.py base
    kubectl kustomize k8s/overlays/dev | python check_manifest_invariants.py overlay

Modes:
  base     the placeholder Secret must be present, with placeholder values only
  overlay  the Secret must be absent (real credentials are created out-of-band)

Needs PyYAML:  uv run --with pyyaml python check_manifest_invariants.py <mode>
Exits non-zero and lists every violation if any check fails.
"""

import sys
from collections import defaultdict

import yaml

NAMESPACE = "civicpulse"
PLACEHOLDER = "REPLACE_ME"
SECRET_HINTS = ("PASSWORD", "API_KEY", "TOKEN", "SECRET")
WORKLOAD_KINDS = ("Deployment", "StatefulSet", "Job")


def index_by_kind(docs):
    by_kind = defaultdict(dict)
    for doc in docs:
        by_kind[doc["kind"]][doc["metadata"]["name"]] = doc
    return by_kind


def pod_spec(workload):
    return workload["spec"]["template"]["spec"]


def containers(workload):
    spec = pod_spec(workload)
    return spec.get("containers", []) + spec.get("initContainers", [])


def check_namespace(docs, by_kind, errors):
    if NAMESPACE not in by_kind["Namespace"]:
        errors.append(f"Namespace '{NAMESPACE}' is missing")
    for doc in docs:
        if doc["kind"] == "Namespace":
            continue
        ns = doc["metadata"].get("namespace")
        if ns != NAMESPACE:
            errors.append(f"{doc['kind']}/{doc['metadata']['name']} is in namespace {ns!r}, not '{NAMESPACE}'")


def check_service_links(by_kind, errors):
    # Injected <SERVICE>_PORT=tcp://... env vars collide with app settings
    # (BACKEND_PORT is an int); discovery is by DNS name, so links must be off.
    for kind in WORKLOAD_KINDS:
        for name, workload in by_kind[kind].items():
            if pod_spec(workload).get("enableServiceLinks") is not False:
                errors.append(f"{kind}/{name}: enableServiceLinks must be false (service env vars collide with app settings)")


def check_images(by_kind, errors):
    for kind in WORKLOAD_KINDS:
        for name, workload in by_kind[kind].items():
            for c in containers(workload):
                image = c["image"]
                tag = image.rsplit(":", 1)[1] if ":" in image.rsplit("/", 1)[-1] else ""
                if not tag and "@sha256:" not in image:
                    errors.append(f"{kind}/{name} container '{c['name']}': image '{image}' has no tag")
                if tag == "latest":
                    errors.append(f"{kind}/{name} container '{c['name']}': image '{image}' uses :latest")


def check_resources(by_kind, errors):
    for kind in WORKLOAD_KINDS:
        for name, workload in by_kind[kind].items():
            for c in containers(workload):
                res = c.get("resources", {})
                for section in ("requests", "limits"):
                    for key in ("cpu", "memory"):
                        if key not in res.get(section, {}):
                            errors.append(f"{kind}/{name} container '{c['name']}': resources.{section}.{key} missing")


def check_services(by_kind, errors):
    services = by_kind["Service"]
    if set(services) != {"frontend", "backend", "postgres", "redis"}:
        errors.append(f"expected Services frontend/backend/postgres/redis, found {sorted(services)}")
    for name, svc in services.items():
        svc_type = svc["spec"].get("type", "ClusterIP")
        if svc_type != "ClusterIP":
            errors.append(f"Service/{name} is {svc_type}; every Service must be ClusterIP")


def check_backend(by_kind, errors):
    backend = by_kind["Deployment"].get("backend")
    if backend is None:
        errors.append("Deployment/backend is missing")
        return
    spec = backend["spec"]
    if "replicas" in spec:
        errors.append("backend Deployment must not set replicas: the HPA owns replica count")
    hpa = by_kind["HorizontalPodAutoscaler"].get("backend")
    if hpa is None:
        errors.append("HorizontalPodAutoscaler/backend is missing")
    elif hpa["spec"].get("minReplicas", 0) < 2:
        errors.append("backend HPA minReplicas must be >= 2")
    rolling = spec.get("strategy", {}).get("rollingUpdate", {})
    if rolling.get("maxSurge") != 1 or rolling.get("maxUnavailable") != 0:
        errors.append("backend rollingUpdate must be maxSurge: 1, maxUnavailable: 0")
    pod = pod_spec(backend)
    if "terminationGracePeriodSeconds" not in pod:
        errors.append("backend terminationGracePeriodSeconds is not set")
    if pod.get("initContainers"):
        errors.append("backend must not use initContainers (migrations run in Job/migrate)")
    main = pod["containers"][0]
    if "preStop" not in main.get("lifecycle", {}):
        errors.append("backend container has no preStop hook")
    expected = {"startupProbe": "/health", "livenessProbe": "/health", "readinessProbe": "/ready"}
    for probe, path in expected.items():
        actual = main.get(probe, {}).get("httpGet", {}).get("path")
        if actual != path:
            errors.append(f"backend {probe} path is {actual!r}, expected {path!r}")
    startup = main.get("startupProbe", {})
    if startup.get("failureThreshold") != 30 or startup.get("periodSeconds") != 2:
        errors.append("backend startupProbe must be failureThreshold: 30, periodSeconds: 2")


def check_data_layer(by_kind, errors):
    if "postgres" in by_kind["Deployment"]:
        errors.append("postgres must be a StatefulSet, not a Deployment")
    postgres = by_kind["StatefulSet"].get("postgres")
    if postgres is None:
        errors.append("StatefulSet/postgres is missing")
    elif not postgres["spec"].get("volumeClaimTemplates"):
        errors.append("StatefulSet/postgres has no volumeClaimTemplates (no PVC)")

    redis = by_kind["Deployment"].get("redis")
    if redis is None:
        errors.append("Deployment/redis is missing")
    else:
        if redis["spec"].get("strategy", {}).get("type") != "Recreate":
            errors.append("redis strategy must be Recreate (RWO PVC deadlocks a RollingUpdate)")
        claims = [v["persistentVolumeClaim"]["claimName"] for v in pod_spec(redis).get("volumes", []) if "persistentVolumeClaim" in v]
        if not claims:
            errors.append("redis has no PVC volume")
        for claim in claims:
            if claim not in by_kind["PersistentVolumeClaim"]:
                errors.append(f"redis references PVC '{claim}' that does not exist")


def check_frontend(by_kind, errors):
    frontend = by_kind["Deployment"].get("frontend")
    if frontend is None:
        errors.append("Deployment/frontend is missing")
    elif frontend["spec"].get("replicas", 1) < 2:
        errors.append("frontend replicas must be >= 2")


def check_migrate(by_kind, errors):
    job = by_kind["Job"].get("migrate")
    if job is None:
        errors.append("Job/migrate is missing")
        return
    command = job["spec"]["template"]["spec"]["containers"][0].get("command")
    if command != ["alembic", "upgrade", "head"]:
        errors.append(f"Job/migrate command is {command}, expected alembic upgrade head")


def check_ingress(by_kind, errors):
    ingress = next(iter(by_kind["Ingress"].values()), None)
    if ingress is None:
        errors.append("Ingress is missing")
        return
    rules = ingress["spec"].get("rules", [])
    if len(rules) != 1:
        errors.append(f"Ingress must have exactly one rule set (one host), found {len(rules)}")
        return
    routes = {p["path"]: p["backend"]["service"]["name"] for p in rules[0]["http"]["paths"]}
    if routes != {"/api": "backend", "/": "frontend"}:
        errors.append(f"Ingress routes are {routes}, expected /api->backend and /->frontend")


def check_pdb(by_kind, errors):
    pdb = by_kind["PodDisruptionBudget"].get("backend")
    if pdb is None or pdb["spec"].get("minAvailable") != 1:
        errors.append("PodDisruptionBudget/backend with minAvailable: 1 is missing")


def check_config_and_secret(by_kind, mode, errors):
    for name, cm in by_kind["ConfigMap"].items():
        for key in cm.get("data", {}):
            if any(hint in key.upper() for hint in SECRET_HINTS):
                errors.append(f"ConfigMap/{name} key '{key}' looks like a secret; it belongs in the Secret")
    secrets = by_kind["Secret"]
    if mode == "overlay":
        if secrets:
            errors.append(f"overlay output must not contain a Secret (found {sorted(secrets)}); real values are created out-of-band")
        return
    secret = secrets.get("civicpulse-secrets")
    if secret is None:
        errors.append("base is missing the placeholder Secret 'civicpulse-secrets'")
        return
    values = {**secret.get("data", {}), **secret.get("stringData", {})}
    for key, value in values.items():
        if value != PLACEHOLDER:
            errors.append(f"Secret key '{key}' is not the placeholder '{PLACEHOLDER}' — never commit real values")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("base", "overlay"):
        sys.exit(__doc__)
    mode = sys.argv[1]
    docs = [d for d in yaml.safe_load_all(sys.stdin) if d]
    by_kind = index_by_kind(docs)
    errors: list[str] = []
    check_namespace(docs, by_kind, errors)
    check_service_links(by_kind, errors)
    check_images(by_kind, errors)
    check_resources(by_kind, errors)
    check_services(by_kind, errors)
    check_backend(by_kind, errors)
    check_data_layer(by_kind, errors)
    check_frontend(by_kind, errors)
    check_migrate(by_kind, errors)
    check_ingress(by_kind, errors)
    check_pdb(by_kind, errors)
    check_config_and_secret(by_kind, mode, errors)
    if errors:
        print(f"{len(errors)} invariant violation(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    print(f"all invariants hold ({len(docs)} resources, mode={mode})")


if __name__ == "__main__":
    main()
