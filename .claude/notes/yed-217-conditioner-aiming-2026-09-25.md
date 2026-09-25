# YED-217: the conditioner aims material at named speakers (2026-09-25)

Infra build, so this note is the spec (YED-129 ruling). Linear: YED-217. Companion (not built here): YED-218.

## Problem

The YED-172 A/B found that the two retrieval arms were good at different things. The substrate pack won on
**material**; the legacy pack won on **packaging**. At Apollo, the blind Sonnet seat preferred legacy because it
turned prior knowledge into *"two specific, speaker-named, chase-able questions (Dale Seo, Dan Boerner)."*

Evidence scope, stated narrowly: that is **one rater on one event**. At AI Builders, both seats preferred legacy
for dated, specific topic substance, not questions, and no speakers were known.

Mechanism, checked against the saved Apollo packs: the Seo question came from a `Top Questions` property item.
The Boerner question did not. The conditioner aimed a topic *claim* at him without being told to. The substrate
pack also had questions, but its best one *"has no named target."* So the gap is **aim**, not question supply.

## Change

1. `.claude/agents/research/knowledge-conditioning.md`: a new **Aimed Questions** step, output section, and
   quality-bar line. Constraints:
   - anchored word for word to a claim in the raw pull (claim id when present; ≤25 words; cut only with …)
   - the trust flag is inherited unchanged
   - a non-KNOWN anchor must be phrased as a test, not a premise
   - a thesis may only be tested against its own author
   - targets must be named in the invite, otherwise the room or the format (never a blocker)
   - budget ≤2 per person, ≤6 total, and zero is valid
2. `.claude/agents/research/event-research-synthesizer.md`: `Questions to ask` may now draw from the pack's
   Aimed Questions (see pre-mortem finding 1).
3. `.claude/scripts/check_aimed_questions.py`: a mechanical traceability check. It fails an anchor that is not
   word for word in the raw pull, a claim id that is absent, a missing trust tag, a target not in the invite, or a
   premise-shaped non-KNOWN question.

## Alternatives rejected

- **Aim in the synthesizer instead.** Rejected: by then the specialists have already researched without the
  aimed questions, and the pack is the persisted, auditable artifact (Step 1.7c). The conditioner is where the
  claims and the invite first sit side by side.
- **Aim only from `Top Questions`.** Rejected: that ties packaging to the legacy source. The Boerner question
  shows that claims can be aimed too, and the substrate has no Top Questions until YED-218 ships.
- **Let the judge catch invented questions.** Rejected as the only guard: traceability is a string-match fact
  and should be checked by a script, not an LLM.

## Adversarial pass (pre-mortem, written before calling it done)

*"It's 3 weeks later and this shipped but did nothing, or did harm. Why?"*

1. **The questions never reach Alex.** ✅ REAL, FIXED. The synthesizer's `Questions to ask` rule listed only
   Top Questions + Open-on-site and said "do NOT invent new questions", so aimed questions would have been
   dropped between pack and brief. The A/B scored packs directly, which hid this. Fixed by adding the pack's
   Aimed Questions as a third allowed source, with target + trust flag kept.
2. **Laundering through phrasing.** A trust tag does not protect a question worded as a premise ("Given that
   X…"). Handled by the test-not-premise rule; the checker flags premise openers on non-KNOWN anchors
   (heuristic, first words only).
3. **Anchors that "trace" to a paraphrase.** ✅ REAL, FIXED after the stand-in run. v1 of the spec asked for an
   anchor that "appears on a card above", but cards paraphrase, so the anchor pointed at the conditioner's
   own restatement and not the source. The anchor is now word for word from the raw pull, plus a claim id.
   The stand-in run also caught a real inserted word ("its DBs" → "its own DBs").
4. **Quota pressure produces filler.** Zero is explicitly valid; there is a budget cap and no minimum.
   ✅ A quieter version showed up in the v2 stand-in: with both speakers at their cap, a question went to the
   Program Manager *"rather than the engineer or advocacy roles already at their question cap"*. The cap pushed
   the question onto a weaker target. Fixed: drop it, don't re-route it.
5. **Inherited flags can be too generous.** OPEN (pre-existing, not introduced here). The trust-flag rule says
   a person's thesis is `UNVERIFIED` regardless. The stand-in tagged first-hand speaker theses (Levan, Gleb
   Otochkin) `KNOWN`, reading "Alex heard them say it" as verification. A question inherits whatever the card
   decided. The test-shaped wording limits the damage, but the card-level ambiguity (attribution verified vs.
   content verified) is a trust-flag question for its own issue: **YED-222**.

## Validation

**Stand-in run, this session (NOT acceptance).** The agent registry is session-frozen, so the registered agent
here still runs the old spec. A general-purpose Sonnet agent was told to follow the edited spec word for word
(Read-only) on the real Apollo **substrate-only** pull. The v1 spec produced 5 questions: 2 → Dale Seo,
2 → Dan Boerner, 1 → the format. Checker: **4/5 pass.** The failure was a real inserted word, not an invented
claim. Every anchor traced to a specific substrate claim id. The one `UNVERIFIED` anchor (Apollo's MCP idle time,
c:bf5bb9c0) was correctly worded as a test ("Does that timeline hold…?"). Several anchors went over 25 words.

After the anchor rule was tightened (verbatim from the raw pull + claim id), a **v2 stand-in** on the same input
produced 6 questions (2 → Seo, 2 → Boerner, 1 → Barnard, 1 → Lawson). Checker: **6/6 pass**, every anchor with its
claim id. Freshness got stricter: May claims were tagged `STALE` under the 60-day rule, where v1 had called them
`KNOWN`. Every STALE/UNVERIFIED question is worded as a test. The UNVERIFIED one is aimed at *resolving* the
Apollo GraphQL vs Apollo.io ambiguity rather than assuming either. The re-routing it did (the Lawson question)
led to the drop-don't-re-route rule in pre-mortem item 4.

The checker was validated against a planted bad fixture: a premise-shaped UNVERIFIED question, an invented
anchor, an invented target, and a missing trust tag. It failed all 3 questions, and it still fails the v1 inserted-word anchor.

**Acceptance run: owed by a FRESH session.** Inputs are staged, gitignored, in this worktree at
`.claude/.state/yed-217/` (the raw pull holds personal job-search rows, so it is not committed):

1. Open a new Claude Code session **in `esep-wt-conditioner`** (the edited agent must be on disk at startup).
2. Dispatch the **registered** `knowledge-conditioning` agent with `.claude/.state/yed-217/apollo_inputs.md`
   (it points to the raw pull).
3. Save the returned pack to `.claude/.state/yed-217/pack.md`, then:
   `python3 .claude/scripts/check_aimed_questions.py .claude/.state/yed-217/pack.md --invite .claude/.state/yed-217/apollo_invite.txt --raw .claude/.state/yed-217/apollo_substrate_raw.md`
4. Pass = ≥1 question aimed at Dale Seo or Dan Boerner, and 0 FAIL lines. Record the result on YED-217.
