#!/usr/bin/env python3
"""/memory-inbox helper (YED-447): the deterministic half of promoting the mini's memory inbox. Run on the LAPTOP.

The judgement half (already covered? contradicts? gated topic? docs-lane eligible?) is the session's, under the rubric in
.claude/commands/memory-inbox.md. This script only fetches, scans, promotes and archives, and refuses anything unsafe.

  fetch  --dest DIR                     copy the mini's live inbox to DIR (read-only on the mini)
  scan   DIR                            JSON per item: kind, name, existing-note match, privacy-scan hits, topic hints
  promote FILE --index-line LINE        add a NEW note to the laptop memory + its index line (refuses if the name exists)
  archive REL... --action A --reason R  move items on the mini to memory-inbox-done/<date>/ with a reason sidecar;
                                        --drop-from-mini-memory also removes a dropped note from the mini's memory dirs
"""
import argparse, hashlib, json, re, subprocess, sys
from datetime import date
from pathlib import Path

MINI = "esep-mini"
INBOX = "Developer/esep-private/memory-inbox"
DONE = "Developer/esep-private/memory-inbox-done"
SLUG = "-Users-sameoldexpressions-Documents-GitHub-Empire-State-Events-Pipeline-Take-3"
LAPTOP_MEM = Path.home() / f".claude/projects/{SLUG}/memory"
MINI_MEMS = [f".claude/projects/{SLUG}/memory",
             ".claude/projects/-Users-sameoldexpressions-Developer-Empire-State-Events-Pipeline-Take-3/memory"]
# Hints only: they point the reviewer at rubric rule 5 (gated topics). They never decide on their own.
GATED = {"privacy/PII": r"\b(pii|privacy|personal data|contact detail|email address|phone)\b",
         "secrets": r"\b(secret|token|api[_ ]?key|credential|password|\.env)\b",
         "spend": r"\b(spend|credit|billing|subscription|paid|invoice|\$\d)",
         "publishing": r"\b(publish|post(ed)? publicly|public repo|go live)\b",
         "CRM": r"\b(hubspot|crm)\b",
         "hooks/settings": r"\b(hook|settings\.json|permission)\b",
         "merge policy": r"\b(merge to main|admin merge|auto-?merge|branch protection)\b",
         "invariants": r"\b(invariant|adr-\d+|decisions-not-to-reopen)\b"}
REPO = Path(__file__).resolve().parents[2]


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120, **kw)


def pii_hits(text: str) -> list:
    sys.path.insert(0, str(REPO / ".claude/scripts"))
    try:
        import spine_client as sc
        sc.telemetry(False)
    except Exception as e:
        return [f"privacy scan unavailable ({type(e).__name__}): treat as a hit"]
    try:
        sc._scan_pii({"text": text}, "memory_inbox")
        return []
    except sc.PIIViolation as e:
        return [str(e)[:160]]


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        if v and not line.startswith(" "):
            out[k.strip()] = v.strip().strip('"')
    if "type" not in out and m:
        t = re.search(r"^\s+type:\s*([\w-]+)", m.group(1), re.M)
        if t:
            out["type"] = t.group(1)
    return out


def cmd_fetch(a):
    a.dest.mkdir(parents=True, exist_ok=True)
    p = sh(["rsync", "-a", f"{MINI}:{INBOX}/", f"{a.dest}/"])
    if p.returncode:
        print(f"FETCH FAIL rc={p.returncode}: {p.stderr.strip()[-200:]}"); return 2
    n = len(list(a.dest.rglob("*.md")))
    print(f"fetched {n} inbox item(s) into {a.dest}")
    return 0


