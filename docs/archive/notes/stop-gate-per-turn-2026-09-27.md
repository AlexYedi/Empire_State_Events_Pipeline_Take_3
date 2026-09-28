# Stop-hook gates fire per turn, not per run close — diagnosis, fix, and finishing the Shortlist run (spec of record; approved plan 2026-09-27)

**Session:** b7b796e0 (2026-09-27) · `/event-deep-research` for The Shortlist: September Founder Showcase (YED-205 live acceptance) · scope confirmed by Alex: **gate fix + ledger mismatch + finish this run**.

## Context — why this is being done

During the run, the two Stop-hook gates (`deep-read-gate.sh`, `substrate-gate.sh`) reported **FAILED** on nearly every turn boundary while the run was legitimately in progress. Alex's read — "the gates fail constantly and we're wasting tokens" — is correct, and the cause is a design defect, not this run:

1. **Claude Code's `Stop` event fires at every turn end.** Both hooks were written as if it fires once at session close (every design doc says "at close" / "at session end"; none mention per-turn). In a multi-turn interactive pipeline, `pending` is the *normal* state for most of the run — the Deep Read is ~30 min of subagent wall clock, the graph write a multi-minute background job, HubSpot waits on a human.
2. **Mechanics (confirmed):** on a pending row the hook returns `decision:block` (exit 0). The harness re-invokes the model. That turn ends with `stop_hook_active=true` → the hook appends one `*_gate_failed` row and allows the stop. So each turn end with pending work = 1 block + 1 full-context re-invocation + 1 **false** failure row. This session: **5** deep-read rows + **4** substrate rows, all false (the run passed). The re-invocation loop is the token burn.
3. **Neither gate has an in-progress signal.** `event-claim.py` already provides one (claimed Step 1.0, released at close, 4h TTL, machine-global JSON with `session_id`) — unused by the gates.
4. **The gates' intent is right and stays:** a silently skipped Deep Read / graph write must never close green (YED-139, YED-205). They caught two real defects this session — the no-retry network stall (fixed, `f531b3a`) and the Evidence Ledger table-vs-bullet mismatch (worked around, not fixed). Only the *trigger granularity* is wrong.

Also true: the historic telemetry is barely affected (1 prior row, 2026-09-20); the pollution is this session's 9 rows.

## Fix 1 — In-progress awareness for both gates (`.claude/hooks/deep-read-gate.sh`, `.claude/hooks/substrate-gate.sh`)

**Rule:** a `pending` row is *not* a failure while **this session holds a live event claim**. It becomes a failure only when the row is pending AND the session holds no live claim (run closed or abandoned).

- **Signal:** scan `~/.claude/event-claims/*.json`; "live for this session" = `session_id == <stdin .session_id>` AND `released_at == null` AND `claimed_at + ttl_hours > now`. No slug↔page_id mapping needed — the link is `session_id`, which both the claim file and the per-session ledger filename already carry. (`pid` in the claim is the short-lived script pid — do not use it.)
- **Behaviour while in progress:** exit 0, no `decision:block`, no failure row. Emit at most a one-line `systemMessage` (`gate: 1 pending · run in progress (claim live) — will be checked at close`) — optional; default silent to avoid re-prompt noise.
- **Behaviour when NOT in progress (no live claim):** unchanged — block once, then log once. This is the run-close case: Step 6 of the command releases the claim, so the very next turn end is the real gate.
- **Log-once guard:** before appending a failure row, skip if a row with the same `session` + same `events[].page_id`/`key` already exists in the failures log (prevents repeat rows if an abandoned run somehow keeps ending turns).
- **`_pending` session fallback** (no `CLAUDE_CODE_SESSION_ID`): treat as no claim → existing behaviour. Document this in the hook header.
- Factor the claim check into one shared helper `.claude/hooks/_run_in_progress.sh` (sourced by both gates) so the two "deliberate siblings" stay identical.
- **Abandoned-run coverage (a dead session never fires Stop again):** add a **SessionStart sweep** — the existing SessionStart hook chain (ADR-8 graph / linear-priorities) gets one more script that scans `.claude/.state/*.deep_read_gate.jsonl` / `*.substrate_gate.jsonl` for `pending` rows whose session has no live claim and whose `ts` is > 4h old, logs each once as `*_gate_abandoned`, and prints them. *Verify at build whether Claude Code's `SessionEnd` hook event is available in this version; if so, log the abandoned case there too (log only — it cannot block).*
- Update the docs that state the wrong semantics: hook headers (`deep-read-gate.sh:10`, `deep-read-ledger.sh:6`), `.claude/proposals/deep-read-marker-gate.md` (lines 33, 63), `event-deep-research.md` (line 161, 224-225) — one sentence each: "Stop fires per turn; the gate treats pending as in-progress while the event claim is live; it fails at the first turn end after the claim is released or expires."

## Fix 2 — Evidence Ledger parser accepts the table shape (`.claude/scripts/substrate.py` `parse_ledger`, ~line 501)

