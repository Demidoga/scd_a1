<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 282-307 (§3.3 (objects, probes, rolling updates)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Kubernetes: manifests, probes, rolling updates. Source: §3.3 (objects, probes, rolling updates). Index: [INDEX.md](INDEX.md). Related: [12-kubernetes-autoscaling.md](12-kubernetes-autoscaling.md), [rubric/H-kubernetes.md](rubric/H-kubernetes.md).

# **3.3 Kubernetes** 

Local cluster: **k3d** or **kind** — both run inside Docker, both are free, both work on a student laptop. A managed cloud cluster is not required and earns no extra marks. 

**Manifests, organised with Kustomize** (base/ plus overlays/dev and overlays/prod). Helm is acceptable if you prefer it; say so in an ADR. 

|**Object**|**Requirement**|
|---|---|
|Namespace|Everything in civicpulse, never default|
|Deployment × 2|backend (≥ 2 replicas), frontend (≥ 2 replicas)|
|StatefulSet|postgres, with volumeClaimTemplates → PVC. A Deployment<br>for a database is a marked error — be ready to explain why at<br>viva.|
|Deployment + PVC|redis|
|Service × 4|ClusterIP for all. The database is never a NodePort or<br>LoadBalancer.|
|Ingress|Routes / → frontend, /api → backend, on one host|
|ConfigMap|Non-secret configuration|
|Secret|DB password, LLM API key. Manifests committed must contain<br>**placeholders only**.|
|HorizontalPodAutoscaler|On the backend — see below|
|PodDisruptionBudget|minAvailable: 1 on the backend|



# **Probes — all three, and know the difference.** 

startupProbe:    # slow start is not failure — this is what stops restart loops on boot httpGet: { path: /health, port: 8000 } failureThreshold: 30 periodSeconds: 2 livenessProbe:   # restarts the pod — must NOT depend on the database httpGet: { path: /health, port: 8000 } readinessProbe:  # removes the pod from the Service — SHOULD depend on the database httpGet: { path: /ready, port: 8000 } 

**Rolling updates.** maxSurge: 1, maxUnavailable: 0, plus terminationGracePeriodSeconds and a preStop sleep so the pod leaves the Service endpoints before it stops accepting connections. Demonstrate a zero-downtime rollout: run a load generator during a kubectl set image, and show zero failed requests. 
