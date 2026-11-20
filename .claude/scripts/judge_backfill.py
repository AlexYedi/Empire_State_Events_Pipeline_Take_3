#!/usr/bin/env python3
"""judge_backfill.py — write the 11/19 source-page judge verdicts onto claim (YED-451, g1119-t1).

WAITS FOR THE YED-451 MERGE. Until spine_client's ALLOW["claim"] opens the judge record, every PATCH is refused by
the guard. Nothing runs automatically; Alex (or a session he approves) runs it once.

What it writes, and nothing else: claim.judge_verdict, judge_model, judge_prompt_hash, judged_at. These are the 0023
judge-record columns. 0023's claim_judge_record_complete CHECK needs all four together, and claim_judge_verdict_vocab
admits only supported | unsupported | abstain. status, metadata and claim text are never touched.

Verdict mapping (the 11/19 run's labels -> the 0023 vocabulary):
  SUPPORTED     -> supported
  UNSUPPORTED   -> unsupported
  MISATTRIBUTED -> unsupported   (the page does not support the claim as attributed; 14 rows)
  UNREADABLE    -> abstain       (403 / 404 / login wall / paywall / still rate-limited: the judge could not decide)

Write path: substrate.Graph.patch -> spine_client guard (ADR-9). This file holds no socket code and no REST paths.
Safety:
  * Dry run by default; --apply is needed to write.
  * Idempotent: a row that already has a judge_verdict is skipped unless --overwrite. A later judge is never clobbered.
  * Refuses a judge model that is not given, or a prompt hash that is not 64 hex characters. If the prompt file sits
    next to the hash file, the hash must match its sha256.
  * Claim ids not found on prod are counted and reported, never created.

Usage (from the repo root):
  python3 .claude/scripts/judge_backfill.py \\
      --state .claude/.state/reviews/claim-judge-2026-11-19b/phase2b_state.json \\
      --hash-file .claude/.state/reviews/claim-judge-2026-11-19b/judge_prompt_v2.sha256 \\
      --judge-model <the model the 11/19 judge agents ran on> [--judged-at 2026-11-19T21:06:00Z] [--apply]
  python3 .claude/scripts/judge_backfill.py --selftest
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

VERDICT_MAP = {"SUPPORTED": "supported", "UNSUPPORTED": "unsupported", "MISATTRIBUTED": "unsupported",
               "UNREADABLE": "abstain"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
CHUNK = 50


def load_verdicts(state_path: str) -> dict[str, str]:
    """{claim_id: 0023 verdict} from the judge run's merged state. An unknown label is a hard failure, never a guess."""
    recs = json.load(open(state_path, encoding="utf-8"))["claim_records"]
    out, bad = {}, collections.Counter()
    for cid, r in recs.items():
        v = VERDICT_MAP.get(str(r.get("verdict", "")).upper())
        if v is None:
            bad[r.get("verdict")] += 1
        else:
            out[cid] = v
    if bad:
        raise SystemExit(f"judge_backfill: unknown verdict labels {dict(bad)}; refusing to map them")
    return out


def load_hash(hash_file: str) -> str:
    """The prompt hash from a `sha256sum`-style line. If the prompt file it names sits beside it, check the hash."""
    line = open(hash_file, encoding="utf-8").read().split()
    h = line[0].lower() if line else ""
    if not HEX64.match(h):
        raise SystemExit(f"judge_backfill: {hash_file} does not hold a 64-hex sha256")
    if len(line) > 1:
        prompt = os.path.join(os.path.dirname(hash_file), line[1])
        if os.path.exists(prompt) and hashlib.sha256(open(prompt, "rb").read()).hexdigest() != h:
            raise SystemExit(f"judge_backfill: sha256({line[1]}) != {hash_file}; the prompt changed since the run")
    return h


def backfill(g, verdicts: dict[str, str], *, model: str, prompt_hash: str, judged_at: str,
             overwrite: bool = False) -> collections.Counter:
    """PATCH the judge record onto each listed claim, grouped by verdict. Returns counts."""
    if not (model or "").strip():
        raise SystemExit("judge_backfill: --judge-model is required (no default: it must be the model that judged)")
    if not HEX64.match(prompt_hash or ""):
        raise SystemExit("judge_backfill: prompt hash must be 64 lowercase hex characters")
    import substrate
    c = collections.Counter()
    ids = list(verdicts)
    current = substrate._rows_by_id(g, ids, "id,judge_verdict")          # read before any write
    todo: dict[str, list[str]] = collections.defaultdict(list)
    for cid in ids:
        r = current.get(cid)
        if r is None:
            c["not_found"] += 1
        elif r.get("judge_verdict") is not None and not overwrite:
            c["already_judged"] += 1
        else:
            todo[verdicts[cid]].append(cid)
    for verdict, vids in sorted(todo.items()):
        body = {"judge_verdict": verdict, "judge_model": model.strip(), "judge_prompt_hash": prompt_hash,
                "judged_at": judged_at}
        for i in range(0, len(vids), CHUNK):
            g.patch("claim", f"id=in.({','.join(vids[i:i + CHUNK])})", body)
        c[verdict] += len(vids)
    return c


