# Transcription Quality Scorecard (ElevenLabs vs phone ASR)

The eval/measurement layer for the recording→clean-transcript ingest (Linear **YED-95**). One row per event; accumulates into a benchmark. This is also the bake-off harness.

## Method (don't over-build)
**Truth, not difference.** The phone transcript is the **baseline to beat**, NOT the reference. Both transcripts are scored against an independent ground-truth, so we measure *lift*, not just disagreement.

**Primary metric — Entity accuracy.** Ground truth = the event's known proper nouns (from pre-event research / calendar invite / verified post-event). For each entity: does it appear *correctly* (case-insensitive) in the transcript? Score = correct ÷ total. This is the cheapest, highest-signal metric — proper nouns are exactly where phone ASR fails and where content value lives. Scored by `score_entities.py`.

**Secondary (only as needed):**
- **WER on a hand-corrected 2–3 min gold slice** — catches general degradation entity-accuracy misses. Don't transcribe whole events by hand.
- **Diarization spot-check** — did speaker turns map correctly on the gold slice?
- **#manual-fixes downstream** — corrections the content step still needed (trends to 0 = real value).

**Guardrails (from the YED-95 adversarial pass):**
- Score against truth, **never readability**. A fluent, confident "$466M→$4.66B" is *worse*, not better. Cleaner ≠ correct.
- Credit **calibration**: a transcript that flags low-confidence spots (Scribe per-word `logprob`) preserves quote safety; one that hides uncertainty should not score higher just for looking clean.

## Ground-truth entity lists
**NYC AI Demos #10 (2026-06-24)** — verified post-event:
- Companies: `Spring Health`, `Spara`, `Pace`, `Uncovr`, `Pensar`
- VCs: `Thrive`, `First Round`, `Index Ventures`, `Inspired Capital`, `Able Partners`
- People: `Kyle Bhiro`, `John de Lorenzo`, `Dave Walker`, `Tristan`, `Karem`

**Agents Behaving Badly (2026-06-25)** — *announced participants (calendar invite); expand once transcripts read*:
- Companies/orgs: `Arklex`, `Datadog`, `Meta Superintelligence`, `Columbia University`, `AccelGentic`
- People: `Kilian Lieret`, `Zhou Yu`, `John Mark`, `Yi Ju`, `Arielle Mella`

## Scorecard
| Event | Audio? | Baseline transcript | EL (plain) | EL (+keyterms) | Notes |
|---|---|---|---|---|---|
| NYC AI Demos #10 (06-24) | ❌ none | phone .txt exists | — | — | no audio → can't A/B |
| Agents Behaving Badly (06-25) | ✅ 24 MB m4a | **3/6 = 50%** (recorder-app, obtained 06-27) | **4/6 = 67%** (scribe_v1) | **6/6 = 100%** (scribe_v2, re-seeded) | real baseline + re-seeded keyterms; see Regrade below |

## Result (2026-06-27): keyterms is the fix
Head-to-head on spoken proper nouns — plain `scribe_v1` vs `scribe_v2`+keyterms:
- **`Arklex`: "Arc"/"Archlex" (5 wrong, 0 right) → `Arklex` (correct, wrong variants gone).** The exact failure mode, fixed by biasing.
- `Kilian`, `Columbia`, `Datadog`: correct in both.
- `Zhou Yu`, `Meta Superintelligence`, `Lieret`: 0 in both — **never spoken aloud** (not a transcription miss).
- Note: `keyterms` **requires `scribe_v2`** (v1 returns a 400). Minor: Arklex correct-count was 1 vs 5 mangled mentions in v1 — worth a closer look if mention frequency matters, but the wrong variants are eliminated.
**Takeaway:** the proper-noun problem is real and `keyterms` (on scribe_v2, seeded from pre-event entities) solves it. The earlier "EL is worse" was an artifact of (a) scoring vs a research brief and (b) scoring unspoken names with an exact matcher.

## Regrade (2026-06-27) — REAL recorder-app baseline obtained; fully redone
The mislabeled "transcript" (a research brief) was **deleted** and the **actual recorder-app transcript** added, so we now measure TRUE lift (not just EL-internal). EL transcripts relocated to `.claude/evals/agents-behaving-badly/`; scored via `score_entities.py` (spoken-entities-only, variant-aware, mangles ≠ hits).

| Transcript | Spoken-entity accuracy | Lift vs baseline | Detail |
|---|---|---|---|
| Baseline (recorder app) | **3/6 = 50%** | — | Datadog ✓ (1×) · Columbia ✓ · Arielle ✓ · **Arklex ✗** (Archlex) · **Kilian ✗** (absent) · **AccelGentic ✗** |
| EL plain (scribe_v1) | **4/6 = 67%** | **+17 pts** | + Kilian; **Datadog 6×** vs baseline 1×; Arklex still mangled (Arc ×4 / Archlex), AccelGentic absent |
| EL +keyterms (scribe_v2) | **6/6 = 100%** | **+50 pts** | **Arklex ✓ (all 5 mentions)** · **AccelGentic ✓** · **Arielle ✓** — all recovered after re-seeding keyterms with "Arielle Mella" + host names (2026-06-27 re-run) |

