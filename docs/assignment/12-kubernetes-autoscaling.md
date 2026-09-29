<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 309-341 (§3.3 (HPA, VPA)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Kubernetes: HPA and VPA. Source: §3.3 (HPA, VPA). Index: [INDEX.md](INDEX.md). Related: [11-kubernetes-manifests-and-probes.md](11-kubernetes-manifests-and-probes.md), [rubric/H-kubernetes.md](rubric/H-kubernetes.md).

# **Horizontal scaling — HPA** 

apiVersion: autoscaling/v2 kind: HorizontalPodAutoscaler 

spec: minReplicas: 2 maxReplicas: 10 metrics: - type: Resource resource: { name: cpu, target: { type: Utilization, averageUtilization: 60 } } behavior: scaleDown: stabilizationWindowSeconds: 300   # scale down slowly — flapping is expensive scaleUp: stabilizationWindowSeconds: 0     # scale up immediately — users are waiting 

**Requests are mandatory.** The HPA computes utilisation as _usage ÷ request_ . With no resources.requests.cpu on your pods there is no denominator, and the HPA sits at <unknown>/60% forever. Every semester, several teams debug a "broken HPA" that is in fact a missing three-line block. 

**Deliverable:** install metrics-server, then generate load with k6 or hey and **capture the scale-out** . Submit kubectl get hpa -w output showing replicas rising, a chart of replicas against offered load over time, and 3–5 sentences on the lag between load arriving and capacity arriving. That lag is the reason autoscaling is not a substitute for capacity planning, and noticing it yourself is the learning outcome. 

# **Vertical scaling — VPA** 

Install the Vertical Pod Autoscaler and run it on the backend in **recommender mode** (updateMode: "Off"). 

spec: 

updatePolicy: { updateMode: "Off" }   # recommend only — do not evict 

Then do the loop that matters: 

1. Record the requests you guessed when you wrote the manifest. 

2. Run your load test. 

3. kubectl describe vpa backend-vpa → commit the Target, Lower Bound and Upper Bound recommendations. 

4. Update your requests to match the recommendation. 

5. Re-run the load test and report what changed about HPA behaviour. 

**Say explicitly in your notes why VPA runs in Off mode here.** HPA scaling on CPU and VPA in Auto mode adjusting CPU requests act on the same signal and fight: VPA raises the request, which lowers computed utilisation, which makes HPA scale in, which raises per-pod load, which makes VPA raise the request again. Recommender mode plus a human decision is the current 

industrial practice for exactly this reason. A team that explains this conflict clearly has understood autoscaling better than one that got a number to move. 
