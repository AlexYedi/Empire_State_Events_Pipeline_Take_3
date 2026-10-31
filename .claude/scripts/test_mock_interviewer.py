#!/usr/bin/env python3
"""test_mock_interviewer.py — offline convention checks for the mock-interviewer skill (E-09 / YED-256).

Stdlib only, no network, no Notion. Modes:
  default     — full convention checks against .claude/skills/mock-interviewer/
  --selftest  — harness self-checks on synthetic samples, then the full convention checks
                (picked up automatically by .github/workflows/selftests.yml)

The Notion guard bans tool-identifier shapes (MCP prefixes, tool names, the REST host, SDK
imports) anywhere in the skill. Prose that merely names the product ("a Notion needs_review
draft") is not a tool reference and stays allowed — tool names are hyphen/underscore-shaped,
never space-separated.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.normpath(os.path.join(HERE, "..", "skills", "mock-interviewer"))

DIMENSIONS = [
    "commercial bias",
    "diagnose before build",
    "failure paths",
    "adoption and handoff",
    "experimentation",
    "honest AI scoping",
    "communication across levels",
]
ROUNDS = [
    "Frustrated rep (discovery)",
    "Hiring manager (behavioural)",
    "Portfolio skeptic",
    "Take-home panel",
    "Commercial: discovery call",
    "Commercial: book review",
    "Commercial: QBR / renewal save",
    "Technical deep-dive",
    "Curveball / stress",
]
FAMILIES = ["behavioural", "commercial depth", "technical / role-specific", "curveball / stress"]
FIXTURE_ROUNDS = [
    "round-1-hiring-manager",
    "round-2-commercial-book-review",
    "round-3-portfolio-skeptic",
]
PRIVATE_INPUT_NAMES = ["me-model", "target-companies"]

NOTION_TOOL_PATTERNS = [
    re.compile(r"mcp__[a-z0-9_]*notion", re.I),
    re.compile(r"notion[-_](?:create|update|move|duplicate|fetch|search|get|append|comment|page|patch|delete|write|send|post)", re.I),
    re.compile(r"api\.notion\.com", re.I),
    re.compile(r"notion[-_](?:sdk|client|token|key)\b", re.I),
    re.compile(r"(?:import|from)\s+notion\b", re.I),
]


def notion_tool_hits(text):
    """Return Notion tool-identifier matches in text (empty list = clean)."""
    hits = []
    for pat in NOTION_TOOL_PATTERNS:
        hits.extend(m.group(0) for m in pat.finditer(text))
    return hits


def parse_scoresheet_rows(text):
    """Scoresheet table rows -> [(dimension, score_cell, evidence_cell)]."""
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([0-5]|n/e)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m:
            rows.append((m.group(1).strip(), m.group(2).strip(), m.group(3).strip()))
    return rows


def first_quoted(cell):
    m = re.search(r'"([^"]+)"', cell)
    return m.group(1) if m else None


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


ok = n = 0


def ck(name, cond):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("  ✓ " if cond else "  ✗ ") + name)


def anchors_present(skill_text, dims):
    """Each dimension's anchors carry a 5 / 3 / 1 anchor line within a small window."""
    lines = skill_text.splitlines()
    for dim in dims:
        found = False
        for i, line in enumerate(lines):
            if dim.lower() in line.lower():
                window = " ".join(lines[i:i + 4]).lower()
                if "5:" in window and "3:" in window and "1:" in window:
                    found = True
                    break
        if not found:
            return False
    return True


def run_harness_selftests():
    print("selftest — notion detector")
    ck("detector flags an MCP Notion tool call",
       notion_tool_hits("call mcp__notion__notion-create-pages now") != [])
    ck("detector flags a bare Notion tool name",
       notion_tool_hits("then use notion-update-page to set the status") != [])
    ck("detector flags the Notion REST host",
       notion_tool_hits("curl https://api.notion.com/v1/pages") != [])
    ck("detector flags a Notion token reference",
       notion_tool_hits("the NOTION_TOKEN comes from the environment") != [])
    ck("detector flags a Notion SDK import",
       notion_tool_hits("import notion\nclient = notion.Client()") != [])
    ck("detector passes prose that merely names the product",
       notion_tool_hits("a Notion needs_review draft written by the parent session") == [])
    ck("detector passes 'notionally' and prose mentions",
       notion_tool_hits("notionally speaking, the parent session writes the debrief to Notion") == [])
    print("selftest — scoresheet parser")
    sample = "\n".join([
        "| Dimension | Score | Quoted evidence |",
        "|---|---|---|",
        '| commercial bias | 4 | "opens on their metric" |',
        "| experimentation | n/e | round never reached a test |",
    ])
    rows = parse_scoresheet_rows(sample)
    ck("parser reads score and n/e rows, skips header and separator",
       len(rows) == 2
       and rows[0] == ("commercial bias", "4", '"opens on their metric"')
       and rows[1][1] == "n/e")
    ck("quote extractor takes the first quoted span",
       first_quoted('say "line one" then "line two"') == "line one")


