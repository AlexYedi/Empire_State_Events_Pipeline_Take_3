#!/usr/bin/env python3
"""test_bundle_multifile.py: bundle_version 3 — range/files bundles + the whole-bundle quote haystack (YED-231 §8).

Offline and free: builds bundles from git history and replays logged quotes; no seat is called.
The fixture range is PR #139 (c607c08..42602e4): 7 code/doc files + 5 telemetry .jsonl rows, ~78k chars in full.
Run from the repo root: python3 .claude/evals/test_bundle_multifile.py
"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge_lib as jl

ROOT = os.getcwd()
SYS, RUB = ".claude/evals/prompts/judge-system-v2.md", ".claude/evals/rubrics/build-quality-v6.md"
RANGE = "c607c08..42602e4"
SPEC_NOTE = ".claude/notes/stop-gate-per-turn-2026-09-27.md"      # the spec the 09-27 deep-read-gate run was given
ok = n = 0


def ck(name, cond, detail=""):
    global ok, n
    n += 1; ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"   {detail}" if detail and not cond else ""))


if subprocess.run(["git", "cat-file", "-e", "42602e4^{commit}"], capture_output=True).returncode:
    print("  ✗ PR #139 range not reachable — run `git fetch origin` first"); sys.exit(1)

b1 = jl.build_bundle(None, "hook", SYS, RUB, spec_files=[".claude/evals/test_gate_in_progress.sh", SPEC_NOTE], rng=RANGE)
b2 = jl.build_bundle(None, "hook", SYS, RUB, spec_files=[".claude/evals/test_gate_in_progress.sh", SPEC_NOTE], rng=RANGE)
paths = [f["path"] for f in b1["files"]]
WANT = {".claude/evals/test_gate_in_progress.sh", ".claude/hooks/deep-read-gate.sh", ".claude/hooks/gate-sweep-sessionstart.sh",
        ".claude/hooks/substrate-gate.sh", ".claude/scripts/spine_client.py", ".claude/settings.json",
        ".claude/skills/rigor-review/SKILL.md"}
ck("range: the 7 code/doc files are in the bundle", set(paths) == WANT, str(paths))
ck("range: none of the 5 telemetry .jsonl rows is", not any(p.endswith(".jsonl") for p in paths))
ck("range: bundle_version 3, artifact id names the range", b1["bundle_version"] == 3 and b1["artifact"] == "range:c607c08..42602e4")
ck("range: artifact_sha256 is stable across two builds", b1["artifact_sha256"] == b2["artifact_sha256"])
ck("range: the whole bundle is byte-stable too", b1["bundle_sha256"] == b2["bundle_sha256"])
ck("range: the diff is carried as a WHAT CHANGED section", "===== WHAT CHANGED" in b1["text"])
ck("range: refs are checked as of HEAD (run-canaries.sh existed at 42602e4, so it is not dangling there)",
   b1["has_dangling"] is False and b1["dangling_refs"] == [], str(b1["dangling_refs"]))
ck("range: each file under its own FILE header", all(f"===== FILE: {p} (" in b1["text"] for p in WANT))

# the 60k rule: PR #139 is ~78k chars in full, so files > 400 lines go as hunks (and only those)
modes = {f["path"]: f["mode"] for f in b1["files"]}
ck("size rule: > 60k chars flips bundle_mode to hunks", b1["bundle_mode"] == "hunks")
ck("size rule: only the > 400-line file is hunked", modes[".claude/scripts/spine_client.py"] == "hunks"
   and all(m == "full" for p, m in modes.items() if p != ".claude/scripts/spine_client.py"), str(modes))
small = jl.build_bundle(None, "ref", SYS, RUB, rng="54fa9fc..071fff8")
ck("size rule: a small range stays full", small["bundle_mode"] == "full" and small["files"][0]["mode"] == "full")

hay = jl.bundle_haystack(b1)
f2 = next(s["text"] for s in b1["sources"] if s["label"] == paths[1])
line2 = next(l for l in f2.splitlines()[5:] if len(l.strip()) > 25)
q = jl.verify_quotes([{"quote": line2}], hay, "hook")
ck("quote from file 2 verifies, and says where", q["unverified"] == 0 and q["matched_in"] == [paths[1]], str(q["matched_in"]))
q = jl.verify_quotes([{"quote": "the stop gate now fails open when the ledger is unreadable, per the spec"}], hay, "hook")
ck("a fabricated quote still fails", q["unverified"] == 1 and q["matched_in"] == [None])

# the deep-read-gate regression (09-27): three CORRECT quotes (two from the spec note, one from spine_client.py as it
# stood before this range changed it) were stripped as fabricated because the haystack was one file; that removed the only voting seat.
row = [json.loads(l) for l in open(".claude/evals/logs/2026-09-27-deep-read-gate-sonnet-deep-read-gate.jsonl")][-1]
stripped = [d for d in row["defects"] if any(str(d.get("quote") or "").startswith(u[:60]) for u in row["quote_check"]["unverified_quotes"])]
ck("regression fixture: the 3 stripped quotes are recovered from the log", len(stripped) == 3, str(len(stripped)))
old = jl.verify_quotes(stripped, open(".claude/hooks/deep-read-gate.sh").read(), "hook")
ck("regression: against the old one-file haystack they fail (reproduced)", old["unverified"] == 3)
new = jl.verify_quotes(stripped, hay, "hook")
ck("regression: against the whole bundle all 3 verify", new["unverified"] == 0, str(new["unverified_quotes"]))
ck("regression: two matched in the spec note, one in the sibling file's removed lines (WHAT CHANGED)",
   sorted(new["matched_in"]) == sorted([SPEC_NOTE, SPEC_NOTE, "diff (removed side)"]), str(new["matched_in"]))
ck("regression: the whole row now clears the 30% bar", not jl.verify_quotes(row["defects"], hay, "hook")["evidence_unverified"])

# single-file bundles: text unchanged in shape; spec text joins the haystack
one = jl.build_bundle(".claude/hooks/deep-read-gate.sh", "hook", SYS, RUB, spec_files=[SPEC_NOTE])
ck("single-file: bundle_version 3, ARTIFACT CONTENT layout kept", one["bundle_version"] == 3 and "===== ARTIFACT CONTENT" in one["text"]
   and one["artifact"] == ".claude/hooks/deep-read-gate.sh")
ck("single-file: a spec quote now verifies", jl.verify_quotes(stripped[:1], jl.bundle_haystack(one), "hook")["unverified"] == 0)

# --files: named files on disk, same haystack rule
fb = jl.build_bundle(None, "code", SYS, RUB, files=[".claude/evals/judge_lib.py", ".claude/hooks/seat-log.py"])
ck("files: id is files:<n>@<sha12>", fb["artifact"] == f"files:2@{fb['artifact_sha256'][:12]}" and fb["bundle_kind"] == "files")
ck("files: slug is filename-safe", "/" not in jl.slug_for(fb["artifact"]) and ":" not in jl.slug_for(fb["artifact"]))

# privacy: a range whose change includes a force-added, ignored path is refused with exit 3 (nothing written)
with tempfile.TemporaryDirectory() as d:
    g = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, check=True)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    open(os.path.join(d, ".gitignore"), "w").write("private.md\n")
    g("add", ".gitignore"); g("commit", "-qm", "base")
    open(os.path.join(d, "ok.md"), "w").write("fine\n")
    open(os.path.join(d, "private.md"), "w").write("do not send\n")
    g("add", "ok.md"); g("add", "-f", "private.md"); g("commit", "-qm", "leak")
    out = os.path.join(d, "b.json")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    p = subprocess.run(["python3", os.path.join(ROOT, ".claude/evals/judge_lib.py"), "bundle", "--range", "HEAD~1..HEAD",
                        "--artifact-type", "ref", "--system", os.path.join(ROOT, SYS), "--rubric", os.path.join(ROOT, RUB),
                        "--out", out], cwd=d, env=env, capture_output=True, text=True)
    ck("privacy: a range containing a gitignored path is refused (exit 3)", p.returncode == 3 and "PRIVACY GUARD" in p.stderr,
       f"rc={p.returncode} {p.stderr.strip()[:120]}")
    ck("privacy: ...and no bundle is written", not os.path.exists(out))

print(f"{ok}/{n} multi-file bundle cases pass")
sys.exit(0 if ok == n else 1)
