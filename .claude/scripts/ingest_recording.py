#!/usr/bin/env python3
"""ingest_recording.py — locked recipe for recording -> clean transcript (Linear YED-95).

Proven on Agents Behaving Badly (06-25): ElevenLabs scribe_v2 + keyterms beat the recorder-app
baseline 100% vs 50% on spoken proper nouns (+50pts), no regressions.

Recipe (the locked decisions):
  - model: scribe_v2 (required for keyterms)
  - keyterms: seed BOTH full names AND first names (the 'Arielle Mella' vs 'Arielle' lesson)
  - diarize=True; optional --num-speakers to curb over-segmentation
  - timestamps_granularity=word -> per-word timestamp + logprob (the quote-safety contract)

Outputs (next to the audio, or --out):
  1. '<stem> — Transcript (ElevenLabs).md'  -> diarized, [speaker] (mm:ss) blocks
  2. '<stem> — Transcript (ElevenLabs).json' -> full word-level data (timestamps + logprob)
  3. '<stem> — REVIEW (low-confidence spots).md' -> words below --confidence-threshold with
     timestamps, so the content step can verify before quoting verbatim (R1 quote-safety guard).

Usage:
  source <repo>/.env   # ELEVENLABS_API_KEY
  uv run --with elevenlabs python ingest_recording.py \
      --audio "/path/to/recording.m4a" \
      --keyterms "Arklex,Arielle,Datadog,..."   # or --keyterms-file path (one per line)
      [--num-speakers 5] [--confidence-threshold -1.0]
"""
import argparse, json, math, os, sys

def fmt_ts(s):
    if s is None: return "??:??"
    s = int(s); return f"{s//60:02d}:{s%60:02d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", default=None, help="output dir (default: audio's folder)")
    ap.add_argument("--keyterms", default="", help="comma-separated; seed full names AND first names")
    ap.add_argument("--keyterms-file", default=None, help="newline-separated keyterms file")
    ap.add_argument("--num-speakers", type=int, default=None)
    ap.add_argument("--confidence-threshold", type=float, default=-1.0,
                    help="flag words with logprob below this for review (default -1.0 ~= p<0.37)")
    args = ap.parse_args()

    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key.startswith("sk_"):
        sys.exit("ELEVENLABS_API_KEY missing/invalid (source the repo .env)")

    keyterms = [k.strip() for k in args.keyterms.split(",") if k.strip()]
    if args.keyterms_file and os.path.exists(args.keyterms_file):
        keyterms += [l.strip() for l in open(args.keyterms_file) if l.strip()]
    keyterms = list(dict.fromkeys(keyterms))  # dedupe, keep order

    outdir = args.out or os.path.dirname(args.audio)
    stem = os.path.splitext(os.path.basename(args.audio))[0]

    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=key)

    kw = dict(model_id="scribe_v2", diarize=True, tag_audio_events=False,
              timestamps_granularity="word")
    if keyterms: kw["keyterms"] = keyterms
    if args.num_speakers: kw["num_speakers"] = args.num_speakers

    print(f"[ingest] scribe_v2 · {len(keyterms)} keyterms · {os.path.basename(args.audio)} ...", flush=True)
    with open(args.audio, "rb") as f:
        res = client.speech_to_text.convert(file=f, **kw)
    data = res.model_dump() if hasattr(res, "model_dump") else (res.dict() if hasattr(res, "dict") else {"text": getattr(res, "text", "")})

    words = data.get("words") or []
    text = data.get("text") or ""

    # 1. full json
    json_path = os.path.join(outdir, f"{stem} — Transcript (ElevenLabs).json")
    json.dump(data, open(json_path, "w"), indent=2, default=str)

    # 2. diarized md with speaker + timestamp blocks
    lines, cur, buf, blk_start = [], None, [], None
    for w in words:
        spk = w.get("speaker_id") or w.get("speaker") or "?"
        if w.get("type") == "spacing":
            buf.append(w.get("text", "")); continue
        if spk != cur:
            if buf: lines.append(f"**[{cur}]** ({fmt_ts(blk_start)})  {''.join(buf).strip()}")
            cur, buf, blk_start = spk, [], w.get("start")
        buf.append(w.get("text", ""))
    if buf: lines.append(f"**[{cur}]** ({fmt_ts(blk_start)})  {''.join(buf).strip()}")
    md_path = os.path.join(outdir, f"{stem} — Transcript (ElevenLabs).md")
    open(md_path, "w").write(f"# {stem} — ElevenLabs transcript (scribe_v2 + keyterms)\n\n" +
                             ("\n\n".join(lines) if lines else text) + "\n")

    # 3. low-confidence review list (quote-safety contract)
    flags = [w for w in words if isinstance(w.get("logprob"), (int, float))
             and w.get("logprob") < args.confidence_threshold and w.get("type") != "spacing"
             and (w.get("text") or "").strip()]
    flags.sort(key=lambda w: w.get("logprob", 0))
    rv = [f"# Low-confidence spots — VERIFY before quoting verbatim",
          f"_Words with logprob < {args.confidence_threshold} (lower = less certain). Use the timestamp to click-to-hear._\n",
          f"Total flagged: {len(flags)} of {len([w for w in words if w.get('type')!='spacing'])} words\n"]
    for w in flags[:200]:
        p = math.exp(w["logprob"]) if w["logprob"] > -50 else 0.0
        rv.append(f"- ({fmt_ts(w.get('start'))}) **{w.get('text','').strip()}** — conf≈{p:.0%} (logprob {w['logprob']:.2f})")
    open(os.path.join(outdir, f"{stem} — REVIEW (low-confidence spots).md"), "w").write("\n".join(rv) + "\n")

    print(f"[ingest] DONE  words={len([w for w in words if w.get('type')!='spacing'])}  "
          f"flagged_low_conf={len(flags)}\n  -> {md_path}\n  -> {json_path}\n  -> review list", flush=True)

if __name__ == "__main__":
    main()
