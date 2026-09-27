"""Prometheus metrics registry. docs/architecture/backend.md §6."""

from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

TRIAGE_LATENCY = Histogram(
    "triage_duration_seconds",
    "Triage pipeline latency",
    ["provider"],
)

TRIAGE_FALLBACK_COUNT = Counter(
    "triage_fallback_total",
    "Number of complaints triaged via the rules:fallback path",
)

TRIAGE_CACHE_HITS = Counter(
    "triage_cache_hits_total",
    "Content-hash triage cache hits — hit rate = hits / (hits + misses)",
)

TRIAGE_CACHE_MISSES = Counter(
    "triage_cache_misses_total",
    "Content-hash triage cache misses",
)
