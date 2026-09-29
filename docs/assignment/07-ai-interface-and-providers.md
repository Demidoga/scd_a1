<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 167-206 (§2.5 (The interface, Recommended free endpoints)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — AI layer: interface, providers, free endpoints. Source: §2.5 (The interface, Recommended free endpoints). Index: [INDEX.md](INDEX.md). Related: [08-ai-reliability-and-testing.md](08-ai-reliability-and-testing.md), [rubric/F-ai-layer.md](rubric/F-ai-layer.md).

# **2.5 AI layer — the core of the system** 

# **The interface** 

class TriageResult(BaseModel): 

category: Category 

priority: Priority 

summary: str = Field(max_length=140) confidence: float = Field(ge=0.0, le=1.0) 

class TriageProvider(Protocol): 

name: str 

def triage(self, text: str, location: str) -> TriageResult: ... 

Four implementations, selected by TRIAGE_PROVIDER: 

|**Provider**|**Use**|
|---|---|
|LLMTriage|Production path. Calls a free-tier hosted model.|
|OllamaTriage|Fully offline path, a container in your Compose stack. Same interface.|
|RuleBasedTriage|Deterministic keyword fallback. Always available, never fails.|
|SimulatedTriage|Deterministic fake for CI — seeded, no network, configurable failure<br>injection.|



# **Recommended free endpoints** 

All three are permanent free tiers with **no credit card** , verified September 2026. Limits change — check the provider's live limits page and cite what you actually saw in your notes. 

**Groq — recommended primary.** OpenAI-compatible endpoint, so the official openai SDK works by changing base_url. Sign up at console.groq.com with an email. <cite index="3-1">A genuinely free, no-credit-card developer tier with access to every model, gated only by rate limits, with no credits system and no per-token charge.</cite> <cite index="4-1">Rate limits apply at the organization level, not individual users, and also apply per model.</cite> Inference is extremely fast, which matters when a citizen is watching a spinner. Use a small instruct model — you are classifying a paragraph, not writing an essay. 

**Google AI Studio (Gemini) — recommended alternative.** <cite index="10-1">A free Gemini API tier on Flash and Flash-Lite models with no credit card and no Google Cloud billing, suitable for prototyping and low-volume use.</cite> Generous daily allowance and native structured-output support. One caveat you must handle as an engineering decision, not ignore: <cite index="10-1">on the free tier, Google may use your inputs to improve its models.</cite> Citizen complaints contain names, addresses and phone numbers. **Write the resulting PII decision into an ADR** — redact before sending, send only the complaint body, or accept and document the exposure. This is CLO 8 arriving in its natural habitat, and a thoughtful ADR here is worth more in an interview than the entire rest of the repository. 

**Ollama — the zero-dependency path.** A container in your Compose file running a 1B-parameter model. No key, no network, no rate limit, no PII leaving your machine. Slower on CPU and noticeably worse at classification, which is itself the lesson: the buy-versus-host trade-off from CLO 4, measured by you rather than asserted by a slide. If free-tier keys become a problem for anyone in your team, take this path — you lose no marks for it. 

Other workable options: OpenRouter's free model tier, Cloudflare Workers AI, Hugging Face Inference. Any provider is acceptable if it is free and you document it. 
