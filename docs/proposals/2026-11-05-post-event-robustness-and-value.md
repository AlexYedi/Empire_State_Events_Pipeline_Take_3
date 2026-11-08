# Post-event stage, v2: robustness and value generation across every driver

Read-only, 2026-11-05. Builds on v1 (`post-event-eval.md`, same folder): v1 found that 17 brief sections have two consumers. v2 asks how robust the stage is, how much value it generates per driver, and what the target shape is. New evidence this pass: dispatch telemetry (`.claude/.state/telemetry/dispatches/2dea6d47….jsonl`, `5139ab4a….jsonl`), `.gitignore` vs the live Agentics folder, the north-star memory (10-27 correction: three standing goals equal to the offer), `build-in-public.md`, `role-radar/SKILL.md`, `agent-routing.md` tiers, the coverage ratio (`Event Content` folders since September: 60 · briefs staged in `.claude/.state/briefs`: 11). Canonical systems references: `alex:systems-thinking` (Meadows). FMEA scoring per `alex:consulting-failure-design` (MIL-STD-1629A; Klein pre-mortem).

## Verdict

Post-event today is a one-driver stage with a nine-driver mandate. It converts a recording into verified copy reliably (the quote-safety loop is the only validated evaluator in the repo) and into graph claims unreliably (mandatory, unenforced), and it produces nothing structured for the job pipeline, interview ammunition, relationships, builds, upskilling, or event selection. Robustness is asymmetric: the failures that would embarrass Alex in public are loud and caught (misattribution, unsourced claims); the failures that quietly destroy compounding value are silent and uncounted (a stalled session with no run state, a skipped 3.8c, a brief that never reaches the graph, a privacy manifest that lists the private names it says to exclude and sits in a tracked-eligible path). Coverage is the biggest single number: roughly one in five event folders since September has a staged post-event brief, so whatever the stage produces, it produces for a minority of rooms. The target state is not a longer checklist. It is four phases with one owner each (capture · synthesize · route · close), a run-state file that makes the stage resumable by any session, and a close-check that reads real state. Value per event rises most by routing what already exists (v1), and value across events rises most by raising coverage and by giving the three cross-event stocks (series ledger, story bank, playbook) a home.

---

## 1. Value-driver map

Leverage rank = how much north-star value per unit of build, judged against the 10-27 correction (offer sprint + three standing goals, equal weight). Evidence cites files; "could produce" stays inside settled decisions.