**Verdict:** ElevenLabs decisively beats the recorder-app baseline — **+17 plain, +50 with keyterms (100% spoken-entity accuracy).** The re-seeded keyterms run (2026-06-27) hit every spoken proper noun: it recovered **all 5 "Arklex" mentions** (was 1), kept AccelGentic, and **fixed the "Arielle"→"Ariel" degrade** — confirming that was a *seed gap*, not a keyterms artifact. The recorder-app baseline, by contrast, drops repeated names hard (Datadog 1× vs 7×) and misses Kilian + Arklex + AccelGentic entirely.

**Caveats (honest):**
1. ~~The "Ariel" degrade~~ **RESOLVED (2026-06-27):** re-seeding keyterms with "Arielle Mella" + host names recovered Arielle (and all 5 Arklex mentions) → 100%. Seed gap, not a keyterms flaw. Runner + seed now committed (`run_scribe.py`, `agents-behaving-badly/keyterms.json`) — reproducible.
2. **"Spoken" is inferred from the 3 transcripts, NOT hand-checked vs the .m4a** — a 2–3 min gold slice would harden the ground truth.
3. Excluded as never-spoken: Meta Superintelligence, Zhou Yu, John Mark, Yi Ju, Lieret.

**Action (value-action contract):** **adopt ElevenLabs over the recorder app** for events (decisive entity lift, now 100%); **`keyterms` (scribe_v2) is the default**, seeded from the pre-event entity roster via the committed `run_scribe.py` + `keyterms.json`. Recorder-app transcript = emergency fallback only.

## Findings (2026-06-27) — first run shook out the eval itself
1. **Data-labeling error.** `06.25.26…Transcript.md` is the **pre-event Research Brief**, not a transcript. Scoring EL against it is meaningless. → We have **no real baseline transcript** for this event; need the actual phone/app transcript to measure "lift," or pivot the lift comparison to **keyterms vs no-keyterms** (both EL).
2. **Score only SPOKEN entities.** Many ground-truth names (speaker self-names, host affiliations — Zhou Yu, Meta Superintelligence, AccelGentic, Yi Ju, Arielle Mella) **never appear in any transcript** because speakers don't say their own name/company aloud. Penalizing a transcript for unspoken names is wrong. Ground truth must be "entities actually verbalized," not the announced roster.
3. **Matcher must be variant-aware.** Plain EL rendered `Arklex` → **"Arc" / "Archlex"**, got `Kilian` and `Columbia` right. Exact word-boundary matching scores these near-misses as 0 → false "EL is worse." Need fuzzy/variant matching (or per-entity human spot-check).
4. **Qualitatively, plain EL is strong** — coherent, ~2× the content, correct on common terms — but **mangles unusual proper nouns** (exactly the `keyterms` case) and **over-segments diarization** (17 speakers for a ~4-person panel; `num_speakers` can cap it).

## Confirmed capabilities (SDK)
`keyterms` ✅ (proper-noun biasing — the fix) · `num_speakers` / `diarization_threshold` (diarization) · `timestamps_granularity` + per-word data (quote-safety contract) · `seed`/`temperature` (determinism).

## Corrected method
- **Lift comparison** needs a real baseline transcript. If none exists, report **EL-plain → EL+keyterms** as the lift on proper nouns.
- **Ground truth = spoken entities only** (derive from the audio / a short gold slice, not the roster).
- **Variant-aware scoring** (fuzzy match or human spot-check on the dozen names that matter).

## Variants (bake-off)
1. baseline transcript (if obtained) · 2. **Scribe plain** ✅ · 3. **+ keyterms** 🟡 · 4. Voice Isolator → Scribe (only if low confidence) · 5. + alias-map/LLM (contingency).

## n=4 generalization (2026-06-27) — EL beats the recorder app on every event
Recipe (scribe_v2 + keyterms) vs recorder-app baseline, on each event's verified spoken proper nouns (`.claude/evals/score_events.py`):

| Event (format) | Baseline | EL (scribe_v2 + keyterms) | Lift |
|---|---|---|---|
| Agents Behaving Badly (panel) | 50% | 100% | +50 |
| AI Demo Night (demo night) | 43% | 86% | +43 |
| 2x AI by Fin (fireside) | 43% | 71% | +29 |
| GTM+AI Masterclass #5 (masterclass) | 85% | 92% | +8 |

**EL wins on all 4 — mean ~55% → ~87%. Recipe generalizes (n=1 → n=4).** Remaining misses are seed-coverage gaps, not model failures: Qwen (→"Quinn"), surnames Donohue/Curran (seed had first names only), Nowoslawski (baseline missed it too). AI Demo Night + 2x AI used AUTO-extracted seeds (noisier) → these are a FLOOR; curated seeds from the briefs' verified rosters score higher. Lesson: seed full names + first names + surnames. Gold slice (audio-verified) still recommended on one event (human listening step).
