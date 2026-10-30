#!/usr/bin/env python3
"""Live Frontier scorecard: reads today's factory PRs from GitHub (gh CLI) and rewrites scorecard-live.md.

A factory PR = opened on or after START in either repo, on a branch that isn't alex/*.
"Needed me" = Alex pushed a commit to it or left a review/comment on it; manual notes come from notes.txt.
Run: python3 scorecard.py   (read-only against GitHub; writes only scorecard-live.md next to this file)
"""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

START = "2026-10-30T13:00:00Z"  # 9:00 ET
ME = "AlexYedi"
REPOS = {"pipeline": "AlexYedi/Empire_State_Events_Pipeline_Take_3", "hub": "AlexYedi/empire-state-hub"}
BASELINE = "~6–7 merged PRs on an ordinary active day (74 + 13 merges, 9/27–10/27)"
HERE = Path(__file__).parent

# File-path → (spec, tier). First match wins, so the most specific patterns come first.
RULES = [
    (r"obvious-factory-notes|^AGENTS\.md$", "00 rules probe", "Probe"),
    (r"src/app/api/mcp|docs/mcp\.md", "05 Rooms MCP", "T4"),
    (r"long-read", "04 Long Reads", "T3"),
    (r"builds|content-performance|feed\.xml|notion_payload\.py", "03 mid builds", "T2"),
    (r"^\.claude/scripts/|^\.github/workflows/selftests", "02 pipeline tests", "T1"),
    (r"not-found|sitemap|robots|opengraph|page\.tsx|layout\.tsx|rooms/\[slug\]", "01 hub fixes", "T1"),
]
PREDICTED = {"Specs": "solo", "Context": "solo", "Skills": "solo", "QA": "help",
             "CI": "out", "Review": "solo", "Loops": "help", "Design systems": "out"}


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"gh failed: {out.stderr.strip()}")
    return json.loads(out.stdout or "null")


def classify(files):
    for pat, spec, tier in RULES:
        if any(re.search(pat, f) for f in files):
            return spec, tier
    return "unmapped", "?"


def collect():
    prs = []
    for key, repo in REPOS.items():
        rows = gh("pr", "list", "-R", repo, "--state", "all", "--limit", "30", "--search", f"created:>={START[:10]}",
                  "--json", "number,title,author,createdAt,mergedAt,state,headRefName,files,commits,reviews,comments,body,statusCheckRollup,url")
        for p in rows:
            if p["createdAt"] < START or p["headRefName"].startswith("alex/"):
                continue
            files = [f["path"] for f in p["files"]]
            spec, tier = classify(files)
            my_commits = sum(1 for c in p["commits"] if any(a.get("login") == ME for a in c.get("authors", [])))
            my_reviews = sum(1 for r in p["reviews"] + p["comments"] if (r.get("author") or {}).get("login") == ME)
            checks = p.get("statusCheckRollup") or []
            prs.append({
                "repo": key, "n": p["number"], "url": p["url"], "title": p["title"], "author": p["author"]["login"],
                "created": p["createdAt"], "merged": p["mergedAt"], "state": p["state"], "spec": spec, "tier": tier,
                "files": files, "tests": any(re.search(r"test|selftest|fixtures", f) for f in files),
                "ci": [c.get("name") or c.get("context") for c in checks],
                "ci_ok": all((c.get("conclusion") or c.get("state")) in ("SUCCESS", "NEUTRAL", "SKIPPED") for c in checks) if checks else None,
                "helped": my_commits + my_reviews > 0, "body": p.get("body") or "",
            })
    return prs


def minutes(a, b):
    f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return round((f(b) - f(a)).total_seconds() / 60)


def render(prs):
    now = datetime.now(timezone.utc).astimezone().strftime("%H:%M")
    merged = [p for p in prs if p["merged"]]
    notes = (HERE / "notes.txt").read_text().strip() if (HERE / "notes.txt").exists() else ""
    L = [f"# Frontier scorecard (live, updated {now})", "",
         f"**Factory PRs: {len(prs)} opened · {len(merged)} merged.** Baseline: {BASELINE}.", ""]

    L += ["## Ladder", "", "| Tier | Spec | Opened | Merged | With tests | CI ran | Needed me |", "|---|---|---|---|---|---|---|"]
    order = ["Probe", "T1", "T2", "T3", "T4", "?"]
    groups = {}
    for p in prs:
        groups.setdefault((p["tier"], p["spec"]), []).append(p)
    for (tier, spec), g in sorted(groups.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1])):
        L.append(f"| {tier} | {spec} | {len(g)} | {sum(1 for p in g if p['merged'])} | {sum(p['tests'] for p in g)} | "
                 f"{sum(1 for p in g if p['ci'])} | {sum(p['helped'] for p in g)} |")

    probe = [p for p in prs if p["spec"] == "00 rules probe"]
    L += ["", "## Track A (rules probe)", ""]
    if not probe:
        L.append("No probe PRs yet.")
    for p in probe:
        run = "run 2 (AGENTS.md)" if "AGENTS.md" in p["files"] else "run 1 (CLAUDE.md only)"
        b = p["body"].lower()
        L.append(f"- {run} · [#{p['n']}]({p['url']}) · one-in-one-out raised: "
                 f"{'yes' if re.search(r'one-in-one-out|replac', b) else 'no'} · baseline attached: "
                 f"{'yes' if 'baseline' in b else 'no'} · cites CLAUDE.md: {'yes' if 'claude.md' in b else 'no'} · "
                 f"opened {minutes(START, p['created'])} min after 9:00")

    t1 = [p for p in prs if p["tier"] == "T1"]
    def frac(xs, f):
        return f"{sum(1 for x in xs if f(x))}/{len(xs)}" if xs else "–"
    ev = {
        "Specs": f"{len(groups)} spec groups produced PRs",
        "Context": "see Track A",
        "Skills": "manual",
        "QA": f"PRs with tests: {frac(prs, lambda p: p['tests'])}",
        "CI": f"PRs where CI ran: {frac(prs, lambda p: p['ci'])}; green: {frac([p for p in prs if p['ci']], lambda p: p['ci_ok'])}",
        "Review": f"merged with no help from me: {frac(merged, lambda p: not p['helped'])}",
        "Loops": f"T1 PRs needing me: {frac(t1, lambda p: p['helped'])}",
        "Design systems": f"T3 PRs: {len([p for p in prs if p['tier'] == 'T3'])}, merged {len([p for p in merged if p['tier'] == 'T3'])}",
    }
    L += ["", "## 8 controls (predicted vs evidence)", "", "| Control | Predicted | Evidence so far |", "|---|---|---|"]
    L += [f"| {c} | {PREDICTED[c]} | {ev[c]} |" for c in PREDICTED]

    L += ["", "## PRs", "", "| Repo | # | Spec | State | Mins open→merge | Needed me | Title |", "|---|---|---|---|---|---|---|"]
    for p in sorted(prs, key=lambda p: p["created"]):
        mm = minutes(p["created"], p["merged"]) if p["merged"] else ""
        L.append(f"| {p['repo']} | [#{p['n']}]({p['url']}) | {p['spec']} | {p['state'].lower()} | {mm} | "
                 f"{'yes' if p['helped'] else ''} | {p['title'][:70]} |")
    if notes:
        L += ["", "## Manual notes (things GitHub can't see)", "", notes]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    out = HERE / "scorecard-live.md"
    out.write_text(render(collect()))
    print(f"wrote {out}")