def run_full_checks():
    skill_path = os.path.join(SKILL_DIR, "SKILL.md")
    print("skill contract")
    ck("skill file exists", os.path.isfile(skill_path))
    if not os.path.isfile(skill_path):
        return
    skill = read(skill_path)
    low = skill.lower()
    ck("frontmatter declares name + description",
       skill.startswith("---") and "name: mock-interviewer" in low and "description:" in low)
    ck("no-write contract stated in the skill itself", "never calls notion write tools" in low)
    ck("failure-path-first rule stated", "failure path" in low and "at most one question" in low)
    for fam in FAMILIES:
        ck(f"family present: {fam}", fam in low)
    for rnd in ROUNDS:
        ck(f"round script present: {rnd}", rnd.lower() in low)
    for dim in DIMENSIONS:
        ck(f"dimension defined: {dim}", dim.lower() in low)
    ck("all 7 dimensions carry 1/3/5 anchors", anchors_present(skill, DIMENSIONS))
    ck("scoresheet format defined", "quoted evidence" in low and "what to say instead" in low)
    ck("debrief contract defined (session debrief, top-3 fixes, needs_review)",
       "top-3" in low and "session debrief" in low and "needs_review" in low)
    ck("private inputs read by path at run time, never copied", "path at run time" in low)
    ck("convention test referenced in the skill", "test_mock_interviewer.py" in low)

    print("notion guard")
    files = []
    for root, _dirs, names in os.walk(SKILL_DIR):
        for name in sorted(names):
            files.append(os.path.join(root, name))
    ck("no Notion tool references in SKILL.md", notion_tool_hits(skill) == [])
    fixture_hits = {
        os.path.relpath(f, SKILL_DIR): notion_tool_hits(read(f))
        for f in files
        if os.path.relpath(f, SKILL_DIR) != "SKILL.md"
    }
    ck("no Notion tool references anywhere in the fixtures",
       all(hits == [] for hits in fixture_hits.values()))

    print("fixtures")
    dossier = os.path.join(SKILL_DIR, "fixtures", "dossier-northwind-freight.md")
    ck("fixture dossier exists", os.path.isfile(dossier))
    if os.path.isfile(dossier):
        dlow = read(dossier).lower()
        ck("fixture dossier is marked fictional", "fictional" in dlow)
        ck("fixture dossier carries the consumed fields",
           all(s in dlow for s in ["company snapshot", "role, decoded", "interview stage",
                                    "interviewer profiles"]))
    any_low_score = False
    for rnd in FIXTURE_ROUNDS:
        rdir = os.path.join(SKILL_DIR, "fixtures", rnd)
        paths = {k: os.path.join(rdir, f"{k}.md") for k in ("transcript", "scoresheet", "debrief")}
        label = rnd.replace("-", " ")
        present = all(os.path.isfile(p) for p in paths.values())
        ck(f"{label}: transcript/scoresheet/debrief all present", present)
        if not present:
            continue
        transcript = read(paths["transcript"])
        sheet = read(paths["scoresheet"])
        rows = parse_scoresheet_rows(sheet)
        dims_found = [r[0].lower() for r in rows]
        ck(f"{label}: scoresheet has all 7 dimensions",
           all(d in dims_found for d in (x.lower() for x in DIMENSIONS)))
        in_range, quotes_ok, ne_ok = True, True, True
        for _dim, score, evidence in rows:
            if score == "n/e":
                ne_ok = ne_ok and bool(evidence.strip())
                continue
            value = int(score)
            in_range = in_range and 1 <= value <= 5
            quote = first_quoted(evidence)
            quotes_ok = quotes_ok and quote is not None and norm(quote) in norm(transcript)
            if value <= 2:
                any_low_score = True
        ck(f"{label}: every 1-5 score is in range", in_range)
        ck(f"{label}: every score quotes the transcript verbatim", quotes_ok)
        ck(f"{label}: every n/e carries a reason", ne_ok)
        rewrite_zone = sheet.split("What to say instead")[-1].lower() if "What to say instead" in sheet else ""
        low_rows = [(dim.lower(), int(score)) for dim, score, _ in rows
                    if score.isdigit() and int(score) <= 2]
        ck(f"{label}: every score <= 2 has a what-to-say-instead rewrite",
           all(dim in rewrite_zone for dim, _ in low_rows))
    ck("the rewrite rule is exercised: at least one score <= 2 across the fixtures", any_low_score)

    session_path = os.path.join(SKILL_DIR, "fixtures", "session-debrief.md")
    ck("session debrief exists", os.path.isfile(session_path))
    if os.path.isfile(session_path):
        slow = read(session_path)
        ck("session debrief: review-draft shape (per-round notes, top-3 fixes, needs_review)",
           "needs_review" in slow and "Top 3 fixes" in slow and "Per-round notes" in slow)
        ck("session debrief covers all three rounds",
           all(f"Round {i}" in slow for i in (1, 2, 3)))

    print("privacy gate")
    clean = True
    for f in files:
        if os.path.relpath(f, SKILL_DIR) == "SKILL.md":
            continue  # the methodology may cite the gitignored PATH (like the dossier skill); fixtures may not
        text = read(f).lower()
        if any(name in text for name in PRIVATE_INPUT_NAMES):
            clean = False
    ck("gitignored private filenames never appear in fixture files", clean)


def main():
    selftest_mode = "--selftest" in sys.argv[1:]
    if selftest_mode:
        run_harness_selftests()
    run_full_checks()
    print(f"\n{'selftest: ' if selftest_mode else ''}{ok}/{n} passed")
    sys.exit(0 if ok == n else 1)


if __name__ == "__main__":
    main()
