<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 449-457 (§4 E). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Rubric E: Cache layer (10). Source: §4 E. Index: [../INDEX.md](../INDEX.md). Related: [../06-cache-layer.md](../06-cache-layer.md).

# **E · Cache layer — 10** 

- /api/stats read-through cache, 30 s TTL, correct X-Cache header — **3** 

- Cache invalidated on write, not left to expire — **2** 

- Distributed Redis rate limiter on POST /api/complaints, 429 with Retry-After — **4** 

- Redis AOF on a named volume, with your justification written down — **1** 
