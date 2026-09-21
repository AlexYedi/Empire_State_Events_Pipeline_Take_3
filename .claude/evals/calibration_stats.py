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

Usage: python3 .claude/evals/calibration_stats.py [--logs .claude/evals/logs] [--json]
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


ORDER = ["shadow", "advisory", "voting"]
SEATS_FILE = ".claude/evals/seats.json"
CANARY_STATE = ".claude/evals/controls/state.json"
CANARY_STALE_DAYS = 14


def compute(rows: list[dict], window: float, keep=lambda seat, r: True,
            strict_parity: bool = True) -> tuple[dict, dict, collections.Counter]:
    """Per-seat stats. Truth comes from ALL rows; `keep(seat, row)` limits which RUNS are scored (the gate's slice).

    strict_parity=True (the gate's setting) scores only rows with evidence_parity TRUE, and reports how many were
    set aside as unknown. strict_parity=False scores unknown rows too, for the historical view.
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


def gate(rows: list[dict], window: float) -> dict:
    """Effective status per configured seat = its configured status, lowered ONE rung if a demotion rule fires.

    Promotion is never automatic (Alex edits seats.json). Demotion is, and it applies to every seat, the trusted
    one included: exempting the anchor seat is how a blind spot survives. Rules read the last 20 PROSPECTIVE runs
    since the seat's `since` date (its current prompt/rubric regime; older behaviour is not held against it).
    Each rule has a minimum sample so three unlucky runs can't demote a seat.
    """
    cfg = json.load(open(SEATS_FILE, encoding="utf-8"))["seats"] if os.path.exists(SEATS_FILE) else []
    canary = json.load(open(CANARY_STATE, encoding="utf-8")) if os.path.exists(CANARY_STATE) else {}
    res = {}
    for seat in cfg:
        name, since = seat["seat_name"], str(seat.get("since") or "")
        mine = [r for r in rows if seat_of(r) == name and r.get("calibration_set") == "prospective"
                and str(r.get("timestamp") or "") >= since]
        recent = {id(r) for r in sorted(mine, key=lambda r: str(r.get("timestamp") or ""))[-20:]}
        m = compute(rows, window, keep=lambda s_, r: s_ == name and id(r) in recent)[0].get(name, {})
        n_runs, n = m.get("runs", 0), m.get("scored_against_alex", 0)
        why = []
        if n_runs >= 10 and (m.get("flat_1.0_rate") or 0) >= 0.30:
            why.append(f"flat-1.0 rate {m['flat_1.0_rate']:.2f} >= 0.30 over {n_runs} runs")
        if m.get("truth_flags", 0) >= 4 and (m.get("flag_recall") or 0) < 0.50:
            why.append(f"flag recall {m['flag_recall']:.2f} < 0.50 on {m['truth_flags']} real flags")
        if m.get("seat_flags", 0) >= 5 and (m.get("flag_precision") or 0) < 0.40:
            why.append(f"flag precision {m['flag_precision']:.2f} < 0.40 on {m['seat_flags']} seat flags (over-flagging)")
        if n >= 15 and m.get("kappa") is not None and m["kappa"] < 0.40:
            why.append(f"kappa {m['kappa']:.2f} < 0.40 on n={n}")
        # --- canary rules (YED-209 step 8). A seat that cannot tell a known-bad artifact from a known-good one
        # is not a judge, whatever its agreement rate says. Absence of a canary is NOT a failure (it would demote
        # everything the day this shipped) — it is reported as `canary: never run` so the quorum can say so.
        c = canary.get(seat["id"]) or {}
        if c:
            if (c.get("consecutive_failures") or 0) >= 2:
                why.append(f"{c['consecutive_failures']} consecutive canary failures (last {c.get('last_run', '?')[:10]})")
            last_model = c.get("model_resolved") or ""
            cur_model = seat.get("model") or ""
            if c.get("status") == "pass" and cur_model and last_model and cur_model not in last_model:
                why.append(f"model changed to {cur_model} since the last green canary ({last_model}): re-run canaries")
            try:
                age = (datetime.datetime.now(datetime.timezone.utc)
                       - datetime.datetime.fromisoformat(c["last_run"].replace("Z", "+00:00"))).days
                if age > CANARY_STALE_DAYS and ORDER.index(seat.get("status", "shadow")) >= 2:
                    why.append(f"canary {age}d old (> {CANARY_STALE_DAYS}d) for a voting seat")
            except (KeyError, ValueError):
                pass
        # the null-baseline rule (YED-212): a seat no better than always-saying-pass cannot auto-accept
        nc = m.get("null_check") or {}
        if nc.get("status") == "unvalidated":
            why.append(f"null-baseline: {nc.get('detail')}")
        conf = seat.get("status", "shadow")
        eff = ORDER[max(0, ORDER.index(conf) - 1)] if why else conf
        ready = (n >= 25 and m.get("truth_flags", 0) >= 8 and (m.get("kappa") or 0) >= 0.60 and (m.get("flag_recall") or 0) >= 0.70
                 and (m.get("flag_precision") or 0) >= 0.60 and (m.get("flat_1.0_rate") or 0) < 0.20
                 and (m.get("agreement") or 0) >= (m.get("always_pass_baseline") or 0) + 0.10)
        res[seat["id"]] = {"seat_name": name, "configured": conf, "effective": eff, "demoted_because": why,
                           "null_check": nc,
                           "meets_voting_bar": ready, "window": m,
                           "canary": ({"status": c.get("status"), "last_run": c.get("last_run"),
                                       "consecutive_failures": c.get("consecutive_failures", 0)}
                                      if c else {"status": "never run"})}
    # --- last-voting-seat guard (Alex's ruling 2026-09-21) ---------------------------------------------------
    # If applying the demotions would leave NO voting seat, the demotion of the final one is recorded but not
    # applied. Rationale: with no trusted seat every run escalates, and a gate that cries wolf gets overridden —
    # the failure mode this whole layer exists to prevent. Alex confirms it by hand in seats.json.
    if not any(v["effective"] == "voting" for v in res.values()):
        survivors = [k for k, v in res.items() if v["configured"] == "voting" and v["demoted_because"]]
        if survivors:
            pick = min(survivors, key=lambda k: len(res[k]["demoted_because"]))   # the least-broken one
            res[pick]["effective"] = "voting"
            res[pick]["last_voting_seat_held"] = True
            res[pick]["demotion_pending_confirmation"] = res[pick]["demoted_because"]
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=".claude/evals/logs")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true", help="effective status per configured seat (auto-demotion)")
    ap.add_argument("--window", type=float, default=3.0, help="max days between a run and the ack it is scored against")
    a = ap.parse_args()
    rows = load(a.logs)
    if a.gate:
        g = gate(rows, a.window)
        if a.json:
            print(json.dumps(g, indent=1)); return 0
        for sid, x in g.items():
            w = x["window"]
            print(f"{sid:<8} configured={x['configured']:<9} effective={x['effective']:<9} "
                  f"runs={w.get('runs', 0)} scored={w.get('scored_against_alex', 0)} kappa={w.get('kappa')} "
                  f"recall={w.get('flag_recall')} flat={w.get('flat_1.0_rate')}  voting-bar-met={x['meets_voting_bar']}")
            for y in x["demoted_because"]:
                print(f"           DEMOTED: {y}")
            nc = x.get("null_check") or {}
            if nc:
                print(f"           null-model: {nc.get('status')} — {nc.get('detail', 'beats the do-nothing baseline')}")
        held = [k for k, v in g.items() if v.get("last_voting_seat_held")]
        if held:
            print(f"\n⚠️  {', '.join(held)} would have been demoted, but it is the LAST voting seat. Demotion is")
            print("    RECORDED, NOT APPLIED, pending Alex's confirmation (YED-212 ruling 2026-09-21): auto-demoting")
            print("    the last seat makes every run escalate, and the pressure to override that defeats the gate.")
            print("    Confirm by setting the seat's status in seats.json, or fix the cause and re-run.")
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
