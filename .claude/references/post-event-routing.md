# Post-event routing block (Step 3.8e) — YED-387

The post-event brief is long by design, and most of its sections used to have no reader (consumption audit,
`docs/proposals/2026-11-05-post-event-consumption-audit.md`). The routing block fixes that. Each item names
one thing in the brief that someone or something should act on, and where it goes. The synthesizer writes
the block, `route_brief.py` validates it and turns it into a write plan, and the parent does the writes.

Read by `post-event-synthesizer` (it writes the block), `/post-event-content` Step 3.8e (parent) and
`.claude/scripts/route_brief.py` (the parser; this file is its contract).

## Shape

The block is the last thing in the synthesizer's handback, after the gaps list. It is two marker lines with
one JSON object per line between them. The parent strips it before the brief is written to Notion
(`route_brief.py strip`).

```
⟦routing⟧
{"routing_version": 1, "event": "<event name>", "recap": true}
{"type": "followup", "title": "...", "source": "§17", "evidence": "...", "why": "...", "owner": "Alex", "due_days": 7, "person": "<name>"}
{"type": "build-idea", "title": "...", "source": "§7", "evidence": "...", "why": "...", "owner": "Alex", "complexity": "small_tool"}
⟦/routing⟧
```

The first line is the header. `recap` is true only when Alex's recap was among the inputs.

## Item fields

| Field | Required | Rule |
|---|---|---|
| `type` | yes | one of the seven types below |
| `title` | yes | ≤100 chars, an action or a question, readable on its own |
| `source` | yes | the brief section it came from, as `§N` (optionally `§N.x` or a sub-heading) |
| `evidence` | yes | ≤240 chars: timestamp, speaker and a short paraphrase or quote locator. Never contact details |
| `why` | yes | ≤240 chars: why acting on this is worth it |
| `owner` | yes | `Alex` or `session` |
| `due_days` | followup and decision: yes; others: optional | integer 1–60, days after the event |
| `person` | followup: yes; others: not allowed | the person's name only |
| `complexity` | build-idea: yes; others: not allowed | `prototype`, `small_tool`, `MVP` or `full_project` (Project Ideas `Complexity Band`) |
| `body` | optional | ≤800 chars of extra detail |

## Types and where they go

| Type | What it is | Destination |
|---|---|---|
| `decision` | a call only Alex can make (e.g. add a company on stage to the target list) | Linear issue, label `decision` |
| `followup` | a dated second touch with someone Alex met or heard (Day 7 / Day 21) | Linear issue with a due date |
| `upskill` | a practice from the room to try on our own work | Linear issue, `B · Builds` |
| `open-loop` | something to verify or close: a Rule 12 claim, an UNRESOLVED entity, a promised share | Linear issue |
| `content-backlog` | an unused angle worth a later post | **one** Linear issue per event listing every angle |
| `build-idea` | a buildable project the room suggested | Notion Project Ideas row, `Status = needs_review` |
| `story` | a first-hand "I was in the room when…" moment for interviews | private local file `.claude/.state/post-event/<slug>/stories.md`; Alex moves keepers into `me-model.md` by hand |

## Rules for the synthesizer

1. **Route only what the brief supports.** Every item cites a section, and its evidence must be in that
   section. Never route general knowledge.
2. **No recap, no people.** Without Alex's recap, write `"recap": false` and route no `followup` (same rule as
   the brief: validated 2026-10-15).
3. **Off the record stays out.** Nothing excluded under Rule 4 of the agent may appear in any field.
4. **At most 12 items.** Prefer fewer, sharper ones. Merge near-duplicates. Aim for 3–8 on a normal night.
5. **No contact details.** No email addresses, phone numbers or private handles in any field (ADR-9).
6. **Content angles are one item each** with `type: content-backlog`. The planner groups them into one issue.

## Rules for the parent (Step 3.8e)

1. `route_brief.py extract <brief>`: exit 0 = valid, 2 = invalid (fix or re-ask the synthesizer, never
   hand-patch silently), 3 = no block (pre-routing brief: run the synthesizer in routing-only mode).
2. `route_brief.py plan <brief> --event "<name>" --event-date YYYY-MM-DD [--notion-event-id <id>]` writes
   `routing-plan.json` (Linear issues, a Notion payload for build ideas) and the local stories file.
3. **Linear:** search before create (`list_issues` with the title's key words). Skip a match and count it as
   routed. Create the rest with team `EMPIRE-STATE`, the planned labels and due date.
4. **Notion:** `notion_payload.py <payload>` must print VALID, then dispatch `notion-writer`.
5. Show Alex the counts in the Step 6 summary. Then
   `run_state.py mark "<event>" route --status done --meta routing_rows=<created+matched>`.
   No routable items: `--status skipped --reason "<why>"`.
6. **Prove-first mode (until YED-387's gate is met):** show the plan to Alex before any write. Auto-write
   once a run needs no hand fix on more than 1 item in 10.

## Routing-only mode (existing briefs, backfill)

For a brief written before this contract, dispatch `post-event-synthesizer` with the brief path, Alex's
recap (if any) and this file, and ask for **routing-only**: it returns just the block, under the same rules.
