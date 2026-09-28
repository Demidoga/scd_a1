<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 49-55 (§2 heading + architecture diagram (OCR text)). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — System architecture diagram (§2 intro). Source: §2 heading + architecture diagram (OCR text). Index: [INDEX.md](INDEX.md). Related: [02-frontend.md](02-frontend.md), [03-backend-layering-and-api.md](03-backend-layering-and-api.md), [06-cache-layer.md](06-cache-layer.md), [07-ai-interface-and-providers.md](07-ai-interface-and-providers.md).

# **2. System architecture** 



<!-- Start of picture text -->
Citizen / Operator<br>|<br>HTTP<br>frontend : React + Vite ><br>nginx<br>multi-stage image<br>backend : FastAPI +<br>Pydantic<br>i ~<br>postgres:16 - volume redis:7 - cache + rate TriageProvider (interface)<br>pgdata limiter 7 —<br>/o NN<br>/ \<br>default cl<br>Groq or Gemini: free tier - SimulatedTriage -<br>JSON mode deterministic fake<br>timeout - 429: bad JSON<br>M<br>RuleBasedTriage:fallback<br><!-- End of picture text -->
