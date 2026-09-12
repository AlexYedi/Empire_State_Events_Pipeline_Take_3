#!/usr/bin/env python3
"""OBS capture ETL — turn a raw OBS webinar recording into the granular value the
pipeline wants: a diarized speaker transcript + extracted slides + OCR'd slide text.

This is the "extract, don't flatten" step that replaced Clarify (whose API gave us only a
paraphrased summary). It generalizes the one-off `.claude/evals/run_scribe.py` into a reusable
recording -> transcript+slides pipeline. Recording lane / input contract is defined in
`.claude/references/obs-capture-setup.md`.

WHAT IT DOES
  1. ffprobe the recording (duration + audio-track count).
  2. Extract the SPEAKER audio track (OBS Track 2 = ffmpeg index 1) to 16 kHz mono WAV.
     Falls back to track 0 if the recording is single-track.
  3. Transcribe with ElevenLabs Scribe v2 (diarized, keyterm-seeded) -> JSON + diarized MD.
  4. Extract slides via ffmpeg scene-change detection (+ the first frame / title card).
  5. OCR each slide with tesseract -> a per-slide markdown sheet.
  6. Bundle everything under  event-transcripts/<event-slug>/ .

USAGE
  python3 .claude/tools/obs_ingest.py RECORDING.mp4 --event 2026-09-15_Some-Event [options]

  # slides + OCR only, no paid transcription:
  python3 .claude/tools/obs_ingest.py REC.mp4 --event 2026-09-15_X --no-transcribe

OPTIONS
  --event SLUG          output folder name (default: derived from the filename date).
  --speaker-track N     0-based ffmpeg audio index for the speaker track (default 1 = OBS Track 2).
  --num-speakers N      diarization speaker cap (default: let Scribe auto-detect).
  --keyterms PATH       JSON file {"keyterms": [...]} to seed Scribe (names/companies/jargon).
  --keyterms-list "a,b" inline comma-separated keyterms (merged with --keyterms if both given).
  --scene-threshold F   ffmpeg scene-change sensitivity 0..1 (default 0.30; lower = more slides).
  --no-transcribe       skip the paid Scribe step (slides + OCR only).
  --no-slides           skip slide extraction + OCR (transcript only).
  --outbase DIR         output base dir (default: event-transcripts/ under the repo root).
  --yes                 skip the paid-transcription confirmation prompt (required non-interactively).

ENV
  ELEVENLABS_API_KEY must be set (it lives in the repo .env). Requires: ffmpeg, ffprobe, tesseract,
  and the `elevenlabs` python SDK (pip install elevenlabs).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Repo root = three levels up from .claude/tools/obs_ingest.py
REPO_ROOT = Path(__file__).resolve().parents[2]


def die(msg: str, code: int = 1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def need(binary: str):
    if shutil.which(binary) is None:
        die(f"`{binary}` not found on PATH.")


def ffprobe_info(path: Path):
    """Return (duration_secs: float, audio_stream_count: int)."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=index,codec_type",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        die(f"ffprobe failed:\n{out.stderr}")
    data = json.loads(out.stdout)
    dur = float(data.get("format", {}).get("duration") or 0.0)
    n_audio = sum(1 for s in data.get("streams", []) if s.get("codec_type") == "audio")
    return dur, n_audio


def hms(secs: float) -> str:
    s = int(round(secs))
    return f"{s // 3600:d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


# ---------------------------------------------------------------------------
# Step 2 — extract the speaker audio track
# ---------------------------------------------------------------------------
def extract_audio(recording: Path, track: int, n_audio: int, workdir: Path) -> Path:
    if track >= n_audio:
        print(f"  ! requested speaker track {track} but recording has {n_audio} audio "
              f"track(s); falling back to track 0.")
        track = 0
    wav = workdir / "speakers_16k_mono.wav"
    print(f"  extracting audio track {track} -> {wav.name} (16 kHz mono)")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(recording), "-map", f"0:a:{track}",
         "-ac", "1", "-ar", "16000", "-vn", str(wav)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"ffmpeg audio extraction failed:\n{r.stderr[-2000:]}")
    return wav