| Driver | Produces today (evidence) | Could produce | Immediate gap (this event, this week) | Compounding gap (across events) | Rank |
|---|---|---|---|---|---|
| **Job / offer pipeline (P1)** | Nothing structured. 0 references to Roles DB, `target-companies.md`, `/scan-roles` or `me-model` in the command or skill; HubSpot 5.5 only for people Alex "actually spoke with" (Agentics: nobody). Hiring signals captured in §3 ("Jesse hires for the ability to write… managers make better IC agentic engineers") have no reader. | Per event: companies-on-stage × target-list check; hiring signals → Roles DB note or a `role-radar` focus hint; a warm-path line per target (who at that company was in the room, what they said) feeding `/tailor-resume` and outreach. | Agentics: Prime Radiant, Nori, StrongDM, Ramp, Pangram seen; none checked against targets; no warm path recorded for Jesse/Amol beyond a connection note. | No per-company dossier of "every time this company appeared in a room I was in." `retrieve.py --lens job` exists but `/interview-prep` never calls it. | **1** |
| **Interview ammunition** | The Anecdotes (§11, 491 words), Hot Takes (§9) and Pre→Post Gap (§3) are exactly interview material and are `BOUNDARY_SECTIONS`/unread. `mock-interviewer` and `interview-prep-dossier` have no story-bank concept (grep: 0). | A `story_bank` claim type (first_hand, speaker-linked, dated) + a "you were there" section in every dossier; a running "proof-of-learning" list (what I changed in my own practice after X). | Agentics gives 3–4 first-class stories (rationalization tables; colleagues with credentials; the Jesse/Amol subagent split) and none is banked. | Stories decay in Notion pages nobody re-opens; by interview week they are re-derived from memory, which is what the pipeline exists to avoid. | **2** |
| **Network and relationships (incl. recurring communities)** | Opt-in connection notes (correct); People & Outreach State table (unread); cadence Day 7/21 as prose (content-correspondent.md:76–104) with no trigger; HubSpot gated. Recap: "Nori runs recurring events… go deeper over time" has no home; no `Series` on Events (the hub has one, `rooms.curated.json`). | A series ledger (who hosted, who spoke, who returned, what Alex asked, what landed) read by 1.7a's Continuity Ledger; cadence rows as To-dos/Linear with dates; speaker ladder per series (see §4). | Amol/Jesse notes exist; nothing records that this is touch 1 of a long game or when touch 2 is due. | Each Nori/Shortlist/Daytona night is researched as if first-touch for relationships even when entities are REFRESH. | **3** |
| **Thought-leadership content and brand (P3, lean)** | Strongest driver: 3 variants + comment + carousel, quote-safety evaluator (0.95 vs 0.65 null), Themes back-catalog (pre-event only; post-event Step 5 omits `Themes`). X cuts in the skill, not in the command output; hub long read never produced; Rooms page 0 Oct/Nov entries; deep-dives 0 runs. | One post now plus a backlog that the content calendar drains (alternates, deep-dives, synthesis pairs by shared Theme, X thread after variant pick, hub long read as the amended artifact). | Agentics: 7 angles, 1 used; the series-arc synthesis ("Aug verify → Nov specify") is the best cut and only Alex can write it; no backlog row holds it. | Back-catalog callbacks starve on post-event posts (no `Themes`); no evergreen assets; lean audience served one post per room. | **5** |
| **Knowledge stock ("most informed person in the room")** | The brief itself; 7 claim types staged (when 3.8c runs). Glossary/Tools/Anecdotes/Open Loops/Angles never leave the page (v1). | Glossary terms → Topic pages/`(general)` themes; a per-theme playbook that accretes (pro-tips + pitfalls across events); `claim_usage` logged so capture is priced. | ~3,500 words/event unread. | The stock is in 11 Notion pages, not in a queryable place; `retrieve.py` can only surface what was staged. Coverage ~1 in 5 event folders. | **4** |
| **MI graph / market lens and trends** | 3.8b/c/d write event, roster, claims, theme assignments (unenforced); ADR-13 slice layer proposed 11-04 will read themes. Topic names were not passed to the Agentics synthesizer (its gaps list), so concept→topic is lossy. | Every concept with a glossary line is a candidate topic or theme tag; `retro`/`gap_score` and `story_bank` as claim types; `claim_usage` attribution at 1.7a. | Agentics 3.8b/c/d pending (claim held 3h by a stalled session). | "A topic with no theme is invisible to every trend" (command:281); post-event is the only producer of attended-event topics, so its coverage caps the trend layer. | **4** |
| **Event-tied builds and portfolio (P2)** | No writer to Project Ideas (17 props, 0 refs). Agentics surfaced 4+ repo-applicable builds (Graphviz CLAUDE.md, rationalization tables, compaction self-letter, description-field rule). | "Build candidates" (idea · traced quote · why-Alex) → Project Ideas `needs_review`; a hackathon/demo-night variant that pulls the problem statement verbatim (anchor rule). | Zero rows. | P2 is the pillar Alex said was starving ("myopic focus… not developing depth and breadth"); events are its natural feed and it has none. | **2** |
| **Upskilling** | Pro-tips staged as `practice` claims for research retrieval only. Nothing routes "apply this to my own practice." | One `upskill` Linear issue per event (apply/reject N practices, each traced); glossary → Knowledge Library; a monthly "what I changed" line into the build journal. | Tip #1 (skill descriptions say when, not what) applies to the repo's 15 skills today. | Standing goal (1) has no artifact that shows learning happened. | **3** |
| **Research quality of the next brief** | Pre→Post Gap per event (4 confirmed · 1 reversed · 2 partial · 2 signals missed · 10 not-predicted at Agentics); Step 7 retro orphaned; `claim_usage` never logged at 1.7a; Demos #10 grading done once by hand ("recall, not ranking, was the killer"). | `gap_score` as a `retro` claim; monthly roll-up of prediction recall vs the invite-only null baseline; usage by claim type. | Nothing. | The one feedback loop that would tell the research stage what to research is not wired. | **3** |
| **Build-in-public journal** | Journal is build-fact driven (`build_journal.py`, prose sidecar); post-event has no hook to it. Prose lapsed three times even when wired. | A one-line "learned at <event>" row per month feeds the sidecar draft; nothing automatic (settled: manual prose). | — | The journal shows shipping, not learning; the learning is in the briefs. | 6 |
| **GKY** | Out of scope by design (`gky-no-saas-metrics` is about GKY docs). Events touch it only when procurement/capability-statement rooms appear (11-04 PANYNJ × UCEDC folder exists). | Tag such events `lens: gky` so their briefs route to GKY proof (certs, PO numbers, Buy America) not SaaS content. | PANYNJ folder has no post-event pass. | Keep out of the pipeline's defaults; one tag. | 7 |

