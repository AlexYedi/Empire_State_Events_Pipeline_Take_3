#!/usr/bin/env python3
"""event-claim.py — one session owns an event's external namespace at a time (YED-213).

THE FAILURE THIS PREVENTS (2026-09-20). Four sessions ran concurrently; two independently ran the full pipeline
for "AI Show and Tell New York". One wrote the Event page, 6 People, 2 Companies, 3 Topics and 5 Content Drafts;
the other reached its Notion write step seven minutes later. No duplicates were created only because that
session happened to run a dedup search and notice a timestamp. It still produced two contradictory records
(Microsoft Agent Framework GA status, Foundry Control Plane GA month) and a thank-you to an unconfirmed
presenter. Duplicate effort is the cheap cost; contradictory records that later runs read as fact are not.

**Git isolation does not isolate Notion.** Both sessions had clean trees, correct branches, no shared files.
Every existing safeguard passed.

WHERE THE CLAIM LIVES, and why not where the issue first proposed. YED-213 suggested
`.claude/.state/event-claims/`. That is gitignored AND per-worktree, so a marker there is invisible to every
other session — the exact blindness YED-214 documented behind this same collision. Claims therefore live
MACHINE-GLOBAL at ~/.claude/event-claims/, outside any worktree, visible to every session on this machine.

ALTERNATIVES WEIGHED (acceptance #2):
  * A property on the Notion Event page — survives across machines, but costs an MCP round-trip per check and
    CANNOT cover the window that actually failed: at Step 1 the Event page often does not exist yet. Rejected.
  * A committed marker (as the graph freeze does) — the freeze is a deliberate, hours-to-days state change worth
    a commit; a pipeline claim is ephemeral and per-run, so committing one would add push/pull races and noise
    to every event. Rejected.
  * Rely on the existing dedup search — that is what failed: it is advisory, and it only catches a collision
    once the other session has already written. Rejected.
  * Machine-global runtime dir — covers concurrent local sessions (the real failure), no network, no commits.
    CHOSEN. Limitation, stated plainly: it does not coordinate across machines.

Usage:
  event-claim.py claim   <event-slug> [--ttl-hours N] [--force "<why>"]   # exit 0 claimed · 3 held by another
  event-claim.py check   <event-slug>                                     # exit 0 free/mine · 3 held
  event-claim.py release <event-slug>                                     # always exit 0 (idempotent)
  event-claim.py list [--all]                                             # live claims (or all, incl. stale)
Stale claims expire after --ttl-hours (default 4) so a crashed session cannot lock an event forever.
"""
from __future__ import annotations
import argparse, datetime, json, os, re, sys

CLAIM_DIR = os.path.expanduser("~/.claude/event-claims")
DEFAULT_TTL_HOURS = 4.0


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def slugify(s: str) -> str:
    """Normalise only what is unambiguous. `&` -> `and` because two sessions typing the same event name will
    differ there; NOT stopword-stripping or fuzzy matching, because a false collision LOCKS a legitimate run,
    which is worse than the miss it prevents. Known gap: "AI Show and Tell NY" and "...New York" still do not
    collide. The dedup search remains the second line of defence."""
    s = s.lower().replace("&", " and ")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")[:80]


def path_for(slug: str) -> str:
    return os.path.join(CLAIM_DIR, f"{slugify(slug)}.json")


