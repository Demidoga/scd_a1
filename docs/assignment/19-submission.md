<!-- Source: docs/Software Construction and Design -  Assignment 1.md, lines 655-673 (§5.8). Text below is verbatim from the source. -->
> **Assignment spec excerpt** — Submission. Source: §5.8. Index: [INDEX.md](INDEX.md).

# **5.8 Submission** 

1. GitHub repository URL — public, or private with both instructors added. 

2. Link to a successful cd.yml run that tested, published and deployed. 

3. Link to both images in GHCR, showing SHA tags. 

4. Demo video link (unlisted). 

5. git shortlog -sn output, pasted. 

6. kubectl get hpa -w capture and your replicas-vs-load chart. 

Before submitting, from the repository root: 

python scripts/check_submission.py 

It is a lint, not a grader. It catches the mechanical failures behind most of §5.3. A clean run does not guarantee a good mark; a dirty run nearly guarantees a bad one. 
