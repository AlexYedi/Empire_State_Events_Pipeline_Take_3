---
description: "Turn an event recording (.m4a) into a clean, diarized, proper-noun-correct transcript (ElevenLabs scribe_v2 + roster-seeded keyterms) that feeds /post-event-content. Use after an event once the audio is in the event folder — beats the recorder-app transcript by ~50pts on spoken proper nouns. Manual command, not a folder-watch."
argument-hint: "[audio path in the event folder; optional --num-speakers N; --slides-dir to align slide photos — keyterms auto-seed from the event roster]"
---

# /ingest-recording — recording → clean transcript (YED-95)

Turn an event recording into a clean, diarized, proper-noun-correct transcript that feeds
`/post-event-content`. Replaces the recorder-app transcript (proven +50pts on spoken proper
nouns: 100% vs 50% on the Agents Behaving Badly bake-off). **Manual command, not a folder-watch.**

## When
After an event, once the `.m4a`/audio is in the event folder. Prereq: `ELEVENLABS_API_KEY` in the
repo `.env` (Creator tier). Recipe is locked in `.claude/scripts/ingest_recording.py`.

## Steps
1. **Build the keyterms seed** from the event's pre-event research entities (Notion People +
   Companies for that event, or the research brief). **Seed BOTH full names AND first names** —
   e.g. `Arielle Mella` *and* `Arielle` (the spoken form is often first-or-last-name only).
   - **Auto path (inside `/post-event-content`):** the roster is pulled from the Step-1 Notion
     Event record (related People + Companies) → written to a temp keyterms file. Pass
     **`--expand-names`** so the script also seeds first/last tokens automatically (covers the
     *Arielle / Donohue / Curran* surname-or-first-name-only misses).
   - **n=4 finding:** auto-extracted seeds are a *floor* — a curated roster seed (clean speaker +
     company names) scores higher. Use the Notion roster when available.
2. **Run the recipe** (from the repo root):
   ```bash
   set -a; source ./.env; set +a
   uv run --with elevenlabs --with pillow python .claude/scripts/ingest_recording.py \
     --audio "Event Content/<event folder>/<recording>.m4a" \
     --keyterms "Arklex,Arielle,Datadog,Kilian Lieret,Kilian,AccelGentic,..." \
     [--num-speakers N] \  # set if diarization over-segments (scribe_v2 tends to)
     [--slides-dir "Event Content/<event folder>"]   # default ON whenever the folder has slide photos
   ```
   Locked config (do not change without a fresh bake-off): `model=scribe_v2` (required for
   keyterms) · `diarize=True` · `timestamps_granularity=word`.
3. **Outputs land next to the audio:**
   - `… — Transcript (ElevenLabs).md` — diarized `[speaker] (mm:ss)` blocks → paste into `/post-event-content` (Step 3.5).
   - `… — Transcript (ElevenLabs).json` — full word-level data (timestamps + logprob).
   - `… — REVIEW (low-confidence spots).md` — the **quote-safety guard**.
   - `slide-recording-alignment.md` / `.json` (with `--slides-dir`) — each slide photo → its
     recording offset + the ±45 s of transcript around it (YED-166).
4. **Quote-safety contract (R1 — do not skip).** Before any verbatim quote ships, check it against
   the REVIEW list: low-confidence words are flagged with a timestamp → click-to-hear to verify.
   A clean transcript must *raise* quote safety, not replace the paraphrase discipline. If no
   keyterms seed was available, treat the transcript as `UNVERIFIED` and keep paraphrase-only.

5. **Slide alignment + confirm pass (YED-166 — do not skip when photos exist).**
   - **How the offset is computed:** recording start = the audio container's `creation_time`
     (Android recorders write it when recording *stops*, so start = stamp − duration; other apps
     write it at start). The script tries both and keeps the one that puts more photos inside the
     recording. Photo time = EXIF capture time (with its timezone offset) → filename (`PXL_…` is
     UTC) → file mtime (LOW). Offset = photo time − start.
   - **Confirm pass (Claude, in the parent thread):** for each aligned photo, view the image next to
     its context block and mark it *matched* (the speaker is discussing that slide) or *mismatched*.
     Record the tally in the brief's Slides Catalog. **Any mismatch → the start is wrong:** re-run
     `align_slides.py` alone with `--recording-start <ISO time>` (or `--creation-time-is start|end`),
     no re-transcription needed. If the camera and recorder were different devices, use
     `--offset-seconds` for clock skew.
   - **LOW confidence or ⚠️ unaligned photos** (taken before/after the recording) → confirm pass is
     mandatory, and unaligned photos stay in the catalog without an offset. Never force-fit them.
   - Re-run alone (free, offline):
     ```bash
     uv run --with pillow python .claude/scripts/align_slides.py \
       --transcript "Event Content/<event>/<stem> — Transcript (ElevenLabs).json" \
       --audio "Event Content/<event>/<recording>" --slides-dir "Event Content/<event>"
     ```
     `python .claude/scripts/align_slides.py --selftest` pins the 2026-09-16 reference case.
   - Offsets **locate** a quote; they do not license quoting it verbatim. The R1 contract (step 4) still applies.

## Notes / gotchas
- `keyterms` **requires `scribe_v2`** (scribe_v1 → HTTP 400).
- Diarization labels are anonymous (`speaker_0…`) and scribe_v2 over-segments — map Speaker→name
  with the pre-event People list (a <5-min human pass); use `--num-speakers` to help.
- The recording's file extension can lie: the 2026-09-16 phone export was an MP4/AAC container named
  `.mp3`. `ffprobe` reads it regardless; `afinfo`/Spotlight may not.
- This calls ElevenLabs via the SDK script directly (not the MCP) — the MCP isn't required.
- Eval: re-score each event with `.claude/evals/score_entities.py` (spoken-only, variant-aware) to
  keep the scorecard growing. The eval now runs on production output, not n=1.
