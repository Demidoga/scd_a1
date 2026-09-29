<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 56-74 (§2.1). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Frontend layer. Source: §2.1. Index: [INDEX.md](INDEX.md). Related: [rubric/B-frontend.md](rubric/B-frontend.md), [10-docker-compose.md](10-docker-compose.md).

# **2.1 Frontend layer** 

**Stack:** React 18 + Vite + TypeScript. Served by nginx:alpine from a **multi-stage image** — Node builds, nginx serves, and the Node toolchain never reaches the final image. 

**Responsibilities.** Present a submission form and an operations dashboard. Nothing else. The frontend owns presentation and interaction; it owns no business rules. Triage category, priority and valid status transitions are decided by the backend and rendered by the frontend, never duplicated in it — the moment your React code contains a list of valid status transitions, you have two sources of truth and one of them will rot. 

# **Required views.** 

|**View**|**Must do**|
|---|---|
|**Submit**|Free-text complaint, location, optional contact. Client-side validation that<br>_mirrors_server rules without replacing them. Show the returned category,<br>priority, AI summary, and which provider produced it. Render the loading state<br>honestly — AI calls take seconds.|
|**Dashboard**|Paginated, filterable list (category, priority, status). Operator can advance status;<br>an invalid transition must surface the server's 409 message, not a generic "error".|
|**Stats**|Aggregate counts by category and priority. Display whether the response was a<br>cache hit, from the X-Cache header. Showing your own cache behaviour in the<br>UI is unusual and is exactly the kind of thing that makes a portfolio repo<br>memorable.|



**Runtime configuration — the part most students get wrong.** A Vite build bakes import.meta.env values into static JavaScript at _build_ time. If your API URL is baked in, your image is environment-specific and you have destroyed build-once-deploy-many for the frontend. Solve it properly: serve /config.js generated at container start from environment variables, or proxy /api through nginx so the frontend never needs an absolute backend URL at all. State your choice in an ADR. 

**Required engineering.** A typed API client generated from or checked against the backend's OpenAPI schema. An error boundary. No secrets in frontend code — anything in a browser bundle is public, and "it's minified" is not a defence. 
