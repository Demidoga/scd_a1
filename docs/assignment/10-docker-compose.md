<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 246-280 (§3.2). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — DevOps: Docker Compose networks and volumes. Source: §3.2. Index: [INDEX.md](INDEX.md). Related: [rubric/G-docker-and-compose.md](rubric/G-docker-and-compose.md).

# **3.2 Docker Compose — networks and volumes** 

Compose is where you demonstrate **network segmentation** and **explicit persistence** . Both are marked. 

# **Networks — two, not one.** 

networks: 

edge:            # frontend ↔ backend driver: bridge 

internal:        # backend ↔ database ↔ cache 

driver: bridge internal: true      # no route to the outside world 

- frontend joins edge only. 

- backend joins **both** — it is the only service that bridges them. 

- database and cache join internal only. 

The consequence is the point: docker compose exec frontend ping database **must fail** . The frontend is the internet-facing component and therefore the most likely to be compromised; it has no route to your data. Demonstrate this failure in your video — a failing command as evidence of correct design is a genuinely satisfying thing to show. 

Note the trade-off you have created: internal: true means those containers cannot reach the internet, so an LLMTriage provider calling Groq must live on a service that can. Work out where that leaves your architecture and write the answer in your notes. There is more than one defensible design. 

# **Volumes — three, each justified.** 

volumes: 

pgdata:        # PostgreSQL data directory — the durable one redisdata:     # AOF persistence — justify this one in your notes ollama_models: # model weights, so you do not re-pull 800 MB on every up 

Plus a **bind mount for development only** , mounting your source into the backend for hot reload — and a sentence on why that is right in compose.yaml and wrong in compose.prod.yaml. 

**Required Compose engineering:** healthchecks on every service; depends_on: condition: service_healthy; all credentials via ${...} from .env; .env.example committed; .env gitignored; every image tag pinned; restart: unless-stopped; resource limits under deploy.resources; no published port on database or cache in the production file. 

Two files: compose.yaml (dev, build:) and compose.prod.yaml (deploy, image: with ${IMAGE_TAG}, no build: key anywhere). 
