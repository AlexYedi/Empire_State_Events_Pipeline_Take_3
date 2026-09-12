#!/usr/bin/env python3
"""
build_graph.py — builds the derived system graph over the repo's own build artifacts.

Spec: docs/adr/ADR-8-system-graph-drift-router.md

The graph is a ROUTER, not a detector: it answers "adjacent-to" and "absent", never "these
contradict". It is a DERIVED CACHE of the repo — never hand-edited, rebuilt from scratch on every
trigger. System of record is the repo itself (working tree + git). Storage is gitignored
`.claude/.state/system-graph/`; the committed artifact (from Increment 3) is the findings ledger,
not this cache.

Stdlib only — no dependencies, no env, no network. That is deliberate: it must run in
Dock-launched sessions that lack `.env` and in fresh worktrees, so the trigger is never
conditional (ADR-8 D1/D6).

SCOPE — Increment 1 (ADR-8 §Increments). Per ADR-8 D7 ("no node or edge type without a consumer
query in the same increment"), this builds `artifact` nodes and `references` edges — and NOTHING
else, because `dangling-ref` is the only check in this increment and `references` is the only
thing it reads. Judge-log ingestion, the findings ledger and `co_changed` arrive in Increments 2-3
with their consumers; they are omitted on purpose, not left as stubs.

This claim was FALSE when first written (2026-09-11) and is corrected here (2026-09-12). The first
cut also emitted `cites_adr`, `tracked_by`, `recalls`, `dispatches`, `orchestrates` and `spec_for`
edges plus `adr`/`linear_issue`/`memory` stub nodes, none of which anything read — a D7 violation
shipped underneath a docstring asserting D7 compliance. The build-quality judge caught it
unprompted; see ADR-8 §Amendment 2. If you add an edge type here, add its consumer in the same
change or do not add it.

Usage:
  build_graph.py                     rebuild the cache (default)
  build_graph.py --check dangling-ref   rebuild, then print <=5 actionable dangling refs
  build_graph.py --verify            rebuild, then assert faithfulness vs check-refs.sh
  build_graph.py --stats             rebuild, then print the baseline counts
  build_graph.py --selftest          extractor regression cases + check-refs.sh agreement

Exit 0 always (advisory; consumers read meta.json).
"""
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import time

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
OUT_DIR = os.path.join(ROOT, ".claude", ".state", "system-graph")
EXTRACTOR_VERSION = "1"

# Artifact roots and exclusions (ADR-8 §Schema → Node types). These are RUN OUTPUT, not build
# surface: per-run logs, generated artifacts, the cache itself, and sibling worktrees.
# Written as segments, assembled below, deliberately: spelled as literal paths they read to any
# path extractor — this one included — as references to files that need not exist, and a directory
# named here is by definition one we do not expect to find.
INCLUDE_EXT = {".md", ".sh", ".py", ".sql"}
EXCLUDE_PARTS = tuple(
    os.path.join(".claude", *parts)
    for parts in (("evals", "logs"), ("artifacts",), (".state",), ("worktrees",))
)

# ---------------------------------------------------------------------------
# check-refs.sh skip rules, inherited VERBATIM (ADR-8 D2: "same conservative skip rules").
# The whole non-whitespace run around `.claude/` (or `docs/`) is inspected first, so the filters
# can see special chars a narrow path charset would truncate away. Err toward under-flagging.
RUN_RE = re.compile(r"[^\s]*(?:\.claude/|docs/)[^\s]*")
TRAILING_MARKUP_RE = re.compile(r"[.,;:)`\"']+$")
# Template / regex / alternation: the path charset stops at `{ ( | [ \ $ %`, leaving a truncated
# prefix that can never exist (`evolution-log-{slug}.md`, `ADR-\d+`, `keyterms.(json|md)`). The
# delimiter is captured as PART of the match so it can be judged per match — the first cut dropped
# the whole whitespace-run, which silently swallowed real references sharing that run (judge D4).
STRICT_PATH_RE = re.compile(r"(?:~/|\./)?(?:\.claude|docs)/[A-Za-z0-9._@/-]+[{(|\[\\$%]?")
# The discriminator is whether the charset stopped MID-TOKEN: a template leaves a dangling
# separator before the delimiter (`keyterms.`+`(`, `skills/`+`{`, `ADR-`+`\`), a complete path does
# not (`real.md`+`(`). Prose `(see .claude/<file>.md)` is untouched either way — `)` is not a
# delimiter, it is trailing markup.
TRUNCATED_RE = re.compile(r"[._/-][{(|\[\\$%]$")
DELIM_TAIL_RE = re.compile(r"[{(|\[\\$%]$")

