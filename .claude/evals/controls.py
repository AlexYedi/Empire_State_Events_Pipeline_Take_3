#!/usr/bin/env python3
"""controls.py: materialise + run the judge control set (YED-209 build step 8).

Controls are REAL artifact states Alex labelled, referenced by git blob, so the repo never carries a broken
copy: a negative control is the content that was flagged, a positive control is content he acked as passing.
A seat that cannot tell them apart is not a judge, whatever its agreement rate says.

  controls.py list                     what is in the set
  controls.py materialise --id <id>    write one control to a temp file, print the path
  controls.py run --seat <id> [--model M] [--ids a,b] [--limit N] [--dry-run]
                                       judge each control with one seat and score it against the label

Results are logged with calibration_set:"control" so calibration_stats keeps them out of kappa (they are a
fixed, re-used set: pooling them would inflate a seat's numbers with questions it has already seen).
Exit: 0 ok · 2 usage · 4 budget.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import judge_lib as jl  # noqa: E402

MANIFEST = ".claude/evals/controls/manifest.json"


def load() -> list[dict]:
    return json.load(open(MANIFEST, encoding="utf-8"))["items"]


def materialise(item: dict, into: str) -> str:
    """Write the control's git blob to a file named like the original (the judge sees a realistic path)."""
    blob = subprocess.run(["git", "cat-file", "blob", item["blob"]], capture_output=True)
    if blob.returncode:
        raise SystemExit(f"blob {item['blob']} not found for {item['id']} (was history rewritten?)")
    base = os.path.basename(item["artifact"])
    if base == "SKILL.md":                       # keep the parent dir: skills are identified by it
        d = os.path.join(into, os.path.basename(os.path.dirname(item["artifact"])))
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, base)
    else:
        path = os.path.join(into, base)
    open(path, "wb").write(blob.stdout)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "materialise", "run"])
    ap.add_argument("--id"); ap.add_argument("--ids"); ap.add_argument("--limit", type=int)
    ap.add_argument("--seat", default="openai"); ap.add_argument("--model")
    ap.add_argument("--label-suffix", default=""); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    items = load()
    if a.ids:
        want = set(a.ids.split(","))
        items = [i for i in items if i["id"] in want]
    if a.id:
        items = [i for i in items if i["id"] == a.id]
    if a.limit:
        neg = [i for i in items if i["expect"] == "flag"][: (a.limit + 1) // 2]
        pos = [i for i in items if i["expect"] == "pass"][: a.limit // 2]
        items = neg + pos                        # keep both classes when sampling, or recall is unmeasurable

    if a.cmd == "list":
        for i in items:
            print(f"  {i['expect']:<5} {i['id']:<44} {i['artifact']}")
        print(f"{len(items)} controls ({sum(i['expect'] == 'flag' for i in items)} negative)")
        return 0
    if a.cmd == "materialise":
        if len(items) != 1:
            print("materialise needs exactly one --id", file=sys.stderr); return 2
        d = tempfile.mkdtemp(prefix="judge-control-")
        print(materialise(items[0], d))
        return 0

    seat_cfg = next((s for s in json.load(open(".claude/evals/seats.json"))["seats"] if s["id"] == a.seat), None)
    if not seat_cfg or a.seat == "claude":
        print(f"--seat must be an adapter-backed seat (not '{a.seat}': the Claude seat runs as a subagent)", file=sys.stderr)
        return 2
    model = a.model or seat_cfg.get("model") or ""
    tmp = tempfile.mkdtemp(prefix="judge-controls-")
    res = []
    for i in items:
        path = materialise(i, tmp)
        cmd = [seat_cfg["runner"], "--artifact", path, "--artifact-type", i["artifact_type"],
               "--calibration-set", "control", "--label", f"control-{i['id']}{a.label_suffix}",
               "--context", f"Control item {i['id']} for the judge control set. This is a real historical state of "
                            f"{i['artifact']} from this repo, judged on its own terms. Score it as you would any build artifact."]
        if model:
            cmd += ["--model", model]
        if a.dry_run:
            cmd += ["--dry-run"]
        p = subprocess.run(["bash"] + cmd if cmd[0].endswith(".sh") else cmd, capture_output=True, text=True)
        line = (p.stdout or p.stderr).strip().splitlines()
        got = next((l for l in line if l.startswith("==")), line[-1] if line else "(no output)")
        verdict = "flag" if " (flag)" in got else ("pass" if " (pass)" in got else "?")
        hit = "✓" if verdict == i["expect"] else ("·" if a.dry_run else "✗")
        res.append({"id": i["id"], "expect": i["expect"], "got": verdict, "ok": verdict == i["expect"], "out": got})
        print(f"  {hit} {i['id']:<44} expect {i['expect']:<5} got {verdict:<5} {'' if a.dry_run else got.split('=>')[-1].strip()[:60]}")
    if not a.dry_run:
        scored = [r for r in res if r["got"] in ("pass", "flag")]
        neg = [r for r in scored if r["expect"] == "flag"]
        pos = [r for r in scored if r["expect"] == "pass"]
        rec = sum(r["ok"] for r in neg) / len(neg) if neg else None
        fp = sum(not r["ok"] for r in pos) / len(pos) if pos else None
        print(f"\nseat={a.seat} model={model or 'default'} · scored {len(scored)}/{len(res)} · "
              f"defect recall {rec if rec is None else round(rec, 2)} ({sum(r['ok'] for r in neg)}/{len(neg)}) · "
              f"false-flag rate {fp if fp is None else round(fp, 2)} ({sum(not r['ok'] for r in pos)}/{len(pos)})")
        m, t = jl.spent(seat_cfg.get("provider", a.seat))
        print(f"spend: ${m:.2f} this month, ${t:.2f} lifetime")
    return 0


if __name__ == "__main__":
    sys.exit(main())
