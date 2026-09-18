#!/usr/bin/env python3
"""align_slides.py — map slide photos to their offset in an event recording (Linear YED-166).

Proven by hand on Postgres Tuning in the Age of AI (2026-09-16): 11/11 photos landed on the
moment the speaker was talking about that slide. This script is that method, made repeatable.

How it works:
  recording_start  = container creation_time (±duration, see below)  |  --recording-start override
  photo_time       = EXIF DateTimeOriginal(+OffsetTimeOriginal) | filename pattern | file mtime
  offset           = photo_time - recording_start      (all times timezone-aware UTC)
  context          = transcript words within ±--context-seconds of the offset

The start/end ambiguity: Android recorders write the container creation_time when recording
STOPS; other apps write it at START. `--creation-time-is auto` (default) tries both and keeps the
interpretation that puts more photos inside [start, start+duration]. If both fit equally, the
result is marked LOW confidence — the visual confirm pass in /ingest-recording is mandatory then.

No paid API calls — re-run freely without re-transcribing.

Outputs (next to the transcript, or --out):
  slide-recording-alignment.md    human table + ±N s transcript context per photo
  slide-recording-alignment.json  machine-readable (for the post-event brief's Slides Catalog)

Usage:
  uv run --with pillow python .claude/scripts/align_slides.py \
      --transcript "<event>/<stem> — Transcript (ElevenLabs).json" \
      --audio "<event>/<recording>.m4a" --slides-dir "<event>"
      [--recording-start 2026-09-16T18:32:04-04:00] [--creation-time-is auto|start|end]
      [--offset-seconds 0] [--context-seconds 45] [--tz America/New_York]
  python .claude/scripts/align_slides.py --selftest
"""
import argparse, datetime as dt, json, os, re, subprocess, sys
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}
DUP_SECONDS = 3


def fmt_off(s):
    if s is None:
        return "—"
    sign = "-" if s < 0 else ""
    s = int(round(abs(s)))
    return f"{sign}{s // 60:02d}:{s % 60:02d}"


# ---------- recording start ----------