Reading the ranks: drivers 1–2 (offer, interview, builds) have the highest value-per-build because they need no new capture, only routing of what the brief already holds (v1 gap 2, 5). Driver 3 items need one new stock each (series ledger, upskill issue, gap_score). Content (5) is the mature driver; its gap is backlog, not quality.

## 2. Robustness (FMEA; S/O/D 1–5, RPN = S×O×D; higher is worse; D=5 means undetected)

| Failure mode | Evidence from real runs | S | O | D | RPN | Loud or silent | Mitigation (detection first) |
|---|---|---|---|---|---|---|---|
| **Stalled session, run state lost** | Agentics: claim held by session `2dea6d47` 3h; the session hand-wrote `00-post-event-inputs.md` as a manifest; `content-correspondent` dispatch errored (`model_resolved: None`, wrong agent name) then relaunched as `alex:content-correspondent` async; no record of which steps completed | 4 | 4 | 4 | **64** | Silent (a second session sees "held" and nothing else) | `run-state.json` per event written at each step; Step 1.0 reads it; claim carries the last completed step; agent-name check before dispatch |
| **Silent drift of unenforced steps** (3.8b/c/d, Themes, Rooms, 5.6) | Command admits "a skipped graph write closes green" (231); Rooms 0/30 since Oct; `Themes` absent from Step 5 list; deep-dives 0 runs; 24 of 27 events never reached the graph before YED-160 | 4 | 4 | 5 | **80** | Silent | Step 6.5 close-check reading real state (graph row, claims>0 or skipped-with-reason, themes, `Themes`, rooms); PASS/FAIL printed, never blocks |
| **Privacy leak into public-eligible files** | `00-post-event-inputs.md` (not gitignored) lists "Private names out: [five private names]" and the two do-not-publish items by description; `alex-recap.md` not ignored; the brief and conditioned transcripts are ignored. A defect by the privacy-layer rule regardless of the backstop (`feedback_privacy_layer_fails_regardless_of_backstop`) | 5 | 3 | 4 | **60** | Silent until `git add` | Any file under `post-event/` ignored by default except an explicit `public/` subfolder; the do-not-publish list lives in `.claude/.state/post-event/<slug>/`, never in `Event Content/`; pre-commit grep already exists for "off the record" but not for this manifest shape |
| **Coverage: no post-event run at all** | 60 event folders since Sep · 11 staged briefs. Some are virtual/pending, but the ratio means most attended rooms produce no brief | 4 | 5 | 3 | **60** | Semi-silent (visible only by comparing folders to briefs) | A weekly "attended, not debriefed" list from calendar vs `.state/briefs`; a 24h-lite mode (recap + Supercut summary, no full brief) so coverage is not binary |
| **Recap gate latency** | Synthesizer: recap "REQUIRED"; Agentics recap given 11-05 for a 11-04 room; without it the brief "must not propose any follow-up" | 3 | 4 | 2 | 24 | Loud (synthesizer says INPUTS MISSING) | 4-question Wispr template captured as Field Color the same night; pass-1/pass-2 split already exists |
| **Transcript / diarization / quote safety** | Strongest loop: Scribe v2 + keyterms (100% vs 50% proper nouns, n=1 event), HIGH/MED tiers, `output_checks.py` + `output-evaluator` (54/57 vs 37/57 null). Residual: merged block P2 30:20–36:27 attributed by content; ~34 MED quotes | 5 | 2 | 1 | 10 | Loud | Keep. Add a per-event conditioning score line to the close-check so the June n=1 bake-off is re-measured |
| **Notion / graph write failures** | notion-writer manifests make retries safe; 3.8c 404 until migration 0009 applied; "writer unavailable → stop, don't write inline" (f7e8979) | 3 | 3 | 2 | 18 | Loud (writer table) | Keep; the close-check turns "skipped" into a counted state |
| **Token / context cost of a 20k-word brief** | Synthesizer on Fable: 1,340 s (22 min); on Opus: 498 s; notion-writer 318 s; the brief then re-enters context for content-correspondent, output-evaluator ×2, and the 3.8c parse. Only `output_tokens`/`peak_context` are honest (platform-constraints:60). Subscription is the engine (think-bigger memory), so cost is wall-clock and context pressure, not dollars | 2 | 5 | 3 | 30 | Silent (no per-event budget line) | Pass the routing block and review head, not the whole brief, to downstream agents; log `duration_s` per step in run-state; no token cap (settled: spend the subscription) |
| **Single-session dependency** | All writes in the parent; MCP connectors do not work in subagents; one laptop; claims expire at 4h | 3 | 3 | 3 | 27 | Silent | Same fix as stall: run-state + resumable steps; nothing else is in scope (settled: no orchestrator) |
| **Wrong-event folder / naming non-determinism** | Two folders for one night (`11 04 26 Agentics Spotlight` with the carousel, `…Skills, Harnesses  Agent Identity` with post-event) | 2 | 3 | 3 | 18 | Silent | Derive the folder slug from the Notion Event title once, in Step 1 |

