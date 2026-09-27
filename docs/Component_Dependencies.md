# CivicPulse --- Component Dependencies

## 1. Components That Can Be Worked On in Parallel

These areas have little direct dependency on each other and can be
developed at the same time.

### Backend

-   [ ] API routes and schemas
-   [ ] Database models and repositories
-   [ ] AI provider implementations
-   [ ] Redis cache and rate limiter
-   [ ] Logging and health endpoints

### Frontend

-   [ ] Submission page UI
-   [ ] Dashboard UI
-   [ ] Stats UI
-   [ ] Frontend component tests

### DevOps

-   [ ] Backend Dockerfile
-   [ ] Frontend Dockerfile
-   [ ] Docker Compose structure
-   [ ] Kubernetes manifests
-   [ ] CI workflow structure
-   [ ] Documentation

## 2. Components With Dependencies

### Frontend API Integration

**Depends on:** - Backend API contract

Frontend UI can be built independently, but API integration needs the
backend endpoints/schema.

### Backend Services

**Depends on:** - Database/repositories - AI provider interface - Redis
interfaces

The service layer combines these components.

### Complaint Creation

**Depends on:** - API route - Validation - AI triage - Database
repository - Redis rate limiter

Flow:

`Frontend → API → Rate Limiter → Validation → AI Triage → Database`

### Statistics

**Depends on:** - Database - Redis cache - Stats API endpoint

Flow:

`Database → Stats Service → Redis Cache → API → Frontend`

### Status Updates

**Depends on:** - Backend state machine - Database repository - PATCH
API

The frontend only needs the API contract to display the functionality.

### AI Fallback

**Depends on:** - TriageProvider interface - RuleBasedTriage -
Hosted/Ollama provider - Redis triage cache

Flow:

`LLM Provider → Failure → RuleBasedTriage → Database`

### Docker Compose

**Depends on:** - Backend image - Frontend image - PostgreSQL
configuration - Redis configuration - Ollama configuration

### Kubernetes Deployment

**Depends on:** - Docker images - Compose-tested application -
Kubernetes manifests - ConfigMap/Secret configuration

### HPA

**Depends on:** - Kubernetes backend Deployment - CPU resource
requests - Metrics Server

### VPA

**Depends on:** - Backend Deployment - Resource requests - Load
testing - VPA installation

### CI/CD

**Depends on:** - Tests - Dockerfiles - Kubernetes manifests - GHCR
configuration

CI tests and builds the system; CD deploys the resulting images.

## 3. Simple Dependency Picture

``` text
                    ┌──────────────┐
                    │   Frontend   │
                    └──────┬───────┘
                           │ API
                           ▼
                    ┌──────────────┐
                    │   Backend    │
                    └──────┬───────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     PostgreSQL          Redis          AI Providers
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Application Complete
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        Docker/Compose              Kubernetes
                                         │
                                         ▼
                                       HPA/VPA
                                         │
                                         ▼
                                       CI/CD
```

## 4. Practical Development Order

You do **not** need to finish one component completely before starting
the others.

1.  Define API contracts and database schema.
2.  Develop backend, frontend UI, AI providers, and Dockerfiles in
    parallel.
3.  Connect backend to PostgreSQL and Redis.
4.  Connect frontend to the backend API.
5.  Complete Docker Compose integration.
6.  Add Kubernetes deployment.
7.  Add HPA/VPA and load testing.
8.  Add CI/CD integration.
9.  Complete documentation and evidence.

## 5. Key Idea

**Can be parallel:** frontend UI, backend modules, AI providers,
database setup, Redis, Dockerfiles, Kubernetes manifests, and
documentation.

**Must eventually connect:** frontend → backend → AI/database/Redis →
Docker → Kubernetes → CI/CD.
