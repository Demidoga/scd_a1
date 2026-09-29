"""Render replicas-vs-CPU-utilization charts from the hpa-watch*.log captures
(Milestone 8, docs/ENGINEERING-NOTES.md "Live run"). Each log line is one
`kubectl get hpa backend -n civicpulse` sample, prefixed with a UTC HH:MM:SS
timestamp by the polling loop in the operational guide.

Usage: uv run --with matplotlib,pyyaml python load/results/plot_hpa.py
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt

LINE_RE = re.compile(
    r"^(?P<ts>\d\d:\d\d:\d\d)\s+backend\s+Deployment/backend\s+"
    r"cpu:\s+(?P<cpu>unknown|\d+)%?(?:/60%)?\s+\d+\s+\d+\s+(?P<replicas>\d+)"
)


def parse(path: Path):
    times, cpu, replicas = [], [], []
    base = None
    for line in path.read_text().splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        t = datetime.strptime(m.group("ts"), "%H:%M:%S")
        if base is None:
            base = t
        elapsed = (t - base).total_seconds()
        if elapsed < 0:  # crossed midnight during the run
            elapsed += 24 * 3600
        times.append(elapsed)
        cpu.append(None if m.group("cpu") == "unknown" else int(m.group("cpu")))
        replicas.append(int(m.group("replicas")))
    return times, cpu, replicas


def plot(path: Path, title: str, out: Path):
    times, cpu, replicas = parse(path)
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.step(times, replicas, where="post", color="tab:blue", label="replicas")
    ax1.set_xlabel("seconds since first sample")
    ax1.set_ylabel("replicas", color="tab:blue")
    ax1.set_ylim(0, 11)
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    cpu_x = [t for t, c in zip(times, cpu) if c is not None]
    cpu_y = [c for c in cpu if c is not None]
    ax2.plot(cpu_x, cpu_y, color="tab:red", alpha=0.7, label="CPU % of request")
    ax2.axhline(60, color="tab:red", linestyle="--", alpha=0.4, label="60% target")
    ax2.set_ylabel("CPU utilization (% of request)", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"wrote {out}")


if __name__ == "__main__":
    here = Path(__file__).parent
    plot(
        here / "hpa-watch.log",
        "Run 1 — original requests (cpu: 100m) — replicas vs. CPU utilization",
        here / "hpa-run1-replicas-vs-load.png",
    )
    plot(
        here / "hpa-watch-2.log",
        "Run 2 — VPA-resized requests (cpu: 300m) — replicas vs. CPU utilization",
        here / "hpa-run2-replicas-vs-load.png",
    )
