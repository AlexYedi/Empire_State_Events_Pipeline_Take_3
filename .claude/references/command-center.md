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
2. **Tick and add actions** (`actions/<id>`): set finished ones to `status: "done"` with `doneOn`; add new ones with `track, owner (Alex|Claude), kind (action|decision), text, due, ref`, and `recommendation` for decisions. Every action has a due date.
3. **Move milestones and metrics** that changed. A metric always carries its `baseline`.
4. **Append one log row** (`log/l-<date>-<n>`): what landed, with PR/issue refs.
5. **On a milestone move only:** edit the track's public hub JSON as well (milestone-level, never per commit).

Writes go through the `ArtifactData` tool (`batch` for more than two docs; pin `if_version` on existing docs). Collections: `tracks`, `actions`, `milestones`, `metrics`, `log`.

## What the page must never hold

No secrets, keys, email addresses or phone numbers (invariant 1 applies in spirit). No other people's confidences. Company names in the job-search track are fine: the artifact is private to Alex. It must never be shared beyond him without his go.

## Session limits that go with it

At most two Claude sessions alive across all tracks; each session's first line names its track and milestone. The **drift number** (`metrics/drift`: P1 applications + warm touches in the trailing 7 days; baseline 0, target ≥8, under 5 = drifting) is updated at every Friday review.

Source of the page: `.claude/.state/reviews/command-center.html` (private). The re-plan behind the tracks: `.claude/.state/reviews/replan-2026-11-18.md` (private).
