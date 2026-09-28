#!/usr/bin/env python3
"""controls.py: the judge control set (YED-209 step 8; YED-231: runs ONLY when the reviewer's model id changes).

Controls are REAL artifact states Alex labelled, referenced by git blob, so the repo never carries a broken
copy: a negative control is the content that was flagged, a positive control is content he acked as passing.
A reviewer that cannot tell them apart is not a judge. No schedule, no canaries: judge.py prints the trigger when
the model id it is given differs from the last one logged.

  controls.py list                     what is in the set
  controls.py materialise --id <id>    write one control to a temp file, print the path
  controls.py plan [--ids a,b]         materialise every control and print the judge.py command for each
                                       (the reviewer is a subagent, so the parent thread dispatches each run)

Runs are logged with calibration_set:"control" so calibration_stats keeps them out of kappa (a fixed, re-used set).
Exit: 0 ok · 2 usage.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile


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
    ap.add_argument("cmd", choices=["list", "materialise", "plan"])
    ap.add_argument("--id"); ap.add_argument("--ids"); ap.add_argument("--limit", type=int)
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

    tmp = tempfile.mkdtemp(prefix="judge-controls-")
    for i in items:
        path = materialise(i, tmp)
        print(f"# {i['id']}  expect {i['expect']}\n"
              f"python3 .claude/evals/judge.py run --artifact {path} --artifact-type {i['artifact_type']} "
              f"--artifact-blob {i['blob']} --calibration-set control --label control-{i['id']} "
              f"--context \"Control item {i['id']}: a real historical state of {i['artifact']} from this repo, judged on "
              f"its own terms. Score it as you would any build artifact.\"")
    print(f"\n{len(items)} controls. After each --resume, compare final_verdict with the expectation above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