def read(slug: str) -> dict | None:
    try:
        with open(path_for(slug), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def age_hours(c: dict) -> float | None:
    try:
        t = datetime.datetime.fromisoformat(str(c.get("heartbeat") or c["claimed_at"]).replace("Z", "+00:00"))
        return (now() - t).total_seconds() / 3600
    except (KeyError, ValueError):
        return None


def me() -> str:
    return os.environ.get("CLAUDE_CODE_SESSION_ID", "_nosession")


def status(slug: str, ttl: float) -> tuple[str, dict | None]:
    """free | mine | stale | held — the only four states a caller needs."""
    c = read(slug)
    if not c:
        return "free", None
    if c.get("released_at"):
        return "free", c
    a = age_hours(c)
    if a is None or a > ttl:                 # unparseable timestamp counts as stale, not as a permanent lock
        return "stale", c
    return ("mine" if c.get("session_id") == me() else "held"), c


def write_claim(slug: str, ttl: float, note: str = "", took_over: dict | None = None) -> dict:
    os.makedirs(CLAIM_DIR, exist_ok=True)
    c = {"event": slug, "slug": slugify(slug), "session_id": me(), "claimed_at": now().isoformat(timespec="seconds").replace("+00:00", "Z"),
         "heartbeat": now().isoformat(timespec="seconds").replace("+00:00", "Z"), "ttl_hours": ttl,
         "cwd": os.getcwd(), "pid": os.getpid(), "note": note, "released_at": None}
    if took_over:
        c["took_over_from"] = {k: took_over.get(k) for k in ("session_id", "claimed_at", "cwd")}
    with open(path_for(slug), "w", encoding="utf-8") as f:
        json.dump(c, f, indent=1)
    return c


def describe(c: dict) -> str:
    a = age_hours(c)
    return (f"session {str(c.get('session_id'))[:8]} · started {str(c.get('claimed_at'))[:19]}"
            f"{f' · {a:.1f}h ago' if a is not None else ''} · in {c.get('cwd', '?')}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["claim", "check", "release", "list"])
    ap.add_argument("slug", nargs="?", default="")
    ap.add_argument("--ttl-hours", type=float, default=DEFAULT_TTL_HOURS)
    ap.add_argument("--force", default="", metavar="WHY", help="take over a live claim; the reason is recorded")
    ap.add_argument("--note", default="")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()

    if a.cmd == "list":
        os.makedirs(CLAIM_DIR, exist_ok=True)
        rows = []
        for f in sorted(os.listdir(CLAIM_DIR)):
            if not f.endswith(".json"):
                continue
            c = read(f[:-5])
            if not c:
                continue
            st, _ = status(f[:-5], a.ttl_hours)
            if a.all or st in ("mine", "held"):
                rows.append(f"  {st:<6} {c.get('slug', '?'):<44} {describe(c)}")
        print("\n".join(rows) if rows else "  (no live claims)")
        return 0

    if not a.slug:
        print("ERROR: a slug is required", file=sys.stderr); return 2
    st, c = status(a.slug, a.ttl_hours)

    if a.cmd == "check":
        if st == "held":
            print(f"HELD by another session — {describe(c)}", file=sys.stderr); return 3
        print(f"{st}" + (f" — {describe(c)}" if c and st == "mine" else ""))
        return 0

    if a.cmd == "release":
        if c and st in ("mine", "stale", "held"):
            c["released_at"] = now().isoformat(timespec="seconds").replace("+00:00", "Z")
            with open(path_for(a.slug), "w", encoding="utf-8") as f:
                json.dump(c, f, indent=1)
            print(f"released {slugify(a.slug)}")
        else:
            print(f"nothing to release for {slugify(a.slug)}")
        return 0

    # claim
    if st == "held" and not a.force:
        print(f"REFUSED: '{slugify(a.slug)}' is already being run by another session — {describe(c)}\n"
              f"  Go READ-ONLY for this event and report, exactly as the reconciliation terminal does for git.\n"
              f"  If that session is dead, wait for the {a.ttl_hours:g}h expiry, or take it over deliberately:\n"
              f"    event-claim.py claim {slugify(a.slug)} --force \"<why>\"", file=sys.stderr)
        return 3
    took = c if (st in ("held", "stale") and c) else None
    new = write_claim(a.slug, a.ttl_hours, a.note, took)
    if st == "stale" and c:
        print(f"took over a STALE claim ({describe(c)})")
    elif a.force and st == "held":
        print(f"FORCED takeover of a live claim — reason: {a.force}\n  previous: {describe(c)}")
        new["forced_reason"] = a.force
        with open(path_for(a.slug), "w", encoding="utf-8") as f:
            json.dump(new, f, indent=1)
    print(f"claimed {new['slug']} for session {new['session_id'][:8]} (ttl {a.ttl_hours:g}h)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