# ---------------------------------------------------------------------------
# Step 3 — transcribe with Scribe v2, write JSON + diarized markdown
# ---------------------------------------------------------------------------
def load_keyterms(args) -> list:
    terms = []
    if args.keyterms:
        p = Path(args.keyterms)
        if not p.exists():
            die(f"--keyterms file not found: {p}")
        cfg = json.load(open(p))
        terms += cfg.get("keyterms", cfg if isinstance(cfg, list) else [])
    if args.keyterms_list:
        terms += [t.strip() for t in args.keyterms_list.split(",") if t.strip()]
    # de-dupe, preserve order
    seen, out = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def transcribe(wav: Path, keyterms: list, num_speakers, event: str, outdir: Path):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        die("ELEVENLABS_API_KEY not set (it lives in the repo .env).")
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        die("elevenlabs SDK not installed: pip install elevenlabs")

    client = ElevenLabs(api_key=key)
    print(f"  transcribing with scribe_v2 (keyterms={len(keyterms)}, "
          f"num_speakers={num_speakers or 'auto'}) ...")
    kwargs = dict(model_id="scribe_v2", timestamps_granularity="word")
    if keyterms:
        kwargs["keyterms"] = keyterms
    if num_speakers:
        kwargs["num_speakers"] = int(num_speakers)
    with open(wav, "rb") as f:
        r = client.speech_to_text.convert(file=f, **kwargs)
    data = r.model_dump() if hasattr(r, "model_dump") else dict(r)

    json_path = outdir / f"{event} — Transcript (Scribe v2).json"
    json.dump(data, open(json_path, "w"), indent=0)

    md_path = outdir / f"{event} — Transcript (Scribe v2).md"
    md_path.write_text(diarized_markdown(data, event))
    n_words = sum(1 for w in data.get("words", []) if w.get("type") == "word")
    print(f"  done: {n_words} words -> {md_path.name}")
    return md_path


def diarized_markdown(data: dict, event: str) -> str:
    """Group words into per-speaker turns, matching the existing
    '— Transcript (Scribe v2).md' format used across event-transcripts/."""
    words = data.get("words", [])
    dur = data.get("audio_duration_secs", 0) or 0
    mins = int(round(dur / 60)) if dur else 0
    speakers = sorted({w.get("speaker_id") for w in words if w.get("speaker_id")})
    n_words = sum(1 for w in words if w.get("type") == "word")

    turns, cur_spk, buf = [], None, []
    for w in words:
        if w.get("type") not in ("word", "spacing"):
            continue  # skip audio_event markers like [laughs] handling done inline by Scribe
        spk = w.get("speaker_id") or "speaker_?"
        if spk != cur_spk and w.get("type") == "word":
            if buf:
                turns.append((cur_spk, "".join(buf).strip()))
            cur_spk, buf = spk, [w.get("text", "")]
        else:
            buf.append(w.get("text", ""))
    if buf:
        turns.append((cur_spk, "".join(buf).strip()))

    lines = [f"# {event} — ElevenLabs Scribe v2 transcript", ""]
    meta = f"_scribe_v2 · diarized · ~{mins} min · {n_words} words · {len(speakers)} speakers_"
    lines += [meta, ""]
    for spk, text in turns:
        if text:
            lines.append(f"**[{spk}]** {text}")
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Steps 4 & 5 — slide extraction + OCR
# ---------------------------------------------------------------------------
def extract_slides(recording: Path, threshold: float, outdir: Path) -> list:
    slides_dir = outdir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    # First frame (title card) + every scene change above threshold.
    vf = f"select=eq(n\\,0)+gt(scene\\,{threshold}),showinfo"
    print(f"  extracting slides (scene threshold {threshold}) ...")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(recording), "-vf", vf, "-vsync", "vfr",
         str(slides_dir / "slide_%03d.png")],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        die(f"ffmpeg slide extraction failed:\n{r.stderr[-2000:]}")
    # showinfo prints one 'pts_time:<t>' per passed frame, in output order.
    pts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    slides = sorted(slides_dir.glob("slide_*.png"))
    print(f"  extracted {len(slides)} slides")
    return list(zip(slides, pts + [None] * (len(slides) - len(pts))))


