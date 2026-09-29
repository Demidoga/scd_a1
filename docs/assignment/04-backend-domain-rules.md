<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 115-121 (§2.2 (Domain rules)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Backend: domain rules (state machine, graceful shutdown, logging). Source: §2.2 (Domain rules). Index: [INDEX.md](INDEX.md). Related: [03-backend-layering-and-api.md](03-backend-layering-and-api.md), [rubric/C-backend.md](rubric/C-backend.md).

# **Domain rules** 

**Status state machine.** open → in_progress → resolved; open → rejected; in_progress → rejected. resolved and rejected are terminal. Everything else is 409. Implement it as an explicit transition table, not a chain of ifs. 

**Graceful shutdown.** Handle SIGTERM: stop accepting new requests, finish in-flight ones, close pool connections, exit. Without this, every Kubernetes rolling update drops live requests. Two dozen lines; most teams skip it and lose the marks and the rolling-update demo together. 

**Structured logging.** JSON to stdout — never to a file, because a container's filesystem is ephemeral and your log shipper reads stdout. Every log line carries a request_id propagated from an X-Request-ID header (generate one if absent). One WARNING per triage fallback with the complaint id, the provider and the error class. 
