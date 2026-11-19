#!/usr/bin/env python3
"""YED-411 step 6: daily laptop <-> mini parity check. Read-only: it compares and reports, it never syncs or fixes.

Catches the silent failures found on 11/18 (symlinks skipped by worktrees, a source 17 days stale) before a session
hits them. Runs under launchd, which cannot read ~/Documents (TCC), so the hard links into that checkout are checked
from this side: each private file in the landing folder must have link count >= 2 (1 = the ~/Documents link broke).

Checks (each PASS / FAIL / SKIP with evidence):
  sync-age     last good private sync (.synced-at) < 2 h when the laptop is reachable, < 36 h otherwise
  hard-links   every private file in the landing folder has >= 2 links
  private      laptop vs mini content (rsync --dry-run --checksum, read-only keys) for the 4 files + reviews/
  memory       laptop vs mini note content (MEMORY.md excluded) and every laptop index line present on the mini
  inbox        no memory-inbox item older than 8 days (a missed Friday review)
Writes ~/Developer/esep-private/parity.json (read by /freshen). Exit 0 all pass/skip, 11 any FAIL. Stdlib only.
"""
import json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
PRIVATE = Path(os.environ.get("ESEP_PRIVATE", HOME / "Developer/esep-private"))
LAPTOP = os.environ.get("ESEP_LAPTOP", "alexs-macbook-pro-2")
RSYNC = "/opt/homebrew/bin/rsync"
FILES = [".claude/references/me-model.md", ".claude/references/target-companies.md",
         ".claude/references/inbox-denylist.md", ".claude/references/inbox-allowlist.md"]
MEMSLUG = "-Users-sameoldexpressions-Documents-GitHub-Empire-State-Events-Pipeline-Take-3"
MINI_MEM = Path(os.environ.get("ESEP_MINI_MEM", HOME / f".claude/projects/{MEMSLUG}/memory"))
results = []


def rec(name, status, evidence):
    results.append({"check": name, "status": status, "evidence": evidence})


def ssh(key):
    return f"ssh -i {HOME}/.ssh/{key} -o BatchMode=yes -o ConnectTimeout=10 -o IdentitiesOnly=yes"


def dry(key, srcs, dest, extra=()):
    """Paths that would change if we synced now (= differ by checksum). None if the laptop is unreachable."""
    cmd = [RSYNC, "-n", "-a", "-c", "--itemize-changes", "--relative", *extra, "-e", ssh(key), *srcs, str(dest) + "/"]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if p.returncode == 255:
        return None
    if p.returncode not in (0, 23, 24):
        raise RuntimeError(f"rsync rc={p.returncode}: {p.stderr.strip()[-200:]}")
    return [l.split(" ", 1)[1] for l in p.stdout.splitlines() if l[:2] in (">f", "<f", "cf") or l.startswith(">f")]


def main():
    reachable = subprocess.run(["ssh", "-i", f"{HOME}/.ssh/esep_sync", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
                                "-o", "IdentitiesOnly=yes", LAPTOP, "true"], capture_output=True).returncode != 255
    # sync-age
    try:
        last = datetime.fromisoformat((PRIVATE / ".synced-at").read_text().strip().replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        limit = 2 if reachable else 36
        rec("sync-age", "PASS" if age_h < limit else "FAIL",
            f"last sync {last:%Y-%m-%d %H:%MZ} ({age_h:.1f} h ago; limit {limit} h, laptop {'reachable' if reachable else 'unreachable'})")
    except (OSError, ValueError) as e:
        rec("sync-age", "FAIL", f"no readable .synced-at ({type(e).__name__})")
    # hard-links
    bad = [f for f in FILES if (PRIVATE / f).exists() and os.stat(PRIVATE / f).st_nlink < 2]
    missing = [f for f in FILES if not (PRIVATE / f).exists()]
    rec("hard-links", "FAIL" if bad or missing else "PASS",
        f"broken: {bad}; missing: {missing}" if bad or missing else f"{len(FILES)} files linked into the ~/Documents checkout")
    if not reachable:
        for c in ("private", "memory"):
            rec(c, "SKIP", "laptop unreachable (asleep or off Tailscale); compared next run")
    else:
        try:
            srcs = [f"{LAPTOP}:{FILES[0]}"] + [f":{f}" for f in FILES[1:]] + [":.claude/.state/reviews/"]
            diff = dry("esep_sync", srcs, PRIVATE, ("--exclude=.DS_Store",))
            rec("private", "PASS" if not diff else "FAIL", "identical by checksum" if not diff else f"differ: {diff[:8]}")
        except Exception as e:
            rec("private", "FAIL", f"compare error: {e}")
        try:
            if not (HOME / ".ssh/esep_memory").exists():
                rec("memory", "SKIP", "no esep_memory key")
            else:
                diff = dry("esep_memory", [f"{LAPTOP}:./"], MINI_MEM, ("--include=*.md", "--exclude=MEMORY.md", "--exclude=*"))
                lap_idx = PRIVATE / "memory-laptop/MEMORY.md"
                mini_idx = MINI_MEM / "MEMORY.md"
                missing_lines = []
                if lap_idx.exists() and mini_idx.exists():
                    have = set(mini_idx.read_text(encoding="utf-8").splitlines())
                    missing_lines = [l for l in lap_idx.read_text(encoding="utf-8").splitlines() if l.strip() and l not in have]
                ok = not diff and not missing_lines
                rec("memory", "PASS" if ok else "FAIL",
                    "notes identical, index complete" if ok else f"notes differ: {(diff or [])[:8]}; index lines missing: {len(missing_lines)}")
        except Exception as e:
            rec("memory", "FAIL", f"compare error: {e}")
    # inbox
    inbox = PRIVATE / "memory-inbox"
    items = [p for p in inbox.rglob("*.md")] if inbox.is_dir() else []
    old = [p for p in items if time.time() - p.stat().st_mtime > 8 * 86400]
    rec("inbox", "FAIL" if old else "PASS",
        f"{len(items)} item(s), {len(old)} older than 8 days (Friday review missed)" if old else f"{len(items)} item(s), none overdue")
    fails = [r for r in results if r["status"] == "FAIL"]
    report = {"checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "ok": not fails, "results": results}
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "parity.json").write_text(json.dumps(report, indent=1))
    for r in results:
        print(f"{r['check']:<11} {r['status']:<4} {r['evidence']}")
    print(f"PARITY: {'OK' if not fails else 'FAIL (' + ', '.join(r['check'] for r in fails) + ')'}")
    return 0 if not fails else 11


if __name__ == "__main__":
    sys.exit(main())