Pattern: every RPN ≥ 60 is a silent failure, and every loud failure is already mitigated. The stage has over-invested in B1 (public-copy safety) and under-invested in detection for everything that compounds. Pre-mortem line: "a year of post-event runs produced perfect posts and an empty graph, and nobody noticed because nothing counted."

## 3. Integration and timing: target-state shape

Four phases, one owner each, one artifact each. Each later phase reads the earlier phase's artifact, never the whole brief.

```
SAME NIGHT (owner: Alex, 3 min)            →  Phase 1 CAPTURE
  Wispr: who / follow-up / missed / left / "the one thing" (= recap + Field Color)
  Supercut recording exists; phone photos in the folder
  Artifact: recap.md + run-state.json{captured}

WITHIN 24h (owner: session A)              →  Phase 2 SYNTHESIZE
  2A/2B → 3.5 condition → 3.6 enrich → 3.7 synthesize (brief + ⟦routing⟧ block)
  Review head to Alex; brief to Notion
  Artifact: post_event_brief + routing block; run-state{synthesized}

WITHIN 24–72h (owner: session A or B)      →  Phase 3 ROUTE  (v1 gap 1, 2, 4, 5, 6 + content plan)
  3.8a–d graph/Notion write-back
  3.8e route: Open Loops → Linear · Build candidates → Project Ideas · Practices → one upskill issue
              · companies/hiring → job-lens check + story_bank claims · Outreach rows → To-dos (Day 7/21)
              · gap_score → retro claim · Series on Event
  Steer Touch 2 → content-correspondent → evaluator → Notion needs_review
  Content plan: primary post now; backlog rows for alternates / deep-dives / synthesis / X / long read
  Artifact: writer tables + Linear/Notion rows; run-state{routed}

7 DAYS (owner: Alex + /tag-outcome)        →  Phase 4 CLOSE
  Variant picked → X cuts; Day-7 touch-2 To-dos fire; tag-outcome on published rows
  Close-check: graph row · claims · themes · Themes · Linear rows · rooms entry  → PASS/FAIL line
  Artifact: Step 6 summary with real-state verdict; claim released

MONTHLY (owner: a review session)
  Roll-ups: prediction recall vs invite-only baseline · claim_usage by type · attended-not-debriefed list
  · series ledger deltas · playbook accretion (pro-tips/pitfalls by theme) · one journal line
  Feeds upstream: 1.7a Continuity Ledger (series) · role-radar focus (companies seen) · interview-prep
  (story_bank) · steering Touch 1 (what landed last time) · content calendar (backlog drain)
```

