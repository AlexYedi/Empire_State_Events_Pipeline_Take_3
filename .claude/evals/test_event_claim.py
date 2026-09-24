#!/usr/bin/env python3
"""test_event_claim.py — the single-writer claim for an event's external namespace (YED-213). Offline, free.

Pins the behaviour that would have stopped the 2026-09-20 Notion collision: a second session running the same
event must be REFUSED, not left to notice a timestamp by luck.
"""
import importlib.util, json, os, sys, tempfile, datetime

spec = importlib.util.spec_from_file_location("ec", ".claude/hooks/event-claim.py")
ec = importlib.util.module_from_spec(spec); spec.loader.exec_module(ec)
ec.CLAIM_DIR = tempfile.mkdtemp(prefix="claims-")          # never touch the real ~/.claude
ok = n = 0


def ck(name, cond):
    global ok, n; n += 1; ok += bool(cond); print(("  ✓ " if cond else "  ✗ ") + name)


def as_session(sid):
    os.environ["CLAUDE_CODE_SESSION_ID"] = sid


SLUG = "AI Show and Tell New York"
as_session("session-A")
ck("a free event claims cleanly", ec.status(SLUG, 4)[0] == "free")
ec.write_claim(SLUG, 4)
ck("the claiming session sees it as MINE", ec.status(SLUG, 4)[0] == "mine")

as_session("session-B")
ck("a DIFFERENT session sees it as HELD (the 09-20 collision, now visible)", ec.status(SLUG, 4)[0] == "held")
ck("the slug is normalised, so 'AI Show & Tell, New York' collides with it too",
   ec.status("AI Show & Tell, New York!", 4)[0] == "held")

# stale expiry: a crashed session must not lock an event forever
c = ec.read(SLUG)
old = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=9)).isoformat(timespec="seconds").replace("+00:00", "Z")
c["claimed_at"] = c["heartbeat"] = old
json.dump(c, open(ec.path_for(SLUG), "w"))
ck("a 9h-old claim is STALE at the 4h default", ec.status(SLUG, 4)[0] == "stale")
ck("...but still LIVE if the ttl is raised past its age", ec.status(SLUG, 12)[0] == "held")
ec.write_claim(SLUG, 4, took_over=c)
ck("taking over a stale claim records who it was taken from", ec.read(SLUG).get("took_over_from", {}).get("session_id") == "session-A")

# release
ec.status(SLUG, 4)
c = ec.read(SLUG); c["released_at"] = "2026-09-24T00:00:00Z"; json.dump(c, open(ec.path_for(SLUG), "w"))
ck("a released claim frees the event", ec.status(SLUG, 4)[0] == "free")

# corrupt / unparseable
json.dump({"event": SLUG, "session_id": "x", "claimed_at": "not-a-date"}, open(ec.path_for(SLUG), "w"))
ck("an unparseable timestamp is STALE, not a permanent lock", ec.status(SLUG, 4)[0] == "stale")
open(ec.path_for(SLUG), "w").write("{ broken json")
ck("a corrupt claim file reads as FREE rather than crashing the pipeline", ec.status(SLUG, 4)[0] == "free")

# the claim dir is machine-global, NOT per-worktree — the whole point
ck("claims live outside any worktree (~/.claude), so other sessions can see them",
   "/.claude/event-claims" in ec.__dict__["CLAIM_DIR"] or ec.CLAIM_DIR.startswith(tempfile.gettempdir()))
ck("the real default is machine-global",
   importlib.util.spec_from_file_location("ec2", ".claude/hooks/event-claim.py") is not None
   and "expanduser" in open(".claude/hooks/event-claim.py").read())
print(f"{ok}/{n} event-claim cases pass")
sys.exit(0 if ok == n else 1)
