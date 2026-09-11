---
description: "Capture an in-the-moment build-journal prose entry — draft from today's shipped facts, ask ≤3 sharpening forks, write the human-owned prose sidecar, regenerate the hub journal, and flag the deploy. The manual break-point companion to the /dod-close auto-capture."
argument-hint: "[optional: a date YYYY-MM-DD (default today), or a one-line note on what shipped]"
---

# /journal-entry — capture a build-journal entry in the moment

Runs the shared **journal-entry prompt** to pull Alex's voice into the public build journal at a break
point that isn't a full DoD close — a content/carousel ship, a scaffold, a milestone. (For a non-trivial
build close-out, `/dod-close` runs this same routine automatically as its final step.)

## Trigger
Alex types `/journal-entry`, or the agent proactively offers it after a shippable break point that
won't hit `/dod-close` (a Tier-1/2 artifact that still belongs on the build-in-public surface). Because
it writes a reviewable artifact and never publishes on its own (the hub deploy stays manual), it is
safe to start proactively.

## Shape
Follow **`.claude/references/journal-entry-prompt.md`** end to end — it is the authoritative routine:
1. Date + scope (default today, or `$ARGUMENTS` if a date/note was given) → gather today's shipped
   facts from both repos' git log.
2. Pre-draft the ≤3-line what/why/value entry from those facts (prep-then-ask).
3. Ask ≤3 sharpening forks — only where the artifacts can't answer.
4. Compose the final entry from Alex's answers (or ship the draft if he adds nothing).
5. Write `.claude/data/build-journal-prose.json` (merge by date; append as a second ship if the key
   exists) and validate the JSON.
6. `python3 .claude/scripts/build_journal.py` → confirm the day now renders curated (✍).
7. Report the entry + shipped PR chips, and **flag that the `/journal` page needs the hub repo
   committed + deployed to go live — do not auto-deploy.**

## Guardrails
- **Main conversation only** — interactive + touches the sidecar/generator; never a subagent.
- **Never auto-deploys** — the hub is a separate repo; staging is offered, push/deploy is Alex's.
- **No invented ships** — if nothing shipped today, say so and offer a prose-only entry or skip.
- **Prep-then-ask** — draft first, then ≤3 informed forks (mirrors `steering-interview` v2). No cold
  generic prompts.

## Ground truth
- Routine: `.claude/references/journal-entry-prompt.md`
- Generator: `.claude/scripts/build_journal.py` · sidecar: `.claude/data/build-journal-prose.json`
- Stop hook: `.claude/hooks/build-journal-refresh.sh` · public surface: `/journal` on empire-state-hub
- System issue: YED-119
