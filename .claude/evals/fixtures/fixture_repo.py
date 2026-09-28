"""fixture_repo.py: test-only loader. Materialises judge_range_fixture.json as a throwaway git repo so the judge
bundle tests never pin a commit of THIS repo's history (a history rewrite changes every sha).

    fx = build("/tmp/x")   # -> {"root", "base", "head", "small", "range", "small_range", "spec_note", "log_row"}

Three commits: base -> head is the multi-file range (7 judgeable files + 5 telemetry rows, > 60k chars in full);
head -> small is a one-file range. The judge code runs unchanged against it, with the repo as its working directory.
"""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "judge_range_fixture.json")


def _pad(n: int) -> list[str]:
    return [f"_PAD_{i:04d} = 'synthetic filler line, here only so this stand-in trips the bundle size rule ({i:04d})'"
            for i in range(n)]


def _expand(lines: list[str]) -> str:
    out: list[str] = []
    for l in lines:
        if l.startswith("@@PAD ") and l.endswith("@@"):
            out += _pad(int(l[6:-2]))
        else:
            out.append(l)
    return "\n".join(out) + "\n"


def build(root: str) -> dict:
    fx = json.load(open(FIXTURE, encoding="utf-8"))

    def g(*a: str) -> str:
        return subprocess.run(["git", "-C", root, "-c", "user.email=fixture", "-c", "user.name=fixture",
                               "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *a],
                              capture_output=True, text=True, check=True).stdout.strip()

    os.makedirs(root, exist_ok=True)
    g("init", "-q")
    shas = {}
    for c in fx["commits"]:
        for path, lines in c["files"].items():
            p = os.path.join(root, path)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(_expand(lines))
        g("add", "-A")
        g("commit", "-qm", f"fixture: {c['tag']}")
        shas[c["tag"]] = g("rev-parse", "HEAD")
    return {"root": root, **shas, "range": f"{shas['base']}..{shas['head']}",
            "small_range": f"{shas['head']}..{shas['small']}", "spec_note": fx["spec_note"],
            "log_row": fx["regression_log_row"]}