- Under a `##### Evidence Ledger — <Name>` heading, also accept markdown table rows `| claim | tier | source | url | date |`: skip the header row (first cell == `claim`, case-insensitive) and separator rows (`---`), split on unescaped `|`, map cells positionally to claim/tier/source/url/date. Tier cell may carry a qualifier (`web-verified (company-reported)`) — take the leading tier token; fold the qualifier into `source`. Reuse the existing `_public_url`, `TIER_MAP`, skip-counting and dedupe paths unchanged.
- Add selftest cases (same `add(...)` harness): a 3-row table ledger → 2 admissible (one `notion-prior` skipped); header/separator rows never counted as `empty_or_template`; a mixed bullet+table ledger parses both.
- **Contract wording** (`.claude/commands/event-deep-research.md` Step 2 return contract + Step 4.2b): state the exact bullet line format verbatim so the orchestrator never improvises a table; note the parser tolerates tables as a fallback. Do not edit the four specialist agent files (session-frozen registry; they already show the bullet form).

## Fix 3 — Correct this session's false telemetry (no deletion)

Append one correction row to each failures log: `{"event":"gate_false_positive_correction","session":"b7b796e0-…","ts":…,"supersedes":N,"reason":"per-turn Stop firing while run in progress (this plan); run closed green"}`; `/rigor-review` (`.claude/evals/correction-recurrence.md` reader) should exclude superseded rows for that session. Telemetry stays append-only.

## Branch / tracking / rigor

- **Branch:** continue on `alex/yed-205-req-retry` (already holds `f531b3a`); rename PR scope to *"YED-205 acceptance-run fixes: req retry · gate in-progress awareness · ledger table parsing"*. One PR — all three came from the same live run and are reviewed together. Push when GitHub is reachable (was unreachable at 12:0x).
- **Linear:** open a new issue *"Stop-hook gates fire per turn, not per run close"* (labels: bug, rigor; relates YED-139, YED-205; cite the 9 false rows and the re-invocation loop); the YED-205 comment already posted (a61a7c8f) covers the retry fix and flags the ledger mismatch — link the new issue from it.
- **DoD (non-trivial build):** spec = this plan file (infra → in-repo reference satisfies item 1; also drop a copy at `.claude/notes/stop-gate-per-turn-2026-09-27.md`); Linear = new issue; adversarial pass = pre-mortem below; judge = `/judge-build` on the PR diff this session; `/dod-close`.
- **Memory:** save a `feedback`-type note: Stop hooks fire per turn; gates must key on the event claim; never re-poll a background job by ending turns.

### Pre-mortem (item 3)
| Imagined failure | Verdict | Mitigation in plan |
|---|---|---|
| A run forgets to release the claim → gate never fires → silent skip closes green | **Real** | 4h TTL expiry already bounds it; SessionStart sweep logs abandoned rows; Step 6 release is mandatory text in the command |
| Two sessions, one claims, the other has pending rows → the other's gate reads a claim that isn't its own | Not real — match is on `session_id` | — |
| Claim file unreadable / malformed → hook errors | Real, minor | helper treats parse failure as "no claim" (fail-closed = gate stays strict) |
| Log-once guard hides a *second* genuine failure on the same page in one session | Acceptable | same page + same session = same run; a re-run is a new session |
| Table parser mis-splits a claim containing `\|` | Real, minor | split on unescaped `\|` only; selftest pins an escaped-pipe row |

## Finish the Shortlist run (execution steps, in order)

1. `deep-read-ledger.sh rendered 3e8d3699-c2db-81b9-ba32-e122ea8de2fb` is **not yet done** (Event page already carries `deep_read_rendered: 2026-09-27`; the Content Draft mirror is not). Append the Deep Read (`scratchpad/run/render/deep_read.md`, pronoun-fixed) to Content Draft `3e8d3699-c2db-8118-8d6d-c7a88521398e` via `notion-update-page update_content` on the `pending` marker; then flip the ledger.
2. Step 6.5: `notion-fetch` the Event page and confirm the marker; reconcile the ledger.
3. HubSpot Step 5 on Alex's ✅ (table already presented): create 5 companies → 8 contacts w/ associations → 11 notes; attach Ivor's note to `477298938613`; Ivor duplicate (`540707930827`) = Alex's call, not merged unprompted.
4. Step 6 summary block (include the `Graph:` line) → `event-claim.py release "The Shortlist: September Founder Showcase"` — this is the moment the fixed gates evaluate for real.
5. Apply Fixes 1–3 on the branch (they do not need to precede steps 1–4; but doing Fix 1 first stops the noise immediately — recommended order: Fix 1 → steps 1–4 → Fix 2/3 → PR → judge → dod-close).

## Verification

- **Hook unit test** (`.claude/evals/test_gate_in_progress.sh`, pattern of `test_event_claim.py`): temp ledger with one `pending` row; (a) live claim for the session → exit 0, no `decision:block`, no log row; (b) claim released → first call blocks, second call (`stop_hook_active:true`) logs exactly one row; (c) third call logs nothing (log-once); (d) `_pending` session id → existing behaviour; (e) malformed claim file → strict path.
- **SessionStart sweep test:** stale pending row (ts −5h), no claim → one `*_gate_abandoned` row; fresh row → none.
- **Parser:** `substrate.py --selftest` (125 + new cases), `spine_client.py --selftest` 39/39, `--check-writers` clean; dry-run `stage-research` against the *original* table-form evidence file (`…evidence.tables.md`) → `Graph: 171 research claims … created=0`.
- **Live:** with the fixed hooks installed, end a turn mid-run → no gate output; release the claim with everything rendered/staged → gates pass silently; release with a row deliberately left pending (scratch ledger) → one block, one row.
- **Telemetry:** `/rigor-review` dry read excludes the 9 superseded rows.
