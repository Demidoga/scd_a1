<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 489-501 (§4 H). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric H: Kubernetes (20). Source: §4 H. Index: [../INDEX.md](../INDEX.md). Related: [../11-kubernetes-manifests-and-probes.md](../11-kubernetes-manifests-and-probes.md), [../12-kubernetes-autoscaling.md](../12-kubernetes-autoscaling.md).

# **H · Kubernetes — 20** 

- Namespace, Deployments, StatefulSet + PVC for Postgres, ClusterIP Services, Ingress routing / and /api — **5** 

- ConfigMap and Secret separated; committed manifests carry placeholders only — **2** 

- All three probes correct: liveness independent of the database, readiness dependent on it — **4** 

- resources.requests and limits set on every container — **2** 

- HPA v2 with tuned behavior, plus captured kubectl get hpa -w output and a replicas-vs-load chart from a real load test — **4** 

- VPA in recommender mode, recommendations committed, requests updated in response, HPA/VPA conflict explained — **3** 