def cmd_scan(a):
    items = []
    laptop = {p.name: p for p in LAPTOP_MEM.glob("*.md")}
    index = (LAPTOP_MEM / "MEMORY.md").read_text(encoding="utf-8") if (LAPTOP_MEM / "MEMORY.md").exists() else ""
    for p in sorted(a.dir.rglob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = str(p.relative_to(a.dir))
        base = p.name.split("__", 1)[-1]
        is_index = base == "MEMORY.md" or base.startswith("MEMORY.additions")
        fm = {} if is_index else frontmatter(text)
        same = laptop.get(base)
        item = {"rel": rel, "kind": "index-lines" if is_index else "note", "note_file": None if is_index else base,
                "name": fm.get("name"), "type": fm.get("type"),
                "description": fm.get("description"),
                "laptop_has_same_name": bool(same),
                "identical_to_laptop": bool(same) and hashlib.sha256(same.read_bytes()).digest() == hashlib.sha256(p.read_bytes()).digest(),
                "privacy_hits": pii_hits(text),
                "topic_hints": [k for k, rx in GATED.items() if re.search(rx, text, re.I)],
                "index_lines": [l for l in text.splitlines() if l.startswith("- [")] if is_index else
                               [l for l in index.splitlines() if f"({base})" in l]}
        items.append(item)
    print(json.dumps({"items": items}, indent=1))
    return 0


def cmd_promote(a):
    src = a.file
    dst = LAPTOP_MEM / src.name.split("__", 1)[-1]
    if dst.exists():
        print(f"REFUSED: {dst.name} already exists in laptop memory (an edit to an existing note is always raised to Alex)"); return 9
    if pii_hits(src.read_text(encoding="utf-8")):
        print(f"REFUSED: privacy scan hit in {src.name}"); return 9
    line = a.index_line.strip()
    if f"({dst.name})" not in line:
        print(f"REFUSED: index line does not link ({dst.name})"); return 9
    dst.write_bytes(src.read_bytes())
    idx = LAPTOP_MEM / "MEMORY.md"
    cur = idx.read_text(encoding="utf-8")
    if line not in cur.splitlines():
        idx.write_text(cur.rstrip("\n") + "\n" + line + "\n", encoding="utf-8")
    print(f"promoted {dst.name} into laptop memory (+ index line); it reaches the mini at the next sync")
    return 0


def cmd_archive(a):
    day = date.today().isoformat()
    script = [f"set -e; mkdir -p ~/{DONE}/{day}"]
    for rel in a.rel:
        if ".." in rel or rel.startswith("/"):
            print(f"REFUSED path {rel}"); return 9
        name = Path(rel).name
        script.append(f"mv ~/{INBOX}/{rel!s} ~/{DONE}/{day}/{name}")
        script.append(f"printf '%s\\n' {json.dumps(a.action + ': ' + a.reason)} > ~/{DONE}/{day}/{name}.reason.txt")
        if a.drop_from_mini_memory and not name.startswith("MEMORY"):
            base = name.split("__", 1)[-1]
            for d in MINI_MEMS:
                script.append(f"rm -f ~/{d}/{base}; [ -f ~/{d}/MEMORY.md ] && sed -i '' '/({base})/d' ~/{d}/MEMORY.md || true")
    script.append(f"find ~/{INBOX} -type d -empty -delete; echo archived {len(a.rel)} item(s) as {a.action}")
    p = sh(["ssh", "-o", "BatchMode=yes", MINI, "; ".join(script)])
    print(p.stdout.strip() or p.stderr.strip()[-200:])
    return p.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("--dest", type=Path, required=True); f.set_defaults(fn=cmd_fetch)
    s = sub.add_parser("scan"); s.add_argument("dir", type=Path); s.set_defaults(fn=cmd_scan)
    p = sub.add_parser("promote"); p.add_argument("file", type=Path); p.add_argument("--index-line", required=True); p.set_defaults(fn=cmd_promote)
    r = sub.add_parser("archive"); r.add_argument("rel", nargs="+"); r.add_argument("--action", required=True,
        choices=["promoted", "promoted+docs-pr", "dropped-duplicate", "dropped"]); r.add_argument("--reason", required=True)
    r.add_argument("--drop-from-mini-memory", action="store_true"); r.set_defaults(fn=cmd_archive)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
