# media_client: brand tokens + vendor compare mode

**Linear:** YED-252 · **Date:** 2026-09-30 · **Owner:** Alex · **Status:** approved · **Appetite:** 3-7d · **Backfilled?** no

## 1. Problem & why now
The feed is safe and text-only. Of 50 posts, 29 are text and 21 are PDF carousels; 0 carry a photo, video or audio. Alex's 2026-09-28 read was "sooo safe, no soul." Pictorial work stays manual ("Claude writes the prompt; Alex generates", `visual-briefs.md`), so it doesn't happen. Why now: Alex connected Runway, Higgsfield, Canva, Gamma, Mobbin, Magic Patterns and ElevenLabs on subscription credits (Lenny's bundle). The 2026-09-29 test showed a still → clip chain works, and that two rules matter: declare the frame once, and fast video drifts.

*Press release:* "Every post can ship with on-brand imagery or motion. Alex picks from 2-3 blind candidates in under 5 minutes at $0 marginal cost, and a scorecard shows which tools are worth keeping."

## 2. Goals / Non-goals
**Goals**
- One brand-tokens file that every vendor receives, translated into each vendor's own input format.
- Compare mode: the same spec goes to a near-raw control plus 2 vendor harnesses; Claude screens; Alex picks blind.
- A scorecard and credit ledger that make vendor pruning a matter of evidence.
- $0 marginal spend: subscription credits only.

**Non-goals**
- Publishing or scheduling (LinkedIn, Higgsfield TikTok publish). Alex publishes.
- Any pay-per-use API (the Gemini API key, Runway or Higgsfield developer APIs).
- Dense, technical or labelled slides. Claude HTML/SVG keeps them, unchanged.
- Higgsfield Soul likeness and the voice pick (deferred to their own steps).
- Video longer than 8 s; multishot editing; Runway workflows.
- Automatic vendor removal. Pruning is surfaced to Alex, never applied silently.

## 3. Solution sketch + alternatives
**Chosen.** `brand-tokens.yaml` holds palette, type, image-style prompt blocks with a reference image, frame rules, screening rules and per-vendor translation. `media_client.py compile <spec>` emits one request per backend. Gemini and ElevenLabs are called directly (only they have keys). For the claude.ai connectors (Runway, Higgsfield, Canva, Gamma, Magic Patterns), Claude runs the compiled request in the parent thread. `media_client.py ingest` downloads the result next to its spec, crops it to the declared frame, and appends to `scorecard.jsonl`.

**Alternatives rejected**
- *Compare models, not vendors* (Fable's first pass). Rejected by Alex: each vendor is a bet on its harness, so we test harnesses against the raw model and prune empirically.
- *Paid Gemini API as the control.* Breaks the $0 rule. Replaced by Runway's `generate_image` passthrough (no presets; `gemini-3-pro-image` underneath, confirmed 2026-09-30), plus ~1 in 5 runs re-run by Alex in the Gemini app to check the passthrough stays raw.
- *Python calls every vendor.* Not possible: the connectors are OAuth-only, with no local keys.
- *All connected tools on every run.* Too much spend and screening load; capped at control + 2.

## 4. Leverage & systems check
- **Leverage point:** information flows (#6). The scorecard routes "which harness adds value" back to the decider, and it is the mechanism that keeps tool sprawl from growing unnoticed. Direction check: it should reduce the tool count over time, not raise it.
- **Archetype guarded:** *Seeking the Wrong Goal.* Claude's screening rank could become the goal, so Alex's blind pick is the ground truth and Claude's rank is logged separately. *Shifting the Burden:* generation moves from Alex's hands into the pipeline, with Alex left with only the pick.

## 5. Rabbit holes + pre-mortem
**Rabbit holes:** per-vendor aspect-ratio support (Runway NB Pro has no 4:5); async polling differs by vendor; Canva and Gamma return editable designs, not images, so they need an export step; credit costs aren't uniformly preflightable.

**"It's November and this is a regret, because…"**
1. *Nobody runs it.* Compare mode is too slow or too fiddly. Fix: one command plus a single 3-up preview; target ≤5 min of Alex's time per pick.
2. *The scorecard never reaches 8 head-to-heads per format,* so pruning never fires. Fix: count per format, and flag stale formats monthly.
3. *Credits drain silently.* Fix: a pre-run balance check per vendor, a hand-kept cost table for vendors without preflight (marked "verify monthly"), and a hard stop with the Gemini-app fallback when every vendor is short.

## 6. Success criteria + eval
- **North star:** share of published posts carrying generated or field imagery, video or audio. Baseline 0/50. {< 20% of posts after 4 weeks → interview Alex on which step blocks}.
- **Harness value per vendor:** vendor win rate against the control in blind picks. Null baseline 50% (the harness adds nothing). {after 8 head-to-heads in a format, never picked and ≤ 25% wins → surface for removal}.
- **Counter-metrics:** Alex's minutes per pick (≤ 5); credits per published asset; zero pay-per-use API calls.
- **Acceptance criteria**
  - [ ] `brand-tokens.yaml` validates; it contains signature `#8FE83A`, bg `#111418`, the topic accents and both style blocks, and the line-art reference image is committed.
  - [ ] `compile` emits a request per backend whose frame matches the spec, with a crop step logged when the vendor lacks the ratio.
  - [ ] `ingest` saves the asset beside its spec and appends a scorecard row (format, vendor, model, credits, seconds, blind label, Claude rank, Alex pick).
  - [ ] No code path calls a pay-per-use API; a grep test enforces this.
  - [ ] When every vendor is short of credits, the run stops and prints the Gemini-app prompt.
  - [ ] Screening rejects candidates with lettering when the spec says no text.
  - [ ] End-to-end: the 2026-09-29 media-chain scene is rerun at 9:16 with a Kling alternate, giving the "fixed" half of the 30-second demo.
  - [ ] `visual-briefs.md` and `platform-constraints.md` are updated (Gamma and Canva "on trial since 2026-09-30").

## 7. AI-native fields
- **Human-AI boundary:** Claude compiles, runs, screens and recommends; Alex picks, approves any batch over the per-run cap, and approves every removal.
- **Failure UX:** a candidate that fails screening is shown greyed out with its reason, never silently dropped.
- **Built for the slope:** models are named in the vendor tables, not hardcoded in the logic; new models enter through the scorecard.

## 8. Build-time details (deferred)
Spec file format (YAML or JSON) · scorecard path and retention · crop method (Pillow centre-crop or smart-crop) · polling intervals · how the "no lettering" check works (Claude vision or OCR) · per-run credit cap value.

## 9. Invariants honored
CLAUDE.md §4.4 (no secrets; prompts and generated PNGs are fine to commit, `.mp4` stays gitignored) · §4.5 (connector actions run in the parent thread only) · §5 null-baseline rule · §5 one-in-one-out (in: `media_client.py` + `brand-tokens.yaml`; out: the "Claude writes the prompt; Alex generates" manual step in `visual-briefs.md`) · `platform-constraints.md` tombstone rows.

## 10. Decision log
- `2026-09-30` — compare vendors (harnesses), not just models, against a near-raw control; prune by scorecard — Alex's harness-layer thesis — supersedes Fable's "compare models, not vendors".
- `2026-09-30` — $0 rule: subscription credits only; when all are out, surface and hand over a Gemini-app prompt — Lenny's bundle covers the vendors — supersedes the paid Gemini API route proven 2026-09-29.
- `2026-09-30` — control = Runway passthrough plus a ~1-in-5 Gemini-app check (option C) — automatic, with periodic proof that it is raw.
- `2026-09-30` — blind A/B/C picks; prune after 8 head-to-heads, never picked and ≤ 25% wins; control + 2 vendors per run.
- `2026-09-30` — brand: keep the dark editorial base; signature acid green `#8FE83A` (key-word underline + name mark); keep the topic accents in diagrams; ice blue tried and dropped; photo-real for events, editorial line art for ideas (chosen from 3 previews at 20 Runway credits each).
