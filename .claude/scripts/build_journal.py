#!/usr/bin/env python3
"""
Build-journal generator (YED-119 V1) — the self-instrumenting build journal, honest edition.

Assembles a per-build-day journal from FACTS the repos already record, then merges a human-owned
prose sidecar for the ≤3-line what/why/value summary. NO LLM, no API tokens, no fabrication:
every structured field is git/telemetry-derived; the only prose is what a human wrote in the sidecar.

    per build day:
      - shipped    = PR-squash/merge commits (title matches "(#N)") across BOTH repos  → the durable "what"
      - commits    = total commits that day (churn like build-sessions.jsonl updates included in the count only)
      - linear     = YED-\\d+ refs parsed from commit titles
      - rigor      = from build-sessions.jsonl: sessions, dod_met (any), dod_waived (any), correction_rounds (sum)
      - headline   + summary = from the curated prose sidecar (build-journal-prose.json), keyed by date
                     (fallback headline = the day's top PR title; summary = "" so the entry is still honest)

Output: a single JSON the Hub renders (default ../empire-state-hub/src/data/build-journal.json).

Usage:
    python3 .claude/scripts/build_journal.py                 # write to the hub data file
    python3 .claude/scripts/build_journal.py --dry-run       # print summary, write nothing
    python3 .claude/scripts/build_journal.py --since 2026-07-01
    python3 .claude/scripts/build_journal.py --out /path/to/build-journal.json

No secrets, no network — pure git + file reads. Safe to re-run (idempotent); wire to a hook later (V2).
"""
import json, os, re, subprocess, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
TAKE3 = os.path.abspath(os.path.join(HERE, "..", ".."))                 # Empire_State_Events_Pipeline_Take_3
HUB = os.path.abspath(os.path.join(TAKE3, "..", "empire-state-hub"))
REPOS = [("Empire_State_Events_Pipeline_Take_3", TAKE3), ("empire-state-hub", HUB)]
TELEMETRY = os.path.join(TAKE3, ".claude", "artifacts", "build-sessions.jsonl")
PROSE = os.path.join(TAKE3, ".claude", "data", "build-journal-prose.json")
DEFAULT_OUT = os.path.join(HUB, "src", "data", "build-journal.json")
DEFAULT_SINCE = "2026-07-01"

PR_RE = re.compile(r"\(#(\d+)\)\s*$")
YED_RE = re.compile(r"\b(YED-\d+)\b")
# NB: churn (build-sessions/dod-waivers updates, bare "build session" commits) is excluded from "shipped"
# for free — those commits carry no "(#N)", so PR_RE never matches them. No explicit churn filter needed.


def gh_repo(path):
    try:
        url = subprocess.check_output(["git", "-C", path, "remote", "get-url", "origin"], text=True).strip()
    except Exception:
        return None
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    return m.group(1) if m else None


def git_log(path, since):
    try:
        out = subprocess.check_output(
            ["git", "-C", path, "log", f"--since={since}", "--no-merges",
             "--pretty=format:%ad\t%s", "--date=short"],
            text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    rows = []
    for line in out.splitlines():
        if "\t" not in line:
            continue
        d, subj = line.split("\t", 1)
        rows.append((d, subj.strip()))
    return rows


def load_prose():
    if not os.path.exists(PROSE):
        return {}
    try:
        return json.load(open(PROSE))
    except Exception:
        return {}


def load_telemetry_by_day(since):
    days = {}
    if not os.path.exists(TELEMETRY):
        return days
    for line in open(TELEMETRY):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = r.get("started_at") or r.get("ended_at") or ""
        d = ts[:10]
        if not d or d < since:
            continue
        b = days.setdefault(d, {"sessions": 0, "dod_met": False, "dod_waived": False,
                                "correction_rounds": 0, "tool_uses": 0})
        b["sessions"] += 1
        if r.get("dod_met") is True:
            b["dod_met"] = True
        if r.get("dod_waived") is True:
            b["dod_waived"] = True
        b["correction_rounds"] += int(r.get("correction_rounds") or 0)
        b["tool_uses"] += int(r.get("tool_uses") or 0)
    return days


def main():
    args = sys.argv[1:]

    def argval(flag, default):
        # guard against a flag given with no following value (avoids an IndexError)
        if flag in args:
            i = args.index(flag)
            if i + 1 < len(args):
                return args[i + 1]
            sys.exit(f"{flag} requires a value")
        return default

    dry = "--dry-run" in args
    since = argval("--since", DEFAULT_SINCE)
    out = argval("--out", DEFAULT_OUT)

    prose = load_prose()
    telem = load_telemetry_by_day(since)

    # collect per-day: shipped PRs, commit counts, linear refs
    day = {}  # date -> dict
    for repo_name, path in REPOS:
        slug = gh_repo(path) or repo_name
        for d, subj in git_log(path, since):
            e = day.setdefault(d, {"shipped": [], "commits": 0, "linear": set()})
            e["commits"] += 1
            for ref in YED_RE.findall(subj):
                e["linear"].add(ref)
            m = PR_RE.search(subj)
            if m:
                num = int(m.group(1))
                title = PR_RE.sub("", subj).strip()
                e["shipped"].append({
                    "repo": repo_name.replace("Empire_State_Events_Pipeline_Take_3", "pipeline").replace("empire-state-hub", "hub"),
                    "num": num, "title": title,
                    "url": f"https://github.com/{slug}/pull/{num}",
                })

    entries = []
    for d in sorted(day.keys(), reverse=True):
        e = day[d]
        p = prose.get(d, {})
        # skip pure-churn days that shipped nothing and have no curated prose
        if not e["shipped"] and not p.get("summary"):
            continue
        t = telem.get(d, {})
        headline = p.get("headline") or (e["shipped"][0]["title"] if e["shipped"] else "Build day")
        entries.append({
            "date": d,
            "headline": headline,
            "summary": p.get("summary", ""),      # curated ≤3-line what/why/value; "" if not yet written
            "curated": bool(p.get("summary")),
            "shipped": sorted(e["shipped"], key=lambda x: x["num"], reverse=True),
            "linear": sorted(e["linear"]),
            "metrics": {
                "prs": len(e["shipped"]),
                "commits": e["commits"],
                "sessions": t.get("sessions", 0),
                "tools": t.get("tool_uses", 0),
                "dod_met": t.get("dod_met", False),
                "dod_waived": t.get("dod_waived", False),
                "correction_rounds": t.get("correction_rounds", 0),
            },
        })

    doc = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since": since,
        "entries": entries,
    }

    total_prs = sum(x["metrics"]["prs"] for x in entries)
    curated = sum(1 for x in entries if x["curated"])
    print(f"Build journal {'(DRY RUN)' if dry else ''} — {len(entries)} build days | "
          f"{total_prs} PRs shipped | {curated} days with curated prose | since {since}")
    for x in entries[:12]:
        flag = "✍" if x["curated"] else "·"
        dod = "DoD✓" if x["metrics"]["dod_met"] else ("DoD~" if x["metrics"]["dod_waived"] else "—")
        print(f"  {flag} {x['date']}  {x['metrics']['prs']}PR {dod}  {x['headline'][:56]}")
    if len(entries) > 12:
        print(f"  … +{len(entries)-12} more")

    if not dry:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n✅ wrote {len(entries)} entries → {out}")


if __name__ == "__main__":
    main()
