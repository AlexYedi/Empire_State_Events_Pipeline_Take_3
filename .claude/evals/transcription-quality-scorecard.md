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
| Event | Audio? | Entity acc — phone | Entity acc — ElevenLabs | Lift | Notes |
|---|---|---|---|---|---|
| NYC AI Demos #10 (06-24) | ❌ no recording | _pending score_ | — (no audio) | — | baseline-only; can't A/B without audio |
| Agents Behaving Badly (06-25) | ✅ 24 MB m4a | _pending score_ | _pending (EL run in progress)_ | _tbd_ | first live A/B; plain Scribe v1 + diarize (no keyterms yet) |

## Variants to test (bake-off — incremental, manage credits)
1. **phone** (baseline) · 2. **Scribe raw + diarize** (this run) · 3. **+ keyterms** (raw-API biasing, seeded from ground-truth list) · 4. **Voice Isolator → Scribe** (only if low confidence) · 5. **+ alias-map / LLM pass** (contingency).
Run 1↔2 first (answers "does EL lift?"); add 3 if residual proper-noun errors; 4/5 only if needed.