HISTORICAL_RE = re.compile(r"retired|former|superseded|tombstoned|vanished|deleted", re.I)
YED_TOKEN_RE = re.compile(r"\bYED-(\d+)\b")


def should_skip_run(run: str) -> bool:
    """check-refs.sh Pass-1 filters, verbatim."""
    if "://" in run or run.startswith("http"):
        return True  # path embedded in a URL
    if "*" in run or "<" in run or ">" in run:
        return True  # glob or <placeholder>
    if "…" in run or "..." in run:
        return True  # ellipsis-elided illustrative path
    return False


def is_prose_pair(path: str) -> bool:
    """`docs/` is a real English word, so "optional docs/tools" reads as a path to the charset.
    Require a `docs/` match to look like a path: an extension, or a deeper directory. Applies ONLY
    to the root this extractor added beyond check-refs.sh, so the shared rules stay identical."""
    p = path.lstrip("~./")
    if not p.startswith("docs/"):
        return False
    tail = p[len("docs/"):]
    return "/" not in tail and "." not in tail


def extract_paths(text: str):
    """Yield (path, line_no) for every clean, path-shaped reference. Mirrors check-refs.sh."""
    for line_no, line in enumerate(text.splitlines(), 1):
        for run in RUN_RE.findall(line):
            if should_skip_run(run):
                continue
            for m in STRICT_PATH_RE.findall(run):
                if TRUNCATED_RE.search(m):
                    continue                  # template/regex literal — drop THIS match only
                path = TRAILING_MARKUP_RE.sub("", DELIM_TAIL_RE.sub("", m))
                if path and not is_prose_pair(path):
                    yield path, line_no


def sentence_around(lines, line_no: int, needle: str) -> str:
    """The prose context that classifies a reference. Window is the line PLUS its neighbours, not
    the line alone: markdown hard-wraps mid-sentence, so "…plans that had vanished from disk
    (`pathA`, `pathB`)" puts the word that excuses pathB two lines above pathB itself. Scoped to the
    blank-line-delimited paragraph so it never reaches into an unrelated bullet."""
    i = line_no - 1
    start = i
    while start > 0 and lines[start - 1].strip():
        start -= 1
        if i - start >= 3:
            break
    end = i
    while end + 1 < len(lines) and lines[end + 1].strip():
        end += 1
        if end - i >= 3:
            break
    return " ".join(lines[start:end + 1])


# ---------------------------------------------------------------------------
def git(*args):
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30
        ).stdout.strip()
    except Exception:
        return ""


def gitignored(paths):
    """Batch-classify paths as gitignored via `git check-ignore --stdin` (no deps)."""
    if not paths:
        return set()
    try:
        p = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=ROOT, input="\n".join(paths), capture_output=True, text=True, timeout=30,
        )
        return {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}
    except Exception:
        return set()


def subtype_for(rel: str) -> str:
    p = rel.replace(os.sep, "/")
    if p in ("CLAUDE.md", "WORKFLOWS.md", ".claude/WORKFLOWS.md"):
        return "policy"
    if re.match(r"docs/adr/ADR-\d+", p):
        return "adr"
    if p.startswith(".claude/skills/"):
        return "skill" if p.endswith("/SKILL.md") else "skill-ref"
    if p.startswith(".claude/commands/"):
        return "command"
    if p.startswith(".claude/agents/"):
        return "agent"
    if p.startswith(".claude/hooks/"):
        return "hook"
    if p.startswith(".claude/scripts/"):
        return "script"
    if p.startswith(".claude/references/"):
        return "reference"
    if p.startswith(".claude/evals/rubrics/"):
        return "rubric"
    if p.startswith(".claude/evals/prompts/"):
        return "prompt"
    if p.startswith(".claude/notes/"):
        return "note"
    if p.startswith(".claude/proposals/"):
        return "proposal"
    return "doc"


