#!/usr/bin/env python3
"""calibration_stats.py — what each judge seat is actually worth (YED-206).

Raw judge-vs-Alex agreement is the metric the gate used, and it is misleading: if Alex flags 3 of 18
artifacts, a seat that says "pass" to everything scores 83% — which is exactly what the Gemini seat
scored (triage: .claude/notes/gemini-judge-triage-2026-09-19.md). This reports, per seat:

  agreement        raw % vs Alex's verdict          (the old, inflatable number)
  always-pass      what a constant "pass" would score on the SAME rows (the baseline to beat)
  kappa            Cohen's kappa — agreement corrected for chance (0 = no better than guessing)
  flag recall      of the artifacts Alex considers flag-worthy, how many did the seat flag
  flag precision   of the seat's flags, how many Alex agreed with
  flat 1.0         share of runs scoring 1.0 on every criterion (low-information)

kappa is None (printed as "—") when the sample has zero variance: a seat scored only against unanimous
verdicts has no measurable discrimination, and reporting 1.0 there would be the very illusion this file
exists to expose.

TRUTH IS MATCHED ON CONTENT, NOT ON THE FILE NAME (YED-209, 2026-09-19). The first version matched a run to the
nearest ack for the same artifact PATH. A file that was flagged, fixed, and re-judged the same day then had its
correct "pass" scored against the flag on the OLD content, and the trusted Sonnet seat read kappa 0.53 /
recall 0.60 for doing its job. Now:
  * a row carrying `artifact_sha256` is scored ONLY against acks on the same hash (nearest in time);
    an ack on a different hash of the same path is never used, whatever the timestamps say;
  * a legacy row with no hash keeps the time window, but only if git shows NO commit touching that path
    between the ack and the run (any ref). If the file changed in between, the run is left unscored:
    an unscored row is honest, a mis-scored row is not.

Alex's verdict comes from `alex_ack` on ANY seat's row for that artifact (agree -> that row's verdict;
disagree -> its opposite). An artifact is often re-judged after being edited, so a run is matched to the
NEAREST-IN-TIME ack for the same artifact and only within --window days (default 3); its own ack always
wins. Rows with evidence_parity:false or calibration_set in {negative-control, triage-experiment} are
excluded — from BOTH the ground-truth pool and the per-seat scoring.

Usage: python3 .claude/evals/calibration_stats.py [--logs .claude/evals/logs] [--json] [--check]
"""
from __future__ import annotations
import argparse, collections, datetime, functools, glob, json, os, subprocess

EXCLUDE_SETS = {"negative-control", "triage-experiment", "control", "bakeoff"}

# --- null-baseline contract (YED-212, ruled 2026-09-21) ----------------------------------------------------
# A metric that a do-nothing policy scores just as well on is not a standard. "83% Gemini-vs-Alex agreement"
# WAS the always-pass baseline (15/18) on a corpus where 83% of artifacts pass, and the gate's >=80% threshold
# sat BELOW it — so the gate could never fire, for 63 days. Every gating metric now declares its null model and
# must beat it by this margin; anything that doesn't is `unvalidated` and loses the right to auto-accept.
NULL_MARGIN = 0.10      # how far above the do-nothing baseline a metric must sit to count as informative
NULL_MIN_N = 10         # below this, report "insufficient" — never "validated"


def null_check(observed: float | None, baseline: float | None, n: int, values: list | None = None) -> dict:
    """Is this metric doing better than doing nothing? Returns a verdict a caller can act on.

    `values` (optional) enables the zero-variance arm: a source that emits one constant carries no information
    however good the constant looks. That is the shape the Gemini seat had (flat 1.0 on 81% of runs).
    """
    if n < NULL_MIN_N:
        return {"status": "insufficient", "n": n, "detail": f"n={n} < {NULL_MIN_N}"}
    if values is not None and len(set(values)) <= 1:
        return {"status": "unvalidated", "n": n, "reason": "zero_variance",
                "detail": f"every one of {n} observations is {values[0] if values else '?'} — constant output"}
    if observed is None or baseline is None:
        return {"status": "insufficient", "n": n, "detail": "observed or baseline unavailable"}
    margin = round(observed - baseline, 3)
    if margin < NULL_MARGIN:
        return {"status": "unvalidated", "n": n, "reason": "at_or_below_null_baseline", "observed": round(observed, 3),
                "baseline": round(baseline, 3), "margin": margin,
                "detail": f"{observed:.2f} vs do-nothing {baseline:.2f} (+{margin:.2f} < +{NULL_MARGIN})"}
    return {"status": "validated", "n": n, "observed": round(observed, 3), "baseline": round(baseline, 3),
            "margin": margin}