Upstream flows that must exist for the loop to close: (a) 1.7a reads the series ledger and `retro` claims so the next brief's Success Signals are calibrated by what fired last time; (b) `/scan-roles` accepts "companies seen in rooms this month" as a focus hint; (c) `/interview-prep` Step 1 runs `retrieve.py --lens job` and renders a "you were there" block; (d) steering Touch 1 shows last time's gap_score for the same series; (e) the content calendar (Upcoming Week / weekly) drains the backlog rows by Theme.

## 4. What is missing entirely (kept only where it earns it)

| Capability | Earns it? | Why / shape |
|---|---|---|
| **Attendee-roster mining when Alex talks to no one** | **Yes, bounded.** Agentics: auditorium, 600 signed up, zero conversations; the recap's "go deeper over time" needs a *who*. | Not scraping. Use what the organiser publishes (Luma/Partiful guest list visible to attendees, speaker LinkedIn comment threads on the event post) → Notion People rows `Role Context = attendee (public list)`, no contact detail (ADR-9), capped at the people who also appear in a target company or Theme. Public-engagement track only (bucket D). |
| **Speaker relationship ladder across a series** | **Yes.** Nori, Shortlist, Daytona, Clay are recurring; each ladder rung is already a defined artifact (comment → connection → DM touch 2 → coffee). | A `Series` on Events + per-person `ladder_stage` on the People row, advanced by `/tag-outcome`; 1.7a prints the rung so steering can aim ("you're at stage 2 with Amol; the move is a public comment on his next post"). |
| **Cross-event synthesis trigger** | **Yes, cheap.** `pattern-synthesis` exists and waits for Alex to notice a pair. | In Phase 3: one SQL on Content Drafts for briefs sharing a Theme within 30 days → a backlog row "synthesis candidate: A × B"; the skill then runs on request. |
| **Evergreen accreting assets (glossary / playbook)** | **Yes.** The glossary (694 words/event) and pro-tips/pitfalls are the raw material of a "most informed" reference and die per page. | Per Theme, one Notion page (or Topic page section) that Phase 3 appends to: term · definition · first heard · source. Playbook = pro-tips + pitfalls by theme, de-duplicated by claim key. Both are hub long-read candidates later. |
| **Proof-of-learning artifacts for interviews** | **Yes.** Standing goal (1) has no evidence trail. | The `upskill` issue closes with "applied / rejected + what changed"; monthly one-liners roll into `me-model.md` (local) and the journal prose when Alex chooses. |
| **Outcome loop to which events are worth attending** | **Yes.** Step 7's tier A/B/C was the right idea in the wrong place. | `gap_score` + tier as a `retro` claim per event; `/check-new-events` shows the series' last tier when a recurring event appears (read-only hint, no gate). |
| 24h-lite debrief mode | **Yes.** Coverage ~1 in 5. | Recap + Supercut summary + 3 claims, no brief, flagged `lite` in run-state; upgradeable later. |
| Live-room note-taking agent, auto-start on Supercut upload, OTEL traces | No. Settled (no speculative architecture; OTEL only on a named trigger). |

## 5. Removal and simplification

- **Pass the routing block, not the brief.** Downstream agents (content-correspondent, evaluator, 3.8c parser) take the review head + routing block + the sections they need; the 20k-word brief stays in Notion. Cuts context pressure and the 22-minute tail.
- **Delete Step 7 retro** (SKILL.md 7a–7e) once `gap_score` exists; **merge §17/§18 into §12/§13**; **cut Step 5.6** as an in-command step (backlog row instead); **cut the Day 7/21 prose and the `event-signal-tracker` reference** in content-correspondent (skill does not exist); **cut or wire the Rooms line** in Step 6.
- **Collapse the 511-line command** into orchestration-only: the 3.8b/c/d and Step 5 plumbing paragraphs move to a reference (`post-event-writeback.md`) the parent reads on demand; the command keeps the four phases and the gates. The 26-commit history is on exactly these plumbing paragraphs.
- **One folder per event, derived from the Notion title** at Step 1; stop hand-writing manifests.
- **Move every do-not-publish list** out of `Event Content/` into `.claude/.state/post-event/<slug>/`; `Event Content/**/post-event/` ignored by default except `public/`.
- **Do not add brief sections.** Nothing in this pass needs new capture; everything needs a reader.