def _default_judged_at(state_path: str) -> str:
    """When the judge run's merged state was last written (UTC), as the judged_at for the whole batch."""
    t = dt.datetime.fromtimestamp(os.path.getmtime(state_path), tz=dt.timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def selftest() -> bool:
    import substrate
    results = []

    def ok(name, cond):
        results.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}")

    fg = substrate._FakeGraph()
    fg.t["claim"] = [{"id": i, "status": "approved", "metadata": {}, "judge_verdict": None} for i in "abcd"] + [
        {"id": "e", "status": "candidate", "metadata": {}, "judge_verdict": "supported"}]
    st = {r["id"]: r for r in fg.t["claim"]}
    h = "69ec0f7722fdca67198a5b8d9ccb8547d88002e10eac81bc00c9cb6e21e1301a"
    v = {"a": "supported", "b": "unsupported", "c": "abstain", "d": "unsupported", "e": "unsupported", "zz": "supported"}
    c = backfill(fg, v, model="m-1", prompt_hash=h, judged_at="2026-11-19T21:06:00Z")
    ok("writes all four judge columns together (0023 all-or-nothing CHECK)",
       all(st[i]["judge_model"] == "m-1" and st[i]["judge_prompt_hash"] == h
           and st[i]["judged_at"] == "2026-11-19T21:06:00Z" for i in "abcd"))
    ok("verdicts land as mapped", [st[i]["judge_verdict"] for i in "abcd"] ==
       ["supported", "unsupported", "abstain", "unsupported"])
    ok("an already-judged row is skipped; a missing id is counted, never created",
       st["e"]["judge_verdict"] == "supported" and c["already_judged"] == 1 and c["not_found"] == 1
       and len(fg.t["claim"]) == 5)
    ok("status and metadata untouched", all(st[i]["status"] == "approved" and st[i]["metadata"] == {} for i in "abcd"))
    backfill(fg, {"e": "unsupported"}, model="m-1", prompt_hash=h, judged_at="2026-11-19T21:06:00Z", overwrite=True)
    ok("--overwrite replaces an existing verdict", st["e"]["judge_verdict"] == "unsupported")
    for label, kw in (("empty model", {"model": " ", "prompt_hash": h}),
                      ("non-hex hash", {"model": "m", "prompt_hash": "abc"})):
        try:
            backfill(fg, {"a": "supported"}, judged_at="x", **kw)
            ok(f"refuses {label}", False)
        except SystemExit:
            ok(f"refuses {label}", True)
    ok("label mapping: MISATTRIBUTED -> unsupported, UNREADABLE -> abstain",
       VERDICT_MAP["MISATTRIBUTED"] == "unsupported" and VERDICT_MAP["UNREADABLE"] == "abstain")
    try:
        substrate.guard("claim", {"judge_verdict": "supported", "judge_model": "m", "judge_prompt_hash": h,
                                  "judged_at": "2026-11-19T21:06:00Z"}, op="update")
        ok("the real spine_client guard admits the judge record (YED-451 allowlist)", True)
    except Exception as e:  # noqa: BLE001
        ok(f"the real spine_client guard admits the judge record (YED-451 allowlist): {e}", False)
    print(f"judge_backfill selftest: {sum(results)}/{len(results)} pass")
    return all(results)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--state", help="phase2b_state.json from the judge run (gitignored)")
    ap.add_argument("--hash-file", help="judge_prompt_v2.sha256")
    ap.add_argument("--judge-model", help="model id the judge agents ran on (required, no default)")
    ap.add_argument("--judged-at", help="ISO UTC timestamp for the batch (default: the state file's mtime)")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing judge_verdict")
    ap.add_argument("--apply", action="store_true", help="write (default is a dry run)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if not (a.state and a.hash_file and a.judge_model):
        ap.error("--state, --hash-file and --judge-model are required")
    import substrate
    verdicts = load_verdicts(a.state)
    h = load_hash(a.hash_file)
    judged_at = a.judged_at or _default_judged_at(a.state)
    g = substrate.Graph(not a.apply, substrate.Stats())
    c = backfill(g, verdicts, model=a.judge_model, prompt_hash=h, judged_at=judged_at, overwrite=a.overwrite)
    tag = "" if a.apply else "DRY-RUN "
    print(f"{tag}judge_backfill: {len(verdicts)} verdicts · model={a.judge_model} · prompt={h[:12]}… · "
          f"judged_at={judged_at} · " + " · ".join(f"{k}={v}" for k, v in sorted(c.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
