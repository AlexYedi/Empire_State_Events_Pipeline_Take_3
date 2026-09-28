# State reconciliation + drift evidence — 2026-09-12

**Purpose.** The factual record of a cross-session state reconciliation, captured *as evidence* for a
systems diagnostic on why state drifts across worktrees / Linear / ADRs / docs. Written before the
diagnosis so the symptom survives the cleanup.

## 1. Topology (what the system actually is)

Four concurrent **git worktrees**, each driven by a separate Claude session over ~4 days:

| Worktree | Branch | Workstream |
|---|---|---|
| `ESP-jobsearch` | `alex/job-search` | Job-Search Engine, content rulings |
| `.claude/worktrees/feat+inbox-miner` | `worktree-feat+inbox-miner` | Inbox Miner (YED-153) |
| `esep-obs-capture` | `feat/obs-capture` | OBS capture lane (YED-154) |
| `esep-yed118` | `alex/yed-118-doc-kb-rag` | Doc-KB / RAG (YED-118, 155–157) |

Plus the `main` checkout. Worktrees were adopted deliberately (memory: shared-checkout hazard) — they
are the *correct* answer to parallelism. This record is about what they did **not** solve.

## 2. Drift observed at T0 (2026-09-11)

- **4 branches unmerged**, 6–13 commits behind `main`.
- **Linear lying:** 6 issues shipped but still `Backlog` (YED-146, 147, 148, 150, 153, 154). The
  codification rule says Linear is the source of truth for "what's open" — it was not. The SessionStart
  priority hook surfaced 5 stale Urgent items from a retired program as a result.
- **Roadmap** (plan of record) partially updated 2026-09-08, but its **Move 1 was ~a month stale**.
- **Doc version skew:** `content-style-guide.md` was **v0.9 on main, v0.8 on a branch**. Editing from the
  stale branch would have silently clobbered the v0.9 rule. Caught only by an explicit pre-edit check.

## 3. The counter-evidence (this matters — it weakens the obvious hypothesis)

At T1, **~24h later and with no central coordination, 3 of the 4 branches had merged themselves**
(PRs #61 inbox-miner, #62 job-search, #63 obs-capture). `feat/obs-capture` was cleanly deleted and its
worktree removed. **The code-convergence problem largely self-corrected.**

Two sessions also closed the *same* Linear issues within minutes of each other — duplicated effort, not
missed effort.

So: the drift is **not** primarily a failure to merge. Branch convergence works. What did *not*
self-correct is coordination over **shared namespaces and shared status**.

## 4. The sharpest symptom: an ADR numbering collision

Two branches independently minted **ADR-6**:
- `main`: `ADR-6-research-brief-placement.md` (landed via #62)
- a branch lineage: `ADR-6-crm-boundary-clarify.md` (Clarify — a decision that was **rejected**, artifacts
  removed from main in `1240aae`/#58)

Both inherited a common ancestor (`45756b2`) that introduced the Clarify ADR-6. The inbox-miner branch
detected and dropped it on merge (`608051d`); **`alex/yed-118-doc-kb-rag` still carries it today** and
will collide when it merges.

Key property: **the collision is invisible until merge.** Nothing at mint time can see the other branch.
A rule was added post-hoc to `docs/adr/README.md` ("mint ADR numbers from `main`, not a branch"), which
is a convention, not a mechanism.

## 5. Mechanisms that already exist (do not rebuild these)

- **DoD close-out gate** — `/dod-close` → `.claude/.state/<session>.build_meta` → Stop hook → telemetry
  (`build_session` rows). Already fires; already writes met/waived/correction-rounds.
- **Cross-provider build-quality judge** (Claude + Gemini quorum), provisional-trusted.
- **Memory system** (`MEMORY.md` + per-fact files) — cross-session durable facts.
- **CLAUDE.md conventions** — branch-first flow, ADR discipline, HITL defaults, Linear-as-source-of-truth.
- **Roadmap** as the version-controlled narrative spine; **Linear** as live "what's open."
- **Session-start hook** pulling Linear priorities.

## 6. Hypotheses to pressure-test (do not accept either uncritically)

- **H1 (original):** state is written at the moment of *intent* (issue filed, branch cut, ADR drafted) but
  not at the moment of *completion*. Parallelism without a convergence cadence = divergence.
  — *Weakened by §3:* convergence did happen unprompted.
- **H2 (revised):** the failure is not convergence but **coordination over shared, globally-unique
  resources** — ADR numbers, Linear issue status, doc version lineage — which each session mutates
  locally with no visibility into peers. Worktrees isolate *files* but do not isolate (or arbitrate)
  *shared namespaces*.
- **H3:** duplicated close-out work (two sessions closing the same Linear issues) suggests the cost is
  now **redundancy and ambiguity**, not omission.

## 7. What the diagnostic should return

> **2026-09-18:** whether to run this diagnostic at all is **YED-175** (decision, due 2026-10-09; recommendation: drop — the backlog reconciliation is the intervention).


1. Bound the system; stocks/flows; the reinforcing/balancing loops actually at work.
2. Archetype identification **with explicit rule-outs** (per house discipline: name what was considered
   and rejected, with evidence).
3. The **leverage point(s)** — ranked, Meadows-style.
4. A **minimum-viable operating model**, strongly preferring an extension of the existing DoD close-out
   over any new system.
5. An explicit **"do NOT build this"** list — guard against over-engineering; the house bias is that each
   build must remove a *named* friction.
