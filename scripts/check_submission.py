#!/usr/bin/env python3
"""Pre-submission lint. Run from the repository root:

    python scripts/check_submission.py

A lint, not a grader (docs/assignment/19-submission.md): it catches the
mechanical failures behind the automatic deductions in
docs/assignment/16-automatic-deductions.md. Exit code 1 if any FAIL, else 0.
WARN means "a human should look"; it does not fail the run. Standard library
only, so it runs anywhere Python 3.9+ and git are installed.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
results: list[tuple[str, str, str]] = []  # (status, check, detail)


def record(status: str, check: str, detail: str = "") -> None:
    results.append((status, check, detail))


def ok(check: str, detail: str = "") -> None:
    record("PASS", check, detail)


def fail(check: str, detail: str) -> None:
    record("FAIL", check, detail)


def warn(check: str, detail: str) -> None:
    record("WARN", check, detail)


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def files(pattern: str) -> list[Path]:
    return sorted(p for p in ROOT.glob(pattern) if p.is_file())


# --------------------------------------------------------------------- git


def check_secrets_in_history() -> None:
    name = "No .env / key file anywhere in git history (-20)"
    added = git("log", "--all", "--diff-filter=A", "--name-only", "--format=").splitlines()
    bad = sorted(
        {
            f
            for f in added
            if re.search(r"(^|/)\.env($|\.(?!example$))", f)
            or re.search(r"\.(pem|key|p12)$|(^|/)id_rsa", f)
        }
    )
    if bad:
        fail(name, "committed at some point: " + ", ".join(bad))
        return
    patterns = r"gsk_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|ghp_[A-Za-z0-9]{30,}"
    hits = re.findall(patterns, git("log", "--all", "-p", "--format="))
    if hits:
        fail(name, f"{len(hits)} secret-looking string(s) in history (e.g. {hits[0][:8]}...)")
        return
    ok(name)


def check_main_history() -> None:
    name = "No direct commits to main (-5)"
    lines = git("log", "main", "--first-parent", "--no-merges", "--format=%h %s").splitlines()
    if len(lines) > 1:  # the very first commit cannot come from a PR
        warn(
            name,
            f"{len(lines) - 1} non-merge commit(s) sit directly on main's first-parent line; "
            "history can't be rewritten, so use branch + PR from now on",
        )
    else:
        ok(name)


def check_collaboration() -> None:
    total = int(git("rev-list", "--count", "HEAD").strip() or 0)
    if total >= 35:
        ok(">= 35 commits", f"{total}")
    else:
        warn(">= 35 commits", f"only {total} on HEAD")
    shortlog = [ln.split("\t") for ln in git("shortlog", "-sn", "HEAD").splitlines() if ln.strip()]
    if len(shortlog) < 2:
        warn("Both partners contribute", "shortlog shows a single author")
        return
    low = [(n.strip(), int(c)) for c, n in shortlog if total and int(c) / total < 0.35]
    if low:
        warn("Neither partner below 35% (git shortlog -sn)", ", ".join(f"{n}={c}/{total}" for n, c in low))
    else:
        ok("Neither partner below 35% (git shortlog -sn)")


# ------------------------------------------------------------ manifests etc.


def check_pinned_images() -> None:
    name = "Base images pinned to a tag, never latest (-8)"
    problems = []
    for df in files("**/Dockerfile"):
        if "node_modules" in df.parts:
            continue
        stages: set[str] = set()
        for line in read(df).splitlines():
            m = re.match(r"\s*FROM\s+(\S+)(?:\s+AS\s+(\S+))?", line, re.I)
            if not m:
                continue
            image, alias = m.group(1), m.group(2)
            if image in stages:  # FROM <earlier stage>
                continue
            if alias:
                stages.add(alias)
            if ":" not in image or image.endswith(":latest"):
                problems.append(f"{df.relative_to(ROOT)}: {image}")
    yaml_files = [ROOT / "compose.yaml", ROOT / "compose.prod.yaml", *files("k8s/**/*.yaml")]
    for yf in yaml_files:
        for line in read(yf).splitlines():
            m = re.match(r"\s*-?\s*image:\s*(\S+)", line)
            if not m or m.group(1).startswith('"${') or m.group(1).startswith("${"):
                continue
            image = m.group(1).strip("\"'")
            if ":" not in image or image.endswith(":latest"):
                problems.append(f"{yf.relative_to(ROOT)}: {image}")
    ok(name) if not problems else fail(name, "; ".join(problems))


def check_no_latest_deploy() -> None:
    name = "Never deploy :latest (-8)"
    problems = []
    for yf in [ROOT / "compose.prod.yaml", *files("k8s/**/*.yaml")]:
        if re.search(r"image:\s*\S+:latest\b", read(yf)):
            problems.append(str(yf.relative_to(ROOT)))
    cd = read(ROOT / ".github/workflows/cd.yml")
    if re.search(r"deploy\.sh\s+\S+\s+\S*latest", cd):
        problems.append("cd.yml deploys latest")
    if "github.sha" not in cd:
        problems.append("cd.yml never references github.sha")
    ok(name) if not problems else fail(name, "; ".join(problems))


def check_localhost() -> None:
    name = "No localhost for service-to-service traffic (-8)"
    targets = [ROOT / "compose.yaml", ROOT / "compose.prod.yaml", ROOT / "frontend/nginx.conf"]
    targets += files("k8s/**/*.yaml")
    problems = []
    for t in targets:
        for n, line in enumerate(read(t).splitlines(), 1):
            if "localhost" in line and not line.strip().startswith("#"):
                problems.append(f"{t.relative_to(ROOT)}:{n}")
    ok(name) if not problems else fail(name, ", ".join(problems))


def check_prod_ports() -> None:
    name = "No published DB/cache port in compose.prod.yaml; no NodePort/LoadBalancer on the DB (-8)"
    problems = []
    prod = read(ROOT / "compose.prod.yaml")
    for svc in ("postgres", "redis"):
        m = re.search(rf"^  {svc}:\n(.*?)(?=^  \S|\Z)", prod, re.M | re.S)
        if m and re.search(r"^\s+ports:", m.group(1), re.M):
            problems.append(f"compose.prod.yaml publishes {svc} ports")
    for yf in files("k8s/**/*.yaml"):
        text = read(yf)
        if re.search(r"kind:\s*Service\b", text) and re.search(r"type:\s*(NodePort|LoadBalancer)", text):
            problems.append(f"{yf.relative_to(ROOT)} has a NodePort/LoadBalancer Service")
    ok(name) if not problems else fail(name, "; ".join(problems))


def check_postgres_statefulset() -> None:
    name = "PostgreSQL is a StatefulSet with a PVC (-8)"
    text = read(ROOT / "k8s/base/postgres.yaml")
    if "kind: StatefulSet" in text and "volumeClaimTemplates" in text:
        ok(name)
    else:
        fail(name, "k8s/base/postgres.yaml needs kind: StatefulSet and volumeClaimTemplates")


def check_k8s_secrets() -> None:
    name = "No real secret material in committed Kubernetes manifests (-15)"
    problems = []
    for yf in files("k8s/**/*.yaml"):
        text = read(yf)
        if re.search(r"gsk_|AIza[0-9A-Za-z_-]{20,}", text):
            problems.append(f"{yf.relative_to(ROOT)}: looks like an API key")
        if re.search(r"^kind:\s*Secret\b", text, re.M):
            for m in re.finditer(r"^\s{2}(\w+):\s*\"?([^\s\"#]+)\"?\s*$", text.split("data:")[-1], re.M):
                if m.group(2) not in ("REPLACE_ME",) and re.fullmatch(r"[A-Za-z0-9+/=]{16,}", m.group(2)):
                    problems.append(f"{yf.relative_to(ROOT)}: {m.group(1)} holds a non-placeholder value")
    ok(name) if not problems else fail(name, "; ".join(problems))


def check_network_isolation() -> None:
    name = "Two networks, edge + internal (internal: true); frontend not on internal (-8)"
    for cf in ("compose.yaml", "compose.prod.yaml"):
        text = read(ROOT / cf)
        if not re.search(r"internal:\s*true", text):
            fail(name, f"{cf} has no `internal: true` network")
            return
        m = re.search(r"^  frontend:\n(.*?)(?=^  \S|^\S|\Z)", text, re.M | re.S)
        if m and "internal" in re.findall(r"^\s+- (\w+)$", m.group(1).split("networks:")[-1], re.M):
            fail(name, f"{cf}: frontend is attached to the internal network")
            return
    ok(name)


# ---------------------------------------------------------------- workflows


def workflow_jobs(text: str) -> dict[str, str]:
    """Split a workflow into {job_name: block_text} without a YAML parser."""
    m = re.search(r"^jobs:\s*\n(.*)", text, re.M | re.S)
    if not m:
        return {}
    parts = re.split(r"^  ([A-Za-z0-9_-]+):\s*$", m.group(1), flags=re.M)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def check_workflows() -> None:
    wf_dir = ROOT / ".github/workflows"
    for name in ("ci.yml", "cd.yml", "release.yml"):
        if not (wf_dir / name).is_file():
            fail("Workflow files present", f"missing .github/workflows/{name}")
            return
    ok("Workflow files present (ci.yml, cd.yml, release.yml)")

    gate = "Every publishing/deploying job is gated by needs: (-8)"
    problems = []
    for wf in wf_dir.glob("*.yml"):
        text = read(wf)
        for job, block in workflow_jobs(text).items():
            publishes = re.search(r"push:\s*true|docker push|deploy\.sh|kubectl apply", block)
            if publishes and not re.search(r"^    needs:", block, re.M):
                problems.append(f"{wf.name}:{job}")
    ok(gate) if not problems else fail(gate, ", ".join(problems))

    perms = "Every workflow has a top-level permissions: block"
    missing = [w.name for w in wf_dir.glob("*.yml") if not re.search(r"^permissions:", read(w), re.M)]
    ok(perms) if not missing else fail(perms, ", ".join(missing))

    pins = "Actions pinned to >= @v4, a full version tag, or a SHA"
    loose = []
    for wf in wf_dir.glob("*.yml"):
        for ref in re.findall(r"uses:\s*([\w./-]+@[\w.-]+)", read(wf)):
            version = ref.split("@", 1)[1]
            major = re.match(r"v(\d+)(\.\d+\.\d+)?$", version)
            if re.fullmatch(r"[0-9a-f]{40}", version):
                continue
            if major and (int(major.group(1)) >= 4 or major.group(2)):
                continue
            loose.append(f"{wf.name}: {ref}")
    ok(pins) if not loose else fail(pins, "; ".join(loose))

    ci = read(wf_dir / "ci.yml")
    if "push: false" in ci and "push: true" not in ci:
        ok("PR CI never pushes images")
    else:
        fail("PR CI never pushes images", "ci.yml must not contain `push: true`")
    if "TRIAGE_PROVIDER: simulated" in ci:
        ok("CI uses TRIAGE_PROVIDER=simulated")
    else:
        fail("CI uses TRIAGE_PROVIDER=simulated", "not set in ci.yml")


# ---------------------------------------------------------------- documents


def check_documents() -> None:
    required = [
        "README.md",
        "LICENSE",
        ".env.example",
        "compose.yaml",
        "compose.prod.yaml",
        "load/k6-script.js",
        "docs/RUNBOOK.md",
        "docs/AI-USAGE.md",
        "docs/TRIAGE.md",
        "docs/ENGINEERING-NOTES.md",
        "docs/adr/0001-provider-interface.md",
        "docs/adr/0002-frontend-runtime-config.md",
        "docs/adr/0003-deploy-by-sha.md",
        "docs/adr/0004-pii-and-data-governance.md",
        "backend/Dockerfile",
        "backend/.dockerignore",
        "frontend/Dockerfile",
        "frontend/.dockerignore",
        "frontend/nginx.conf",
    ]
    missing = [r for r in required if not (ROOT / r).is_file()]
    ok("Required files present") if not missing else fail("Required files present", ", ".join(missing))

    evidence = ROOT / "docs/evidence"
    if evidence.is_dir() and any(evidence.rglob("*")):
        ok("docs/evidence/ is populated")
    else:
        fail("docs/evidence/ is populated", "directory missing or empty")

    readme = read(ROOT / "README.md")
    for label, pattern in (
        ("README has badges", r"badge\.svg|img\.shields\.io"),
        ("README has a Mermaid diagram", r"```mermaid"),
        ("README has an API table", r"\|\s*Method\s*\|"),
        ("README has a docker compose quickstart", r"docker compose up"),
    ):
        ok(label) if re.search(pattern, readme) else fail(label, "not found")
    if re.search(r"!\[[^\]]*\]\((?!https?://)[^)]+\.(png|jpg|jpeg|gif)\)", readme):
        ok("README has screenshots")
    else:
        warn("README has screenshots", "no local image reference found")

    notes = read(ROOT / "docs/ENGINEERING-NOTES.md")
    missing_q = [f"Q{i}" for i in range(1, 9) if not re.search(rf"^#+ .*\bQ{i}\b", notes, re.M)]
    if missing_q:
        fail("ENGINEERING-NOTES answers all eight questions", "no heading for " + ", ".join(missing_q))
    else:
        ok("ENGINEERING-NOTES answers all eight questions")


def main() -> int:
    check_secrets_in_history()
    check_main_history()
    check_collaboration()
    check_pinned_images()
    check_no_latest_deploy()
    check_localhost()
    check_prod_ports()
    check_postgres_statefulset()
    check_k8s_secrets()
    check_network_isolation()
    check_workflows()
    check_documents()

    width = max(len(c) for _, c, _ in results)
    for status, check, detail in results:
        print(f"[{status}] {check.ljust(width)}" + (f"  {detail}" if detail else ""))
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    warned = sum(1 for s, _, _ in results if s == "WARN")
    print(f"\n{len(results) - failed - warned} passed, {warned} warning(s), {failed} failed")
    print("Not checked here (do by hand): GitHub branch protection, repo secrets, a green cd.yml run,")
    print("GHCR packages, demo video, red->green CI screenshots, README quickstart from a clean clone.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
