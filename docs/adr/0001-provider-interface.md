# ADR 0001 — TriageProvider Interface

## Status

Accepted.

## Context

CivicPulse must classify citizen complaints (category, priority, one-line
summary) as part of complaint creation. The assignment requires this to work
through at least three interchangeable implementations, selected at
deployment time, and requires the system to remain functional and testable
even when the "real" classifier (a hosted LLM) is slow, unavailable, or
returns garbage. AI output is also inherently probabilistic and cannot be
trusted as-is by the rest of the application.

## Decision

The backend depends on a single interface, not a vendor SDK:

```python
class TriageProvider(Protocol):
    name: str
    def triage(self, text: str, location: str) -> TriageResult: ...
```

Three implementations satisfy this interface (`backend/app/providers/triage/`):

- **`LLMTriage`** (`llm.py`, `TRIAGE_PROVIDER=llm`) — hosted production path via
  Groq's chat completions API. Probabilistic, requires network + API key.
- **`RuleBasedTriage`** (`rules.py`, `TRIAGE_PROVIDER=rules`) — deterministic
  keyword classifier. No network. Doubles as the mandatory fallback when
  `LLMTriage` fails (see the retry/fallback pipeline in
  `docs/architecture/ai.md` §5).
- **`SimulatedTriage`** (`simulated.py`, `TRIAGE_PROVIDER=simulated`) —
  deterministic, network-free, supports failure injection via a
  `force_failure` constructor argument. This is the CI/dev default.

`backend/app/providers/triage/factory.py` reads `TRIAGE_PROVIDER` and
constructs the matching implementation; `app/services/triage.py` (the only
caller) depends on the `TriageProvider` protocol, never on a concrete class.

**What `TriageResult` guarantees:** every provider call — regardless of
implementation — is validated against one Pydantic model before the result
is trusted:

```python
class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)
```

This is the hard boundary between "whatever a provider returned" and "data
the rest of the application is allowed to act on." A provider that returns
malformed JSON, an out-of-enum category, an oversized summary, or an
out-of-range confidence never reaches persistence — it's treated the same
as any other provider failure and routed to the fallback (see ADR-adjacent
detail in `docs/architecture/ai.md` §5).

**Why provider selection is configuration-driven, not request-driven:**
`TRIAGE_PROVIDER` is deployment configuration (an environment variable), not
a client-supplied field on `POST /api/complaints`. This keeps the active
provider a single, auditable, process-wide decision — CI is always
`simulated`, a citizen can never force a specific classifier by request, and
switching providers is a deploy-time change, not an application code change.

## Scope reduction: no Ollama

The assignment's own framing lists four provider slots including
`OllamaTriage`. The instructor confirmed teams may implement a single live
triage path — hosted (Groq) *or* local (Ollama) — rather than both. This
project selects the hosted Groq path exclusively; there is no `OllamaTriage`,
no `ollama` container, no `ollama_models` volume. Full reasoning:
`docs/architecture/ai.md` §0. Three implementations still satisfies the
rubric's "≥ 3 implementations" requirement.

## Consequences

- Adding a fourth provider (e.g. a different hosted vendor) means writing one
  new class and one new `factory.py` branch — no changes to `services/`,
  `routes/`, or the persistence schema.
- Every provider, including future ones, inherits the same timeout/retry/
  fallback/cache orchestration for free, because that orchestration lives in
  `TriageService` and operates on the interface, not the implementation
  (see `app/services/triage.py`).
- Tests can inject arbitrary failure modes (`SimulatedTriage(force_failure=...)`)
  without mocking network calls, which is what makes the mandatory
  "provider always raises → still 201, `triaged_by == rules:fallback`" test
  deterministic and fast.
