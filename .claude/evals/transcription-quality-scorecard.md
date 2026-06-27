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
| Agents Behaving Badly (06-25) | ✅ 24 MB m4a | ⚠️ **none** (file labeled "Transcript" is the Research Brief) | **4/6 = 67%** (scribe_v1) | **5/6 = 83%** (scribe_v2) | regraded 2026-06-27 (corrected scorer); see Regrade below |

## Result (2026-06-27): keyterms is the fix
Head-to-head on spoken proper nouns — plain `scribe_v1` vs `scribe_v2`+keyterms:
- **`Arklex`: "Arc"/"Archlex" (5 wrong, 0 right) → `Arklex` (correct, wrong variants gone).** The exact failure mode, fixed by biasing.
- `Kilian`, `Columbia`, `Datadog`: correct in both.
- `Zhou Yu`, `Meta Superintelligence`, `Lieret`: 0 in both — **never spoken aloud** (not a transcription miss).
- Note: `keyterms` **requires `scribe_v2`** (v1 returns a 400). Minor: Arklex correct-count was 1 vs 5 mangled mentions in v1 — worth a closer look if mention frequency matters, but the wrong variants are eliminated.
**Takeaway:** the proper-noun problem is real and `keyterms` (on scribe_v2, seeded from pre-event entities) solves it. The earlier "EL is worse" was an artifact of (a) scoring vs a research brief and (b) scoring unspoken names with an exact matcher.

## Regrade (2026-06-27) — corrected scorer, run via `score_entities.py`
Scorer rebuilt to the corrected method: **EL-plain vs EL+keyterms** (no real phone baseline — the "…Transcript.md" is the research brief), **spoken proper nouns only** (roster names never verbalized excluded), **variant-aware** (mangles do NOT count as hits).

| Transcript | Spoken-entity accuracy | Detail |
|---|---|---|
| EL plain (scribe_v1) | **4/6 = 67%** | Datadog ✓ · Columbia ✓ · Kilian ✓ · Arielle ✓ · **Arklex ✗** (mangled ×5: "Arc"/"Archlex") · **AccelGentic ✗** (absent) |
| EL +keyterms (scribe_v2) | **5/6 = 83%** | Arklex ✓ · Datadog ✓ · Columbia ✓ · Kilian ✓ · **AccelGentic ✓ (recovered)** · **Arielle ✗ (lost)** |

**Lift: +16 pts (67% → 83%).** keyterms recovered BOTH unusual names (Arklex, AccelGentic) — **but dropped "Arielle Mella"** (present in plain, absent in v2). Net +1, **not a pure win** — the prior "keyterms is the fix" was too clean.

**Caveats (honest):**
1. The Arielle miss may be a **spelling variant** the matcher didn't catch ("Ariel"/"Ariella"), not a true regression — needs a 30-sec spot-check of the v2 transcript.
2. **"Spoken" is inferred from transcript presence, NOT the .m4a** (no audio access here). A 2–3 min hand-checked gold slice from the recording would harden the ground truth.
3. Excluded as never-spoken (research-brief-only): Meta Superintelligence, Zhou Yu, John Mark, Yi Ju, Lieret.

**Action (value-action contract):** keep `keyterms` as the default for proper-noun-heavy events; **add "Arielle/Mella" + host names to the keyterms seed and re-run** to confirm the drop is a seeding gap, not a keyterms artifact. Promote excluded names into the seed only if a gold slice shows they were spoken.

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
