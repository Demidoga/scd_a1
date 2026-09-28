<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 559-577 (§5.2). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Engineering notes: the eight questions. Source: §5.2. Index: [INDEX.md](INDEX.md). Related: [rubric/J-documentation-and-reflection.md](rubric/J-documentation-and-reflection.md).

# **5.2 Engineering notes — the eight questions** 

In docs/ENGINEERING-NOTES.md, with references to your own files and lines. Generic answers score zero. 

1. Three things that differ between your laptop and a CI runner, and the exact line in a Dockerfile or manifest that freezes each. 

2. Where your pipeline sits on the CI/CD maturity ladder (Lecture 03, slide 32). Justify the rung; name the next rung and what it buys. 

3. The exact line guaranteeing build-once-deploy-many, and what breaks without it. 

4. With a live LLM provider your service is probabilistic. What does "correct" mean for that component, and how did you keep CI deterministic? (Lecture 01, slide 34.) 

5. Your HPA lag: how many seconds between offered load rising and replicas rising? Where did the time go, and what would reduce it? 

6. Why VPA is in Off mode. Describe the failure mode of running it in Auto alongside your HPA. 

7. Your internal: true network blocks outbound traffic. Where does that leave the service that calls a hosted LLM, and how did you resolve it? 

8. **The failure.** Something cost you more than an hour. Symptoms, what you wrongly believed first, and the exact command or log line that finally told you the truth. 