## 6. Sequenced plan

**0–7 days: manual pilots on Agentics (no code)**
1. Privacy fix first: move `00-post-event-inputs.md` private lines and `alex-recap.md` to `.claude/.state/post-event/agentics-spotlight/`; confirm `git status` clean. Effort XS. Confidence 95%.
2. Hand-write `run-state.json` (captured · synthesized · 3.8 pending · drafts async) and finish 3.8b/c/d from the staged brief. Effort S. 85%.
3. Route by hand: 3–5 Linear issues from §16; 2–3 Project Ideas rows from §6/§7; one `upskill` issue (apply tip #1 to the 15 skills?); two To-dos for Amol/Jesse touch-2 with Day-7 dates; `Series = Agentics Spotlight (Nori)` on the Event; a gap_score line (4/1/2/2/10, tier B) on the Event page; three story lines into `me-model.md`. Effort S. 85%.
4. Content plan by hand: one backlog row per unused angle, Theme set; mark the series-arc synthesis as Alex-authored. Effort S. 80%.
5. Attended-not-debriefed list for September–November from folders vs `.state/briefs`; Alex picks which to run in lite mode. Effort S. 75%.

**2–4 weeks: builds (each a PR with a Linear issue)**
6. `run-state.json` + Step 6.5 close-check script + agent-name preflight. Effort S–M (1 day). 85%.
7. Synthesizer `⟦routing⟧` block + Step 3.8e router (Linear/Project Ideas/To-dos/job-lens/story_bank/retro/Series). Effort M (2–3 days). 80%.
8. `/interview-prep` reads `retrieve.py --lens job` and renders "you were there"; `/scan-roles` accepts a companies-seen hint. Effort S–M. 75%.
9. Content plan + `Themes` on post-event posts + synthesis-candidate query + X cuts in Step 4 output. Effort M. 75%.
10. Lite debrief mode. Effort S. 70%.

**Quarter horizon**
11. Series ledger + speaker ladder read by 1.7a and steering Touch 1; `/check-new-events` shows last tier. Effort M–L. 70%.
12. Per-theme glossary/playbook pages accreting from Phase 3; first hub long read generated from one. Effort M–L. 65%.
13. Monthly roll-up session: prediction recall vs invite-only baseline, `claim_usage` by type (YED-262 re-attribution), coverage, playbook deltas, one journal line. Effort M. 70%.
14. Attendee public-roster mining, bounded as in §4. Effort M; privacy review required (ADR-9 path). 60%.

**Metrics, each with its null baseline:** coverage = debriefed ÷ attended (baseline: today's ~0.18); routing yield = Linear/Project Ideas/To-dos rows closed as done ÷ created (baseline: 0, nothing routed today; judge at 30 days); prediction recall = confirmed ÷ (confirmed + not-predicted) vs the invite-abstract-only prediction; story_bank claims surfaced in a dossier ÷ dossiers (baseline 0); series touch-2 completion ÷ touch-1 sent (baseline: unknown, record `none`).

## Posture
- Might be wrong about: the coverage ratio (folders include virtual, pending and roundup entries; the true attended denominator needs the calendar); whether Alex already acts on §11/§16 by hand.
- Want more evidence on: `claim` row counts per event in Supabase (not queried, read-only MCP not loaded here); Linear issue counts per event; Notion `Themes` fill on post-event posts.
- Extrapolating beyond canon: the four-phase shape and the "route, don't re-read" rule are mine; FMEA scores are judgment calls from file evidence, not measured frequencies.

Overall confidence 76% — moderately confident; the robustness ranking and the driver gaps are file-backed, the value ordering follows the north-star memory rather than measured outcomes.
