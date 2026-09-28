<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 155-165 (§2.4). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Cache layer (Redis: stats cache + rate limiter). Source: §2.4. Index: [INDEX.md](INDEX.md). Related: [rubric/E-cache-layer.md](rubric/E-cache-layer.md).

# **2.4 Cache layer** 

Redis 7 does **two different jobs** , deliberately, so you learn that infrastructure is a capability and not a single-purpose box. 

**Job 1 — read-through cache for /api/stats.** TTL 30 s. X-Cache: HIT|MISS. Invalidate on write, so a newly submitted complaint appears in the stats immediately rather than up to 30 seconds later. Be able to explain at viva why TTL _and_ explicit invalidation, when either alone seems sufficient. 

**Job 2 — distributed rate limiter.** A fixed-window or token-bucket counter in Redis, keyed by client IP, protecting POST /api/complaints. Exceeded → 429 with a Retry-After header. 

Job 2 is not busywork. Your free LLM tier permits on the order of tens of requests per minute; one bored user with a for loop exhausts your entire day's quota. This is Lecture 01's "cost & latency" dimension arriving as a concrete defensive requirement — and it must be _distributed_ , in Redis, not an in-process dictionary, because the moment the HPA scales you to four pods an in-process limiter permits four times the traffic. Understanding that sentence is worth more than the marks attached to it. 

**Persistence.** Enable AOF on a named volume. Then answer, in your notes: _why does the cache need a volume when the whole point of a cache is that it can be rebuilt?_ There is a defensible answer either way. Give yours. 