def probe_audio(path):
    """Return (duration_seconds, creation_time_utc | None, is_android) via ffprobe; (None, None, False) if unavailable."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags",
             "-of", "json", path], capture_output=True, text=True, timeout=60)
        fmt = json.loads(out.stdout or "{}").get("format", {})
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None, None, False
    dur = float(fmt["duration"]) if fmt.get("duration") else None
    tags = {k.lower(): v for k, v in (fmt.get("tags") or {}).items()}
    ct = None
    if tags.get("creation_time"):
        try:
            ct = dt.datetime.fromisoformat(tags["creation_time"].replace("Z", "+00:00")).astimezone(UTC)
        except ValueError:
            ct = None
    return dur, ct, "com.android.version" in tags


def in_window(times, start, dur):
    end = start + dt.timedelta(seconds=dur)
    return sum(1 for t in times if start <= t <= end)


def resolve_start(creation_time, duration, photo_times, mode="auto", is_android=False):
    """Pick the recording start from a container creation_time. Returns (start, basis, confidence, votes)."""
    as_start = creation_time
    as_end = creation_time - dt.timedelta(seconds=duration)
    votes = {"start": in_window(photo_times, as_start, duration),
             "end": in_window(photo_times, as_end, duration)}
    if mode == "start":
        return as_start, "creation_time = start (forced)", "MED", votes
    if mode == "end":
        return as_end, "creation_time = end (forced)", "MED", votes
    n = len(photo_times)
    if votes["start"] == votes["end"]:
        pick = "end" if is_android else "start"
        conf = "LOW" if n else "UNKNOWN"
        why = f"tie ({votes['start']}/{n} in window either way); defaulted to {pick} ({'Android' if is_android else 'non-Android'} container)"
    else:
        pick = max(votes, key=votes.get)
        loser = "start" if pick == "end" else "end"
        conf = "HIGH" if votes[pick] == n and votes[loser] < n else "MED"
        why = f"in-window vote {pick} {votes[pick]}/{n} vs {loser} {votes[loser]}/{n}"
    return (as_end if pick == "end" else as_start), f"creation_time = {pick}: {why}", conf, votes


# ---------- photo time ----------

PXL_RE = re.compile(r"PXL_(\d{8})_(\d{6})(\d{3})?")                 # Google Pixel: UTC
LOCAL_RE = re.compile(r"(?:IMG|VID|Photo)?[_-]?(\d{8})[_-](\d{6})")  # IMG_20260916_184057 etc: local


def exif_time(path, local_tz):
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        try:
            import pillow_heif  # optional HEIC support
            pillow_heif.register_heif_opener()
        except ImportError:
            pass
        ex = Image.open(path).getexif()
        sub = ex.get_ifd(0x8769)
        raw = sub.get(36867) or ex.get(306)          # DateTimeOriginal, else DateTime
        if not raw:
            return None
        t = dt.datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
        off = sub.get(36881) or sub.get(36880)        # OffsetTimeOriginal, else OffsetTime
        if off and re.fullmatch(r"[+-]\d{2}:\d{2}", str(off).strip()):
            t = dt.datetime.fromisoformat(t.isoformat() + str(off).strip())
        else:
            t = t.replace(tzinfo=local_tz)
        return t.astimezone(UTC)
    except Exception:
        return None


def filename_time(name, local_tz):
    m = PXL_RE.search(name)
    if m:
        d, hms, ms = m.group(1), m.group(2), m.group(3) or "000"
        return dt.datetime.strptime(d + hms, "%Y%m%d%H%M%S").replace(
            microsecond=int(ms) * 1000, tzinfo=UTC)
    m = LOCAL_RE.search(name)
    if m:
        try:
            return dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S").replace(
                tzinfo=local_tz).astimezone(UTC)
        except ValueError:
            return None
    return None


def photo_time(path, local_tz):
    t = exif_time(path, local_tz)
    if t:
        return t, "exif"
    t = filename_time(os.path.basename(path), local_tz)
    if t:
        return t, "filename"
    return dt.datetime.fromtimestamp(os.path.getmtime(path), UTC), "mtime (LOW — often the copy time)"


# ---------- alignment ----------

def align(photos, start, duration, words, context_seconds):
    """photos: list of dicts {name, time(UTC), source}. Returns rows sorted by time."""
    rows, prev = [], None
    for p in sorted(photos, key=lambda p: p["time"]):
        off = (p["time"] - start).total_seconds()
        inside = 0 <= off <= duration if duration else off >= 0
        row = {"photo": p["name"], "taken_utc": p["time"].isoformat(), "time_source": p["source"],
               "offset_seconds": round(off, 1), "offset": fmt_off(off), "in_window": inside,
               "near_duplicate_of": None, "speakers": {}, "context": ""}
        if prev and (p["time"] - prev["time"]).total_seconds() <= DUP_SECONDS:
            row["near_duplicate_of"] = prev["name"]
        if inside:
            win = [w for w in words if off - context_seconds <= (w.get("start") or 0) <= off + context_seconds]
            for w in win:
                k = w.get("speaker_id") or "?"
                row["speakers"][k] = row["speakers"].get(k, 0) + 1
            row["context"] = " ".join((w.get("text") or "").strip() for w in win).strip()
        rows.append(row)
        prev = p
    return rows


def render_md(meta, rows, local_tz):
    ok = [r for r in rows if r["in_window"]]
    out = [f"# Slide ↔ recording alignment — {meta['recording']}", "",
           f"- **Recording start:** {meta['start_local']} ({meta['start_basis']})",
           f"- **Confidence:** {meta['confidence']} · duration {fmt_off(meta['duration'])} · "
           f"{len(ok)}/{len(rows)} photos inside the recording",
           "- **Confirm before use:** open each photo next to its context below and mark it matched or "
           "mismatched. One mismatch means the start is wrong → re-run with `--recording-start`.", "",
           "| Offset | Taken | Photo | Time source | Note |", "|---|---|---|---|---|"]
    for r in rows:
        taken = dt.datetime.fromisoformat(r["taken_utc"]).astimezone(local_tz).strftime("%H:%M:%S")
        note = []
        if not r["in_window"]:
            note.append("⚠️ outside recording — unaligned")
        if r["near_duplicate_of"]:
            note.append(f"near-duplicate of `{r['near_duplicate_of']}`")
        out.append(f"| {r['offset'] if r['in_window'] else '—'} | {taken} | `{r['photo']}` | "
                   f"{r['time_source']} | {'; '.join(note)} |")
    out += ["", f"## Transcript context (±{meta['context_seconds']}s around each photo)"]
    for r in ok:
        if r["near_duplicate_of"]:
            continue
        out += ["", f"### {r['offset']} — `{r['photo']}`", f"_speakers in window: {r['speakers']}_", "",
                r["context"] or "_(no words in window)_"]
    return "\n".join(out) + "\n"


# ---------- self-test (offline, pins the 2026-09-16 hand result) ----------

def selftest():
    ny = ZoneInfo("America/New_York")
    ct = dt.datetime(2026, 9, 16, 23, 39, 23, tzinfo=UTC)   # Android container creation_time
    dur = 4039.0
    exif_local = ["18:40:57", "18:41:47", "18:44:12", "18:46:51", "18:47:47", "18:50:07",
                  "18:53:47", "18:55:56", "18:55:57", "19:00:49", "19:15:49"]
    expected = ["08:53", "09:43", "12:08", "14:47", "15:43", "18:03",
                "21:43", "23:52", "23:53", "28:45", "43:45"]
    times = [dt.datetime.fromisoformat(f"2026-09-16T{t}-04:00").astimezone(UTC) for t in exif_local]
    start, basis, conf, votes = resolve_start(ct, dur, times, "auto", is_android=True)
    assert start == dt.datetime(2026, 9, 16, 22, 32, 4, tzinfo=UTC), start
    assert votes == {"start": 0, "end": 11} and conf == "HIGH", (votes, conf)
    photos = [{"name": f"p{i}.jpg", "time": t, "source": "exif"} for i, t in enumerate(times)]
    photos.append({"name": "before.jpg", "time": start - dt.timedelta(minutes=5), "source": "exif"})
    words = [{"text": "one second to a hundred and seventy-three", "start": 28 * 60 + 40, "speaker_id": "speaker_1"}]
    rows = align(photos, start, dur, words, 45)
    got = [r["offset"] for r in rows if r["in_window"]]
    assert got == expected, got
    assert [r["photo"] for r in rows if not r["in_window"]] == ["before.jpg"]
    assert next(r for r in rows if r["offset"] == "23:53")["near_duplicate_of"] == "p7.jpg"
    assert "seventy-three" in next(r for r in rows if r["offset"] == "28:45")["context"]
    # Pixel filename = UTC; IMG_ filename = local
    assert filename_time("PXL_20260916_224057141.jpg", ny) == times[0].replace(microsecond=141000)
    assert filename_time("IMG_20260916_184057.jpg", ny) == times[0]
    # The two candidate windows [ct-dur, ct] and [ct, ct+dur] only touch at ct, so a wrong guess
    # can't silently fit; a tie means photos split across both (e.g. two sessions) → LOW.
    split = [ct - dt.timedelta(seconds=10), ct + dt.timedelta(seconds=10)]
    s2, _, c2, v2 = resolve_start(ct, dur, split, "auto", is_android=False)
    assert c2 == "LOW" and s2 == ct and v2 == {"start": 1, "end": 1}, (c2, v2)
    # partial fit → MED, not HIGH
    _, _, c3, _ = resolve_start(ct, dur, times + [ct + dt.timedelta(seconds=5)], "auto", is_android=True)
    assert c3 == "MED", c3
    assert resolve_start(ct, dur, times, "start")[0] == ct
    # ffprobe missing → probe_audio degrades to (None, None, False) instead of raising
    import unittest.mock as um
    with um.patch.object(subprocess, "run", side_effect=FileNotFoundError("ffprobe")):
        assert probe_audio("/nonexistent.m4a") == (None, None, False)
    print("selftest OK — 2026-09-16 offsets reproduced; tz, duplicates, out-of-window, tie, ffprobe-missing pass")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", help="ElevenLabs word-level JSON from ingest_recording.py")
    ap.add_argument("--slides-dir", help="folder with slide photos (default: transcript's folder)")
    ap.add_argument("--audio", help="recording file (for duration + creation_time via ffprobe)")
    ap.add_argument("--recording-start", help="ISO time override, e.g. 2026-09-16T18:32:04-04:00 (naive = --tz)")
    ap.add_argument("--creation-time-is", choices=["auto", "start", "end"], default="auto")
    ap.add_argument("--offset-seconds", type=float, default=0.0,
                    help="add to every photo time (camera clock skew vs recorder)")
    ap.add_argument("--context-seconds", type=int, default=45)
    ap.add_argument("--tz", default="America/New_York", help="zone for naive timestamps + display")
    ap.add_argument("--out", help="output dir (default: transcript's folder)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.transcript:
        ap.error("--transcript is required (or use --selftest)")

    local_tz = ZoneInfo(args.tz)
    data = json.load(open(args.transcript))
    words = [w for w in data.get("words", []) if w.get("type", "word") == "word"]
    slides_dir = args.slides_dir or os.path.dirname(args.transcript)
    photos = []
    for name in sorted(os.listdir(slides_dir)):
        path = os.path.join(slides_dir, name)
        if os.path.splitext(name)[1].lower() in PHOTO_EXTS and os.path.isfile(path):
            t, src = photo_time(path, local_tz)
            photos.append({"name": name, "time": t + dt.timedelta(seconds=args.offset_seconds), "source": src})
    if not photos:
        sys.exit(f"[align] no photos found in {slides_dir}")

    dur, ct, is_android = probe_audio(args.audio) if args.audio else (None, None, False)
    if dur is None:
        dur = max((w.get("end") or 0) for w in words) if words else 0.0
    if not dur:
        sys.exit("[align] recording duration unknown (no ffprobe duration, no word timestamps) — "
                 "pass --audio with ffprobe installed, or a transcript JSON with word timestamps")
    times = [p["time"] for p in photos]

    if args.recording_start:
        s = dt.datetime.fromisoformat(args.recording_start)
        start = (s if s.tzinfo else s.replace(tzinfo=local_tz)).astimezone(UTC)
        basis, conf, votes = "--recording-start override", "HIGH", {"override": in_window(times, start, dur)}
    elif ct:
        start, basis, conf, votes = resolve_start(ct, dur, times, args.creation_time_is, is_android)
    elif args.audio and os.path.exists(args.audio):
        mt = dt.datetime.fromtimestamp(os.path.getmtime(args.audio), UTC)
        start = mt - dt.timedelta(seconds=dur)
        basis, conf, votes = "audio mtime − duration (no creation_time tag)", "LOW", {"end": in_window(times, start, dur)}
    else:
        sys.exit("[align] can't find a recording start: pass --audio (with a creation_time tag) or --recording-start")

    rows = align(photos, start, dur, words, args.context_seconds)
    meta = {"recording": os.path.basename(args.audio or args.transcript), "start_utc": start.isoformat(),
            "start_local": start.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "start_basis": basis, "confidence": conf, "votes": votes, "duration": dur,
            "context_seconds": args.context_seconds, "offset_seconds_applied": args.offset_seconds}
    outdir = args.out or os.path.dirname(args.transcript)
    md_path = os.path.join(outdir, "slide-recording-alignment.md")
    open(md_path, "w").write(render_md(meta, rows, local_tz))
    json.dump({"meta": meta, "photos": rows}, open(os.path.join(outdir, "slide-recording-alignment.json"), "w"), indent=2)
    n_in = sum(r["in_window"] for r in rows)
    print(f"[align] start {meta['start_local']} · {conf} · {n_in}/{len(rows)} photos in window\n  -> {md_path}")
    if conf in ("LOW", "UNKNOWN") or n_in < len(rows):
        print("[align] ⚠️ verify: confirm pass required (low confidence or unaligned photos)")


if __name__ == "__main__":
    main()
