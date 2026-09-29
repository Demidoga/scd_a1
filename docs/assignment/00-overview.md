<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 1-47 (Cover table, §1.1–§1.4). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Overview: header, problem, what you build, why, definition of done. Source: Cover table, §1.1–§1.4. Index: [INDEX.md](INDEX.md). Related: [01-system-architecture.md](01-system-architecture.md), [rubric/README.md](rubric/README.md).

|**Assignment 01 - CivicPulse**||
|---|---|
|**CS4032 - Software Construction and Design**||
|**Team Size**|**2 Members**|
|**Duration**|**2 Weeks**|
|**Total Marks**|**150 Marks**|



# **1. Project description** 

# **1.1 The problem** 

Every municipality on earth runs the same broken process. A citizen reports _"burst water main flooding Street 12 since fajr, water entering ground floors"_ into a form. That free text lands in an undifferentiated queue. On a Monday the queue is four hundred items long, and the burst main sits behind three streetlight complaints, because nothing sorted them. By the time a human reads it, a street is flooded. 

The naive fix is a dropdown: make the citizen pick a category. That fails for reasons worth understanding — citizens pick wrong, pick "Other" to get through the form faster, and cannot judge urgency. The information is in the text. Somebody has to read it. 

**The engineering problem is not the reading. It is that the reader must be replaceable.** Today it is a keyword rule. Tomorrow it is a language model. Next year it is a fine-tuned classifier. The system around it must not care which — and must not fall over when the clever one is rate-limited, slow, or simply wrong. 

# **1.2 What you are building** 

**CivicPulse** — an end-to-end municipal complaint intake, triage and operations platform. 

A citizen submits a complaint through a web interface. The system validates it, **triages it with an LLM into a category, a priority and a one-line summary** , persists it durably, and surfaces it on a live operations dashboard with aggregate statistics. The whole thing runs as five cooperating containers on your laptop with one command, and as a scaled, probed, auto-scaling workload on a Kubernetes cluster in CI. 

You may rename the product. Keep the contracts in §2 — they are what gets tested. 

# **1.3 Why this system, specifically** 

Nothing here is decoration. Each piece exists because it forces a specific competency that shows up in a junior engineer's first month: 

|**Piece**|**What it forces**|
|---|---|
|A real frontend|CORS, a build step, runtime configuration, a multi-stage image,<br>an origin that is not localhost|
|An AI triage step you do<br>not control|Structured output, schema validation, timeouts, retry, fallback,<br>caching for cost, rate limiting|
|PostgreSQL<br>with<br>migrations|Persistence,<br>volumes,<br>StatefulSets,<br>readiness<br>that<br>means<br>something|
|Redis doing two jobs|Cache semantics_and_a distributed rate limiter — the same<br>infrastructure serving two purposes|
|Two Docker networks|Network segmentation: the frontend must not be able to reach the<br>database|
|Kubernetes + HPA|Declarative operations, resource budgeting, the fact that<br>autoscaling is impossible without requests|



# **1.4 What "done" means** 

A stranger clones your repository and, with one command, has the whole system running with seeded data. A second command puts it on a Kubernetes cluster. A push to main tests it, builds signed and scanned images, deploys them, and can be undone in thirty seconds. Everything a claim in your README asserts, you can demonstrate. 

That is the bar. It is the same bar as a real handover. 