def ack_verdict(ack) -> str | None:
    """'agree'/'disagree' (string or {verdict: ...}) -> the ack word, else None."""
    if isinstance(ack, dict):
        ack = ack.get("verdict")
    if not isinstance(ack, str):
        return None
    a = ack.strip().lower()
    return "agree" if a.startswith("agree") else "disagree" if a.startswith("disagree") else None


def parity(r: dict) -> str:
    """true | false | unknown. ABSENT IS NOT TRUE: 32 Gemini and 47 Claude rows predate the field and were being
    counted as if the seat had been given the spec (YED-212). Unknown rows are reported separately, never
    silently pooled into the number the gate reads."""
    ep = r.get("evidence_parity")
    return "true" if ep is True else "false" if ep is False else "unknown"


def load(logs: str) -> list[dict]:
    rows = []
    for f in sorted(glob.glob(os.path.join(logs, "*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            r["_file"] = os.path.basename(f)
            rows.append(r)
    return fold_acks(rows)


def fold_acks(rows: list[dict]) -> list[dict]:
    """Apply `quorum_ack` rows (written only by judge.py ack, append-only) to their quorum row: the LATEST ack per
    run_id wins. The ack rows themselves stay in the list; they carry no verdict, so every reader skips them."""
    latest: dict[str, dict] = {}
    for r in rows:
        if r.get("record_type") == "quorum_ack" and r.get("run_id"):
            if str(r.get("alex_ack_at") or "") >= str((latest.get(r["run_id"]) or {}).get("alex_ack_at") or ""):
                latest[r["run_id"]] = r
    for r in rows:
        a = latest.get(r.get("run_id")) if r.get("record_type") == "quorum" else None
        if a:
            r["alex_ack"], r["alex_ack_at"] = a.get("alex_ack"), a.get("alex_ack_at")
            if a.get("note"):
                r["alex_ack_note"] = a["note"]
    return rows


def seat_of(r: dict) -> str | None:
    """Normalize a run row to a seat name; quorum records are not a seat."""
    if r.get("record_type") == "quorum":
        return None
    jm = str(r.get("judge_model") or "")
    if not jm or r.get("verdict") not in ("pass", "flag"):
        return None
    for key, name in (("gemini", "gemini"), ("openai", "openai"), ("sonnet", "claude:sonnet"), ("haiku", "claude:haiku"), ("opus", "claude:opus")):
        if key in jm.lower():
            return name
    return jm.split()[0]


def kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Cohen's kappa for two binary raters. UNDEFINED (None) on a zero-variance sample.

    When every item in the sample carries the same label, pe == 1 and kappa is 0/0. Returning 1.0 there
    would report 'perfect agreement corrected for chance' for a seat that has never been tested against a
    single flag — the same illusion of calibration this file exists to expose (it did exactly that for
    claude:opus: 6 unanimous passes -> kappa 1.0). sklearn treats this as undefined; so do we.
    """
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    pe = sum((sum(a == v for a, _ in pairs) / n) * (sum(b == v for _, b in pairs) / n) for v in ("pass", "flag"))
    if pe >= 1:                       # zero variance in at least one rater -> kappa undefined, never 1.0
        return None
    return round((po - pe) / (1 - pe), 3)


SEATS_FILE = ".claude/evals/seats.json"


def compute(rows: list[dict], window: float, keep=lambda seat, r: True,
            strict_parity: bool = True, on_scored=None) -> tuple[dict, dict, collections.Counter]:
    """Per-seat stats. Truth comes from ALL rows; `keep(seat, row)` limits which RUNS are scored (check()'s slice).

    strict_parity=True (check()'s setting) scores only rows with evidence_parity TRUE, and reports how many were
    set aside as unknown. strict_parity=False scores unknown rows too, for the historical view. `on_scored(row)` is
    called for every run that was matched to one of Alex's verdicts.
    """
    a = argparse.Namespace(window=window)

    # 1. every acked row -> (artifact, when, Alex's verdict). Keep them ALL; an artifact re-judged after an
    #    edit has several, and which one applies depends on when the run happened.
    def when(r: dict) -> float:
        ts = str(r.get("timestamp") or "")[:19]
        try:
            return datetime.datetime.fromisoformat(ts).timestamp()
        except ValueError:
            return 0.0

    @functools.lru_cache(maxsize=None)
    def change_times(path: str) -> tuple[float, ...]:
        """Commit times (any ref) that touched `path`. Empty if git is unavailable: the guard then can't fire."""
        try:
            out = subprocess.run(["git", "log", "--all", "--format=%ct", "--", path],
                                 capture_output=True, text=True, timeout=20).stdout
            return tuple(sorted(float(x) for x in out.split()))
        except (OSError, subprocess.SubprocessError, ValueError):
            return ()

    def changed_between(path: str, t1: float, t2: float) -> bool:
        lo, hi = sorted((t1, t2))
        return any(lo < c < hi for c in change_times(path))

    truths: dict[str, list[tuple[float, str, str | None]]] = collections.defaultdict(list)
    for r in rows:
        if r.get("calibration_set") in EXCLUDE_SETS or parity(r) == "false":
            continue          # excluded rows must not seed ground truth either, or an excluded ack
        # NOTE: parity gates how a SEAT is scored, not whether Alex's verdict counts. His ack is a judgement
        # about the artifact; it does not stop being his judgement because one seat lacked the spec. Requiring
        # parity here collapsed the truth pool from 35 artifacts to 1 (caught in test, YED-212).
        ack = ack_verdict(r.get("alex_ack"))   # can be handed to a legitimate run via nearest-ack matching
        art = r.get("artifact")
        if not ack or not art:
            continue
        v = r.get("final_verdict") if r.get("record_type") == "quorum" else r.get("verdict")
        if v not in ("pass", "flag"):
            continue
        truths[art].append((when(r), v if ack == "agree" else ("flag" if v == "pass" else "pass"),
                            r.get("artifact_sha256")))

    def truth_for(r: dict) -> str | None:
        """Own ack first; else the nearest ack for the same artifact inside the window."""
        own = ack_verdict(r.get("alex_ack"))
        if own:
            v = r.get("verdict")
            return v if own == "agree" else ("flag" if v == "pass" else "pass")
        art = r.get("artifact", "")
        cands = truths.get(art)
        if not cands:
            return None
        t, sha = when(r), r.get("artifact_sha256")
        if sha:                                   # content-matched: same hash only, no window needed
            same = [(abs(t - ts), v) for ts, v, h in cands if h == sha]
            if same:
                return min(same, key=lambda x: x[0])[1]
            cands = [c for c in cands if c[2] is None]      # never borrow an ack made on OTHER content
            if not cands:
                return None
        dt, ts, v = min(((abs(t - ts), ts, v) for ts, v, _ in cands), key=lambda x: x[0])
        if dt > a.window * 86400:
            return None
        if t and ts and changed_between(art, t, ts):
            stats["unscored_file_changed"] += 1
            return None
        return v

    stats = collections.Counter()

    # 2. score each seat against that truth
    seats: dict[str, dict] = collections.defaultdict(lambda: {"pairs": [], "flat": 0, "n_runs": 0, "parity_unknown": 0})
    for r in rows:
        seat = seat_of(r)
        if not seat or r.get("calibration_set") in EXCLUDE_SETS:
            continue
        pz = parity(r)
        if pz == "false" or (strict_parity and pz == "unknown"):
            if pz == "unknown":
                seats[seat]["parity_unknown"] += 1      # counted and shown, never silently folded in
            continue
        if not keep(seat, r):
            continue
        s = seats[seat]
        s["n_runs"] += 1
        cs = r.get("criterion_scores") or []
        if r.get("flat_ceiling") is True or (len(cs) == 5 and all(c.get("score") == 1 for c in cs)):
            s["flat"] += 1
        t = truth_for(r)
        if t:
            s["pairs"].append((r["verdict"], t))
            if on_scored:
                on_scored(r)

    out = {}
    for seat, s in sorted(seats.items()):
        p = s["pairs"]
        n = len(p)
        flags_truth = sum(t == "flag" for _, t in p)
        flags_seat = sum(j == "flag" for j, _ in p)
        out[seat] = {
            "runs": s["n_runs"], "scored_against_alex": n,
            "agreement": round(sum(j == t for j, t in p) / n, 3) if n else None,
            "always_pass_baseline": round(sum(t == "pass" for _, t in p) / n, 3) if n else None,
            "kappa": kappa(p),
            "flag_recall": round(sum(j == "flag" and t == "flag" for j, t in p) / flags_truth, 3) if flags_truth else None,
            "flag_precision": round(sum(j == "flag" and t == "flag" for j, t in p) / flags_seat, 3) if flags_seat else None,
            "flat_1.0_rate": round(s["flat"] / s["n_runs"], 3) if s["n_runs"] else None,
            "truth_flags": flags_truth, "seat_flags": flags_seat, "parity_unknown": s["parity_unknown"],
            # the number that matters: does this seat beat a policy of always saying "pass"?
            "null_check": null_check(sum(j == t for j, t in p) / n if n else None,
                                     sum(t == "pass" for _, t in p) / n if n else None, n,
                                     values=[j for j, _ in p] or None),
        }
    return out, truths, stats


def check(rows: list[dict], window: float = 3.0, seats_file: str | None = None) -> dict:
    """Is it time for Alex to revisit the voting seat? REPORTS ONLY: it never writes seats.json (YED-231 §4.5).

    The voter's numbers come from its last 20 prospective, parity-true runs since the seat's `since` (its current
    prompt/rubric regime). `new_acks` counts those of its runs, dated on/after `revisit.since`, that have Alex's
    verdict. `revisit_due` when new_acks >= min_new_acks AND (kappa < kappa_floor on n >= n_min, or flag recall <
    recall_floor). `n_from_escalation` shows how much of the truth set came from escalations (the hard cases): a
    skewed sample is visible, not hidden (pre-mortem 1). The banner is the mechanism; Alex's edit is the decision.
    """
    doc = json.load(open(seats_file or SEATS_FILE, encoding="utf-8"))
    rv = doc.get("revisit") or {}
    since = str(rv.get("since") or "")
    voters = [s for s in doc.get("seats", []) if s.get("role") == "voting"]
    if not voters:
        return {"status": "no_voting_seat", "detail": "no seat has role voting in seats.json", "candidate": rv.get("candidate")}
    seat = voters[0]
    name, regime = seat["seat_name"], str(seat.get("since") or "")
    mine = [r for r in rows if seat_of(r) == name and r.get("calibration_set") == "prospective"
            and str(r.get("timestamp") or "") >= regime]
    recent = {id(r) for r in sorted(mine, key=lambda r: str(r.get("timestamp") or ""))[-20:]}
    new_ids = {id(r) for r in mine if str(r.get("timestamp") or "") >= since}
    scored: list[dict] = []
    m = compute(rows, window, keep=lambda s_, r: s_ == name and id(r) in recent, on_scored=scored.append)[0].get(name, {})
    fresh: list[dict] = []
    compute(rows, window, keep=lambda s_, r: s_ == name and id(r) in new_ids, on_scored=fresh.append)
    n_new = len(fresh)
    esc_runs = {s_.get("run_id") for q in rows if q.get("record_type") == "quorum"
                and q.get("resolution") in ("escalated", "failsafe_flag")
                for s_ in (q.get("seats") or []) if isinstance(s_, dict) and s_.get("id") == seat["id"]}
    n, kappa_, recall = m.get("scored_against_alex", 0), m.get("kappa"), m.get("flag_recall")
    k_floor, r_floor = float(rv.get("kappa_floor", 0.40)), float(rv.get("recall_floor", 0.50))
    n_min, min_new = int(rv.get("n_min", 15)), int(rv.get("min_new_acks", 5))
    why = []
    if n >= n_min and kappa_ is not None and kappa_ < k_floor:
        why.append(f"kappa {kappa_:.2f} < {k_floor} on n={n}")
    if recall is not None and recall < r_floor:
        why.append(f"flag recall {recall:.2f} < {r_floor} on {m.get('truth_flags', 0)} real flags")
    status = "revisit_due" if (n_new >= min_new and why) else "not_due"
    return {"status": status, "seat": seat["id"], "seat_name": name, "since": since, "new_acks": n_new,
            "min_new_acks": min_new, "n": n, "kappa": kappa_, "flag_recall": recall,
            "truth_flags": m.get("truth_flags", 0), "null_check": m.get("null_check"),
            "n_from_escalation": sum(1 for r in scored if r.get("run_id") in esc_runs),
            "reasons": why, "candidate": rv.get("candidate")}


def banner(c: dict) -> str:
    """One line to print wherever the judge runs; empty unless a revisit is due."""
    if c.get("status") != "revisit_due":
        return ""
    cand = c.get("candidate") or {}
    return (f"⚠️  REVISIT the voting seat ({c['seat_name']}): {'; '.join(c['reasons'])} · {c['new_acks']} new acks since "
            f"{c['since']} · {c['n_from_escalation']}/{c['n']} of the truth set came from escalations · "
            f"null-model {(c.get('null_check') or {}).get('status')}. Candidate: {cand.get('seat')} "
            f"({cand.get('model')}). The decision is a one-line role edit in .claude/evals/seats.json.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=".claude/evals/logs")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="the voting seat's numbers vs the revisit floors in seats.json (reports; never writes)")
    ap.add_argument("--window", type=float, default=3.0, help="max days between a run and the ack it is scored against")
    a = ap.parse_args()
    rows = load(a.logs)
    if a.check:
        c = check(rows, a.window)
        if a.json:
            print(json.dumps(c, indent=1)); return 0
        if c["status"] == "no_voting_seat":
            print(f"no voting seat: {c['detail']}"); return 0
        nc = c.get("null_check") or {}
        print(f"{c['seat']} ({c['seat_name']}) voting · n={c['n']} kappa={c['kappa']} recall={c['flag_recall']} "
              f"(real flags {c['truth_flags']}) · from escalations {c['n_from_escalation']}/{c['n']} · "
              f"new acks since {c['since']}: {c['new_acks']}/{c['min_new_acks']} · null-model {nc.get('status')} "
              f"— {nc.get('detail', 'beats the do-nothing baseline')}")
        print(f"revisit: {c['status']}" + (f" ({'; '.join(c['reasons'])})" if c["reasons"] else ""))
        if banner(c):
            print(banner(c))
        return 0
    out, truths, stats = compute(rows, a.window)
    acks = [v for c in truths.values() for _, v, _ in c]
    if a.json:
        print(json.dumps({"alex_acked_runs": len(acks), "artifacts": len(truths), "window_days": a.window,
                          "unscored_file_changed": stats["unscored_file_changed"], "seats": out}, indent=1))
        return 0
    print(f"Alex-acked runs: {len(acks)} over {len(truths)} artifacts  (flag: {sum(v == 'flag' for v in acks)})"
          f"  · match window: ±{a.window:g}d  · left unscored because the file changed between ack and run: "
          f"{stats['unscored_file_changed']}\n")
    hdr = f"{'seat':<15}{'runs':>5}{'vs Alex':>8}{'agree':>7}{'base':>7}{'kappa':>7}{'recall':>8}{'prec':>7}{'flat1.0':>9}"
    print(hdr + "\n" + "-" * len(hdr))
    for seat, m in out.items():
        f = lambda v: "  —  " if v is None else f"{v:.2f}"
        print(f"{seat:<15}{m['runs']:>5}{m['scored_against_alex']:>8}{f(m['agreement']):>7}{f(m['always_pass_baseline']):>7}"
              f"{f(m['kappa']):>7}{f(m['flag_recall']):>8}{f(m['flag_precision']):>7}{f(m['flat_1.0_rate']):>9}")
    print("\nRead: agreement ABOVE baseline is the real signal; kappa ≈ 0 means the seat adds nothing over "
          "always-passing; flag recall is what a gate actually needs; a high flat-1.0 rate means low information.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