def walk_artifacts():
    rels = []
    for base in (".claude", "docs"):
        base_abs = os.path.join(ROOT, base)
        if not os.path.isdir(base_abs):
            continue
        for dirpath, dirnames, filenames in os.walk(base_abs):
            rel_dir = os.path.relpath(dirpath, ROOT)
            if any(rel_dir == x or rel_dir.startswith(x + os.sep) for x in EXCLUDE_PARTS):
                dirnames[:] = []
                continue
            for fn in filenames:
                if os.path.splitext(fn)[1] in INCLUDE_EXT:
                    rels.append(os.path.relpath(os.path.join(dirpath, fn), ROOT))
    if os.path.isfile(os.path.join(ROOT, "CLAUDE.md")):
        rels.append("CLAUDE.md")
    return sorted(set(r.replace(os.sep, "/") for r in rels))
def adr_status(text: str):
    """The whole Status LINE, not its first word. Two reasons, both found the hard way: the first
    word is often a bold marker (`**Accepted`), which the old word-capture missed entirely; and an
    ADR can be partially accepted ("Accepted for Increment 1; Increments 2-3 remain Proposed"),
    so any mention of Proposed still means some paths it names are deliberately unbuilt."""
    m = re.search(r"^\s*[-*]?\s*\*\*Status:\*\*\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
def build():
    rels = walk_artifacts()
    nodes, edges = {}, []
    texts = {}

    # --- Step 1: artifact nodes -------------------------------------------------
    # Fields are limited to what Increment 1 CONSUMES (ADR-8 D7). `last_commit_sha`/`last_commit_at`
    # were removed after the judge flagged them: nothing in this increment read them, and producing
    # them spawned one `git log` subprocess PER ARTIFACT (244 of them), which is what put the
    # rebuild at ~4-5s against the ADR's <2s target. They return in Increment 2 with `judge-stale`,
    # the check that actually needs them — batched into a single git call.
    for rel in rels:
        abs_p = os.path.join(ROOT, rel)
        try:
            raw = open(abs_p, "rb").read()
        except OSError:
            continue
        texts[rel] = raw.decode("utf-8", "replace")
        nodes[rel] = {
            "id": rel, "type": "artifact", "subtype": subtype_for(rel), "exists": True,
            "content_sha": hashlib.sha1(raw).hexdigest(),
        }

    # --- Step 2: reference edges + their classification --------------------------
    # `references` is the ONLY edge type built, because `dangling-ref` is the only check in this
    # increment and the only thing that reads it. cites_adr / tracked_by / recalls / dispatches /
    # orchestrates / spec_for, and the adr/linear/memory stub nodes, were all built here and
    # consumed by NOTHING — a D7 violation shipped while this docstring claimed D7 was honored.
    # Deleted rather than commented out: they belong to Increments 2-3 beside their queries.
    pending = []  # (src, path, line_no, classification-context)
    for rel, text in texts.items():
        lines = text.splitlines()
        for path, line_no in extract_paths(text):
            pending.append((rel, path, line_no, sentence_around(lines, line_no, path)))

    probe_rel = sorted({p for _, p, _, _ in pending if not p.startswith("~/")})
    ignored = gitignored(probe_rel)
    # ADR status is read once per ADR (for the `proposed` class), not re-parsed per reference.
    adr_proposed = {
        rel: "proposed" in (adr_status(t) or "").lower()
        for rel, t in texts.items() if nodes.get(rel, {}).get("subtype") == "adr"
    }

    for src, path, line_no, context in pending:
        # A `~/` path outside the repo runs the SAME ladder as a repo path. Giving it its own
        # blanket class was wrong: it hid a live "this plan is stale, supersede it" TODO among ten
        # honestly-labelled retirements. What excuses a missing reference is what the citing prose
        # SAYS about it, not which filesystem it lives on.
        if path.startswith("~/"):
            exists, norm = os.path.exists(os.path.expanduser(path)), None
        else:
            norm = path[2:] if path.startswith("./") else path
            exists = os.path.exists(os.path.join(ROOT, norm))
        subtype = nodes.get(src, {}).get("subtype")
        src_is_proposed = subtype == "proposal" or adr_proposed.get(src, False)

        # KNOWN LIMITATION (judged 2026-09-12, recorded not hidden): `historical` and `tracked` key
        # off a keyword anywhere in the surrounding paragraph, so an unrelated "deleted" or an
        # unrelated YED-N in the same paragraph CAN suppress a genuinely broken reference. The
        # window is a paragraph because markdown hard-wraps mid-sentence. This trades false
        # negatives for precision deliberately; D4's precision budget measures the other axis, so
        # the recall side is watched by the Increment 3 ledger's `false-positive` acks, not here.
        if norm and norm in ignored:
            cls = "runtime"          # generated at run time; absence is normal
        elif src_is_proposed:
            cls = "proposed"         # a not-yet-built path in a plan is a plan, not a broken link
        elif HISTORICAL_RE.search(context):
            cls = "historical"       # the prose itself says it is retired/superseded
        elif YED_TOKEN_RE.search(context):
            cls = "tracked"          # already recorded where "what's open" lives
        else:
            cls = "repo"             # actionable: cited as live, absent from disk, unexplained
        edges.append({
            "src": src, "dst": path, "type": "references", "provenance": "derived",
            "exists": exists, "class": cls,
            "evidence": {"file": src, "line": line_no},
        })

    meta = {
        "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_sha": git("rev-parse", "--short", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
        "extractor_version": EXTRACTOR_VERSION,
        "increment": 1,
        "counts": {
            "nodes": len(nodes),
            "artifacts": len(nodes),
            "edges": len(edges),
            "references": len(edges),
            "dangling": sum(1 for e in edges if not e["exists"]),
        },
    }
    return nodes, edges, meta


def write(nodes, edges, meta):
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, payload in (("nodes.jsonl", nodes.values()), ("edges.jsonl", edges)):
        tmp = os.path.join(OUT_DIR, name + ".tmp")
        with open(tmp, "w") as f:
            for row in payload:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(tmp, os.path.join(OUT_DIR, name))
    tmp = os.path.join(OUT_DIR, "meta.json.tmp")
    with open(tmp, "w") as f:
        json.dump(meta, f, indent=2)
    os.replace(tmp, os.path.join(OUT_DIR, "meta.json"))


def dangling(edges):
    """The `dangling-ref` check: only class:repo becomes a finding; others are counts."""
    find, counts = {}, {}
    for e in edges:
        if e["type"] != "references" or e["exists"]:
            continue
        counts[e["class"]] = counts.get(e["class"], 0) + 1
        if e["class"] == "repo":
            find.setdefault(e["dst"], []).append(e["evidence"])
    return find, counts


def verify(edges):
    """Faithfulness: check-refs.sh's dangling list must be a SUBSET of ours, per artifact."""
    sh = os.path.join(ROOT, ".claude", "hooks", "check-refs.sh")
    if not os.path.exists(sh):
        print("verify: check-refs.sh absent — skipped", file=sys.stderr)
        return True
    mine = {}
    for e in edges:
        if e["type"] == "references" and not e["exists"]:
            mine.setdefault(e["src"], set()).add(e["dst"])
    srcs = sorted({e["src"] for e in edges if e["type"] == "references"})
    sample = random.sample(srcs, min(5, len(srcs)))
    ok = True
    for s in sample:
        p = subprocess.run(["bash", sh, "--artifact", s], cwd=ROOT,
                           capture_output=True, text=True)
        theirs = {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}
        missed = theirs - mine.get(s, set())
        status = "ok" if not missed else f"MISSED {sorted(missed)}"
        if missed:
            ok = False
        print(f"verify {s}: {status}", file=sys.stderr)
    print(f"verify: {'PASS' if ok else 'FAIL'} (graph must never see less than check-refs.sh)",
          file=sys.stderr)
    return ok


# ---------------------------------------------------------------------------
# Extractor regression cases. These exist because the template rule has been wrong twice: first it
# under-flagged nothing and capped good artifacts on path TEMPLATES (2026-09-11), then its fix
# over-corrected and silently swallowed REAL references sharing a whitespace-run (2026-09-12, judge
# defect D4). Both directions are represented. `--selftest` also re-runs every case through
# check-refs.sh and asserts the two tools agree, which is the only mechanical guard that ADR-8 D2
# ("shared verbatim") still holds — a comment saying "change both" does not enforce itself.
EXTRACTOR_CASES = [
    # (text, expected paths). Every path here RESOLVES ON DISK on purpose: these cases assert
    # EXTRACTION, not existence, and fixture paths that did not exist showed up in the graph as
    # real dangling references — the test data polluting the thing under test.
    # (text, expected paths)
    ("plain .claude/references/roadmap.md here", [".claude/references/roadmap.md"]),
    ("(see .claude/references/notion-schema.md)", [".claude/references/notion-schema.md"]),
    # real path, delimiter immediately after — must SURVIVE (the D4 regression)
    (".claude/references/notion-schema.md(the new one)",
     [".claude/references/notion-schema.md"]),
    # real path comma-joined to a template — only the template is dropped (the D4 regression)
    (".claude/references/roadmap.md,.claude/artifacts/log-{slug}.md",
     [".claude/references/roadmap.md"]),
    # genuine templates / regex literals — must stay suppressed
    ("`.claude/artifacts/evolution-log-{project-slug}.md`", []),
    ("Writes: .claude/evals/x/keyterms.(json|md)", []),
    (".claude/skills/{name}/SKILL.md", []),
    # inherited skip rules
    ("https://example.com/.claude/x.md", []),
    ("see .claude/skills/*/SKILL.md", []),
    ("see .claude/references/<name>.md", []),
]


def selftest():
    """Assert the extractor's behaviour AND that check-refs.sh agrees with it."""
    failures = 0
    for text, expected in EXTRACTOR_CASES:
        got = [p for p, _ in extract_paths(text)]
        if got != expected:
            failures += 1
            print(f"FAIL  {text!r}\n      expected {expected}\n      got      {got}",
                  file=sys.stderr)

    # Cross-tool agreement: write the cases to a temp artifact and diff the two extractors.
    sh = os.path.join(ROOT, ".claude", "hooks", "check-refs.sh")
    if os.path.exists(sh):
        import tempfile
        body = "\n\n".join(text for text, _ in EXTRACTOR_CASES)
        fd, tmp = tempfile.mkstemp(suffix=".md")
        with os.fdopen(fd, "w") as f:
            f.write(body + "\n")
        try:
            p = subprocess.run(["bash", sh, "--artifact", tmp],
                               capture_output=True, text=True, cwd=ROOT)
            theirs = {ln.strip() for ln in p.stdout.splitlines() if ln.strip()}
            # check-refs.sh reports only MISSING paths and only `.claude/` ones, so compare on
            # that subset: anything it reports the graph must also have extracted.
            ours = {p2 for text, _ in EXTRACTOR_CASES for p2, _ in extract_paths(text)
                    if p2.startswith(".claude/")}
            gap = theirs - ours
            if gap:
                failures += 1
                print(f"FAIL  check-refs.sh saw paths the graph did not: {sorted(gap)}",
                      file=sys.stderr)
        finally:
            os.unlink(tmp)
    else:
        print("note: check-refs.sh absent — cross-tool agreement not checked", file=sys.stderr)

    n = len(EXTRACTOR_CASES)
    print(f"selftest: {n - failures}/{n} extractor cases pass"
          f"{' + cross-tool agreement OK' if not failures else ''}", file=sys.stderr)
    return failures == 0


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(0 if selftest() else 1)
    nodes, edges, meta = build()
    write(nodes, edges, meta)
    c = meta["counts"]
    print(f"graph: {c['artifacts']} artifacts, {c['references']} reference edges "
          f"({c['dangling']} dangling, classified) "
          f"@ {meta['git_sha']}{' dirty' if meta['dirty'] else ''}", file=sys.stderr)

    if "--stats" in args:
        find, counts = dangling(edges)
        print(json.dumps({"counts": c, "dangling_by_class": counts,
                          "dangling_repo_targets": sorted(find)}, indent=2))
    if "--verify" in args:
        verify(edges)
    if "--check" in args and "dangling-ref" in args:
        find, counts = dangling(edges)
        items = sorted(find.items())
        for target, ev in items[:5]:
            where = ", ".join(f"{e['file']}:{e['line']}" for e in ev[:3])
            print(f"dangling-ref: {target} ← {where}")
        if len(items) > 5:
            print(f"dangling-ref: +{len(items) - 5} more actionable targets")
        skipped = {k: v for k, v in counts.items() if k != "repo"}
        if skipped:
            print(f"(not flagged: {skipped})")
    sys.exit(0)


if __name__ == "__main__":
    main()
