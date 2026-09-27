# Development Dependency / Milestone Flow

> Part of the CivicPulse architecture. Root index: [`docs/architecture.md`](../architecture.md).
>
> This is the architecture's compressed view of build order. `docs/Milestones.md` covers the same ground in more detail (per-milestone task lists) — treat that as the working checklist and this as the dependency summary.

The project should be built in dependency order rather than trying to implement the entire stack at once.

```text
M1 Foundation & Contracts
   ↓
M2 Database & Backend Core
   ↓
M3 AI + Redis
   ↓
M4 Complete Backend API + Tests
   ↓
M5 Frontend
   ↓
M6 Docker + Compose
   ↓
M7 Kubernetes Baseline
   ↓
M8 HPA/VPA + Operational Testing
   ↓
M9 CI/CD + Security Gates
   ↓
M10 Documentation + Evidence + Hardening
```

## Parallelizable work

After contracts are stable, multiple areas can progress in parallel: frontend presentation components; backend repositories/services; AI providers; Redis implementation; Dockerfiles; Kubernetes manifest scaffolding; documentation skeletons.

## Hard dependencies

```text
API/data contracts
     ↓
backend core
     ↓
AI + Redis integration
     ↓
complete API
     ↓
frontend integration
     ↓
Compose integration
     ↓
Kubernetes
     ↓
HPA/VPA validation
     ↓
CI/CD automation
     ↓
evidence/documentation
```

This does not mean every file must be developed strictly sequentially. It means integration gates should be satisfied in this order.