def ocr_slides(slides_with_ts: list, event: str, outdir: Path):
    lines = [f"# {event} — slide OCR", "",
             "_ffmpeg scene-change keyframes, OCR'd with tesseract. Verify names/numbers "
             "against the video — OCR is lossy on stylized slides._", ""]
    for i, (img, ts) in enumerate(slides_with_ts, 1):
        r = subprocess.run(["tesseract", str(img), "stdout"],
                           capture_output=True, text=True)
        text = (r.stdout or "").strip()
        stamp = hms(ts) if ts is not None else "??:??:??"
        lines.append(f"## Slide {i:03d} · {stamp} · `{img.name}`")
        lines.append("")
        lines.append(text if text else "_(no text detected)_")
        lines.append("")
    ocr_path = outdir / f"{event} — Slides (OCR).md"
    ocr_path.write_text("\n".join(lines))
    print(f"  OCR -> {ocr_path.name}")
    return ocr_path


# ---------------------------------------------------------------------------
def derive_event_slug(recording: Path) -> str:
    m = re.search(r"(\d{4})[-_](\d{2})[-_](\d{2})", recording.stem)
    date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else datetime.now().strftime("%Y-%m-%d")
    return f"{date}_UNTITLED-rename-me"


def main():
    ap = argparse.ArgumentParser(description="OBS recording -> transcript + slides + OCR")
    ap.add_argument("recording", help="path to the OBS .mp4 recording")
    ap.add_argument("--event", help="event slug (default: derived from filename date)")
    ap.add_argument("--speaker-track", type=int, default=1,
                    help="0-based audio track index for speakers (default 1 = OBS Track 2)")
    ap.add_argument("--num-speakers", default=None, help="diarization speaker cap (default auto)")
    ap.add_argument("--keyterms", help="JSON file with a 'keyterms' list")
    ap.add_argument("--keyterms-list", help="inline comma-separated keyterms")
    ap.add_argument("--scene-threshold", type=float, default=0.30)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--no-slides", action="store_true")
    ap.add_argument("--outbase", default=str(REPO_ROOT / "event-transcripts"))
    ap.add_argument("--yes", action="store_true", help="skip paid-transcription confirmation")
    args = ap.parse_args()

    recording = Path(args.recording).expanduser().resolve()
    if not recording.exists():
        die(f"recording not found: {recording}")
    need("ffmpeg"); need("ffprobe")
    if not args.no_slides:
        need("tesseract")

    event = args.event or derive_event_slug(recording)
    outdir = Path(args.outbase).expanduser().resolve() / event
    outdir.mkdir(parents=True, exist_ok=True)
    dur, n_audio = ffprobe_info(recording)

    print(f"OBS ingest: {recording.name}")
    print(f"  duration {hms(dur)} · {n_audio} audio track(s)")
    print(f"  event    {event}")
    print(f"  output   {outdir}")

    # --- transcription (paid) ---
    if not args.no_transcribe:
        est_min = dur / 60
        print(f"\n  ⚠ Scribe v2 is a PAID transcription (~{est_min:.0f} min of audio).")
        if not args.yes:
            if not sys.stdin.isatty():
                die("paid step: re-run with --yes to confirm (non-interactive).")
            if input("  Proceed with transcription? [y/N] ").strip().lower() != "y":
                print("  skipping transcription.")
                args.no_transcribe = True
        if not args.no_transcribe:
            wav = extract_audio(recording, args.speaker_track, n_audio, outdir)
            keyterms = load_keyterms(args)
            transcribe(wav, keyterms, args.num_speakers, event, outdir)

    # --- slides + OCR ---
    if not args.no_slides:
        slides = extract_slides(recording, args.scene_threshold, outdir)
        if slides:
            ocr_slides(slides, event, outdir)

    print(f"\n✓ done. Bundle: {outdir}")
    print("  Feed the transcript + slide OCR into /post-event-content.")


if __name__ == "__main__":
    main()
