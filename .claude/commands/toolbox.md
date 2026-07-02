---
description: "Your tool wall — list every Empire State slash command, skill, and agent (grouped by workflow, one line each with 'use when' + args), scanned live from frontmatter so it never drifts. Optional filter/keyword, or 'plugins <keyword>' to search the alex-plugin skills."
argument-hint: "[optional: keyword or group to filter, e.g. 'content' or 'market-intel' — or 'plugins <keyword>' for plugin skills]"
---

# /toolbox — what's at your fingertips

Solves the "I built so much I forget what I have" problem. The catalog is **generated live** from the
`description` frontmatter in `.claude/{commands,skills,agents}` — there is no separate list to maintain, so
it can never go stale. Lead with the **project-local** kit (Alex's daily tools); the 256 `alex`-plugin
skills are a filterable appendix.

## Modes (from `$ARGUMENTS`)
- **no args** → the full project-local catalog, grouped by workflow.
- **a keyword/group** (e.g. `content`, `market-intel`, `signal`, `judge`) → filter project-local entries whose
  name/description matches (case-insensitive), OR show just that workflow group.
- **`plugins <keyword>`** → search the `alex`-plugin skills (`~/Documents/GitHub/alex-agents-skills/skills/`)
  by keyword and list matches (never dump all 256).

## Step 1 — Scan the frontmatter (live)
Run this to extract name · description · args for every project-local tool:

```bash
cd /Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3
python3 - <<'PY'
import glob, os, re
def fm(p):
    t = open(p).read(); m = re.match(r'^---\n(.*?)\n---', t, re.S); return m.group(1) if m else ''
def field(block, key):
    lines = block.split('\n')
    for i, l in enumerate(lines):
        m = re.match(rf'^{key}:\s*(.*)$', l)
        if not m: continue
        v = m.group(1).strip()
        # seed with the inline value (unless it's a folded/block/empty marker), then append any
        # continuation lines — covers single-line, folded '>', block '|', AND wrapped plain scalars.
        parts = [] if v in ('>', '|', '>-', '|-', '') else [v.strip('"').strip("'")]
        for j in range(i + 1, len(lines)):
            if re.match(r'^[A-Za-z_-]+:', lines[j]): break   # next top-level key at col 0
            if lines[j].strip(): parts.append(lines[j].strip())
        return ' '.join(parts).strip()
    return ''
def emit(kind, name, desc, args=''):
    print(f"{kind}\t{name}\t{' '.join(desc.split())[:160]}\t{args}")
for p in sorted(glob.glob('.claude/commands/*.md')):
    b = fm(p); emit('command', '/' + os.path.basename(p)[:-3], field(b, 'description'), field(b, 'argument-hint'))
for p in sorted(glob.glob('.claude/skills/*/SKILL.md')):
    b = fm(p); emit('skill', field(b, 'name') or os.path.basename(os.path.dirname(p)), field(b, 'description'))
for p in sorted(glob.glob('.claude/agents/**/*.md', recursive=True)):
    b = fm(p); emit('agent', field(b, 'name') or os.path.basename(p)[:-3], field(b, 'description'))
PY
```
(Robust YAML-ish parse — handles folded `>` / block `|` / wrapped multi-line descriptions, so nothing renders truncated.)

For `plugins <keyword>` mode instead run:
```bash
grep -rl -i "<keyword>" ~/Documents/GitHub/alex-agents-skills/skills/*/SKILL.md 2>/dev/null | while read -r f; do
  n=$(awk '/^name:/{sub(/^name: */,"");print;exit}' "$f")
  d=$(awk '/^description:/{sub(/^description: */,"");gsub(/^"|"$/,"");print;exit}' "$f")
  printf 'alex:%s — %s\n' "$n" "$(echo "$d" | cut -c1-100)"
done | head -40
```

## Step 2 — Group & present
Organize the scanned rows into these **workflow groups** (place each by best fit from its description; put
genuine misfits under **Other**; a tool can only appear once — pick its primary group):

1. **Event research & prep** — parsing invites, researching an upcoming event, pre-event content, project ideas.
2. **Post-event & content** — transcripts, post-event briefs, LinkedIn drafts, synthesis, evergreen, recaps, channel copy.
3. **Job search & market-intel** — interview prep, the market-intel engine/dashboard, target-company work.
4. **Signal scanners** — the trend / voice / role radars (`/scan-*`).
5. **Measurement & rigor** — judge, rigor review, outcome tagging, systems analysis.
6. **Research & analysis** — deep research, competitive/market landscape studies.
7. **Agents (called by workflows, not typed)** — the research/content/ops subagents.
8. **Other** — anything unmatched.

Present each entry as a **single scannable line**:
- Commands/skills: `` `/name` or `name` `` — *use-when* (tighten the description to a ≤12-word "reach for this when…") — `args` if any — **tier tag**.
- Agents: list compactly under group 7 (name — one-line role); note they're invoked by commands, not typed directly.

**Tier tag** (per the CLAUDE.md "invocation proactivity — BALANCED" rule): tag each entry so the catalog also
answers "will it fire on its own?" — `T1` (auto-fire: research/draft/analyze) · `T2` (auto-start, then stops
at its own write/approval gate) · `T3` (manual only: irreversible/external/credit/CRM). Infer from what the
tool does; when unsure, tag the higher (more cautious) tier.

Open with a one-line count (`N commands · M skills · K agents`). Close with the pointer:
*"Filter with `/toolbox <keyword>`; search plugin skills with `/toolbox plugins <keyword>` (256 available)."*

Keep it dense and skimmable — this is a menu, not documentation. Do not invent tools; only list what the scan returned.

## Notes
- **Freshness by design:** re-scans every run, so newly-added commands/skills appear automatically — no upkeep.
- **Hub fast-follow:** a browsable `ops/toolbox` page in empire-state-hub can render this same catalog from a
  generated manifest (deferred until the CLI proves the shape).
