# Command Center: the cold-start contract

*Set 2026-11-18 (consolidation re-plan). Alex: "an every time part of development pushes … pages I can come back to from a cold start the next day or days later and pick back up with the full context."*

Every active track has two pages:

| Layer | Where | Holds | Who reads it |
|---|---|---|---|
| **Private cold-start page** | Command Center artifact, `https://claude.ai/artifact/AVd5j9UdmVmP4mWVXFSjq1` (private to Alex), one view per track (`#<track-slug>`) | Where we are, open actions with owners and due dates, decisions waiting on Alex with a recommendation, milestones, metrics against their do-nothing baseline, the session log, and a copyable resume prompt | Alex on a cold start; the next session |
| **Public status page** | Hub `src/data/projects/<slug>.json` (In Flight) | The public-safe story: why, milestones, health, decisions | Anyone |

The job-search track (`offer-sprint`) exists only on the private page.

## The every-push rule

A session that advances a track does this **before it stops**, in the same turn as its last commit or PR:

1. **Update the track row** (`tracks/<slug>`): `whereWeAre` (3–5 sentences a cold reader can act on), `phase`, `health` + `healthReason`, `lastSession` (`{date, what, next}`; `next` is one concrete move), `updated`.
2. **Tick and add actions** (`actions/<id>`): set finished ones to `status: "done"` with `doneOn`; add new ones with `track, owner (Alex|Claude), kind, text, due, ref`. Every action has a due date. Anything that needs Alex is an inbox item (next section), not a plain action.
3. **Move milestones and metrics** that changed. A metric always carries its `baseline`.
4. **Append one log row** (`log/l-<date>-<n>`): what landed, with PR/issue refs.
5. **On a milestone move only:** edit the track's public hub JSON as well (milestone-level, never per commit).

Writes go through the `ArtifactData` tool (`batch` for more than two docs; pin `if_version` on existing docs). Collections: `tracks`, `actions`, `milestones`, `metrics`, `log`.

## Ask Alex through the Inbox (set 2026-11-19)

*Alex: "when reviews or feedback are necessary, creating hoops to jump through or things for me to hunt and find slows us down. Every time, an experience should be spun up that is structured to collect the info necessary to execute on the review quickly."*

When any session needs Alex for anything (a decision, a PR review or merge, a fact only he has, or a go on a gated action), it writes **one inbox item**. It doesn't just ask in chat, a PR comment or Linear, and it doesn't give him a list of things to go and find. The page's **Inbox** view (`#inbox`, the default landing) shows every open item owned by Alex as a card he answers in place. `#i-<id>` deep-links one card.

The item is an `actions/<id>` doc with `owner: "Alex"`, `status: "open"`, `track`, `due`, `minutes` (an honest estimate of his time), `question` (one line), `ask` (1–2 sentences: what exactly is needed and why now), and one of three kinds:

| `kind` | Use for | Extra fields |
|---|---|---|
| `decision` | A choice between options | `options[{key,label,summary,pros[],cons[],cmd?}]`, `recommend`, `recommendWhy`, `confidence`; for anything non-trivial also `context[]`, `facts[{k,v}]`, `why`, `unblocks`, `ifNoDecision` (the full-brief page) |
| `review` | A PR or other artifact Claude has already reviewed, where Alex only confirms or merges | `verdict` (`merge`/`changes`/`hold`), `recommendWhy`, `checks[{k,pass,note}]` (what Claude verified, run by Claude rather than quoted from the PR), `mustRead[{label,url,note}]` (only the exact lines a rule says he must read himself, such as a guard or allowlist diff; empty otherwise), `command` (the one thing he runs, e.g. the merge command) |
| `input` | Facts or preferences only he has | `fields[{key,label,type:"text"|"choice"|"yesno",options?,default?,help?}]` |

Rules that make it fast:

1. **Do the legwork first.** Claude reads the PR, re-runs the checks, verifies counts against the source, and pre-fills defaults. A review card asks for a yes, not for a review.
2. **Recommend.** Every decision and review carries a recommendation; the page puts it first and marks it as the primary button.
3. **Give him the next step.** If an answer leads to something he must run (a mini launch, a merge), put it in `next.cmd`, or in `cmd` on that option. The page copies it to his clipboard on the same click.
4. **Read answers back.** Every answer writes the same patch: `{status:"done", choice, choiceLabel, choiceNote, answers?, doneOn}`. Sessions treat `choiceNote` as binding conditions. A session that resumes a track reads the decided items it raised and acts on them, before doing anything else.
5. **Point to it.** When the item is written, end the session's message to Alex with the card link `https://claude.ai/artifact/AVd5j9UdmVmP4mWVXFSjq1#i-<id>`. Send a push notification too, if that tool is available.
6. **Prefix unattended runs.** Items from unattended runs still prefix `question` with `TONIGHT:`. The page strips the prefix for display.

## What the page must never hold

No secrets, keys, email addresses or phone numbers (invariant 1 applies in spirit). No other people's confidences. Company names in the job-search track are fine: the artifact is private to Alex. It must never be shared beyond him without his go.

## Session limits that go with it

At most two Claude sessions alive across all tracks; each session's first line names its track and milestone. The **drift number** (`metrics/drift`: P1 applications + warm touches in the trailing 7 days; baseline 0, target ≥8, under 5 = drifting) is updated at every Friday review.

Source of the page: `.claude/.state/reviews/command-center.html` (private). The re-plan behind the tracks: `.claude/.state/reviews/replan-2026-11-18.md` (private).
