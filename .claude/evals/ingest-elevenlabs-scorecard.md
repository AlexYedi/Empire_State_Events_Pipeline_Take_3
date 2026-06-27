# Ingest Eval — ElevenLabs Scribe recipe (n=4)
**Date:** 2026-06-27 · **Relates to:** YED-95 (recording→clean-transcript ingest)
**Recipe under test:** `model_id=scribe_v2` + `diarize=true` + `num_speakers` (cap) + `timestamps_granularity=word` + `keyterms` (≤1000).

## Events tested
| Event | Format | Existing transcript | ElevenLabs result |
|---|---|---|---|
| Agents Behaving Badly (06/25) | roundtable | none (pre-event brief only) | 64 min · v1 baseline 22 speakers → **v2+keyterms+num_speakers = 5**; SWE-bench 0→7 |
| AI Demo Night (05/21) | demo night | **already ElevenLabs** | 44 min · 6 speakers · reproducibility check |
| NYC GTM+AI Masterclass #5 (06/03) | masterclass | **rougher legacy ASR** | 120 min · 6 speakers · **lift case** |
| 2x AI by Fin (06/04) | workshop | **already ElevenLabs** | 50 min · 6 speakers · reproducibility check |

## Scores

**Reproducibility (ElevenLabs vs ElevenLabs)** — near-identical entity capture, confirming the recipe is stable:
- 05/21: cBioPortal 4/4 · Google Cloud 9/9 · Red Hat 9/9 · RoleMate 13/13 · Whisper 3/3 (GitHub 13/14, MCP 2/3).
- 06/04: Claude 33/37 · Anthropic 5/6 · RAG 11/12 · Fin 31/30 · agentic 4/4.

**Lift (vs rougher legacy ASR — 06/03)** — ElevenLabs captured **2–3× more** of the domain vocabulary:
| Entity | legacy ASR | ElevenLabs |
|---|---|---|
| Insight Partners | 3 | 7 |
| Sangram | 2 | 6 |
| Clay | 6 | 11 |
| ICP | 7 | 11 |
| ABM | 3 | 8 |
| go-to-market | 1 | 54 |
| Tech Week | 2 | 4 |

The legacy ASR had nearly **lost the core term of a *go-to-market* masterclass** (1 vs 54 — partly hyphenation, but directionally stark). ElevenLabs also captured ~25% more total content (legacy ~16.9k words vs ElevenLabs ~21k).

## Findings
1. **Recipe validated across 4 formats** (roundtable, demo night, masterclass, workshop); consistent 5–6-speaker diarization with `num_speakers` capping the over-segmentation seen in the v1 baseline.
2. **Reproducible** — two ElevenLabs runs on the same audio yield near-identical entity capture.
3. **Clear lift over weaker ASR** — where a real legacy baseline existed (06/03), ElevenLabs materially improved coverage and proper-noun fidelity.
4. **Keyterm AUTO-extraction from the transcript is poor** — it pulled filler ("Um", "Uh", "Speaker", "Okay. So"). **→ The template must seed keyterms from the curated entity list (pre-event research → People/Companies DB), as ABB did — not regex over the transcript.** Biggest design takeaway.
5. Diarization caps speakers well, but **content-attribution for briefs still needs care** (raw speaker IDs ≠ people on a multi-voice stage).

## Implication for Phase B (templatize)
- **Lock the recipe:** scribe_v2 + diarize + num_speakers + word timestamps + **keyterms sourced from the event's curated entity list**.
- Two of three "existing" transcripts were already ElevenLabs → Alex is effectively on the recipe; standardizing it in `/post-event-content` formalizes what's already working.
- This file is the seed of the ingest **eval corpus** for the measurement layer.
