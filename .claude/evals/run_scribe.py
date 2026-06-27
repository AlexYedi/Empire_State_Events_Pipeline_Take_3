#!/usr/bin/env python3
"""Re-run ElevenLabs Scribe v2 with the keyterms seed (YED-95). Committed so the run is reproducible
(the prior runs had no committed runner — that gap is now closed).

Usage:
    ELEVENLABS_API_KEY=sk_... python3 .claude/evals/run_scribe.py

Reads:  .claude/evals/agents-behaving-badly/keyterms.json  (the seed)
Audio:  Event Content/06 25 26_ Agents Behaving Badly/06.25.26.Agents.Behaving.Badly.Recording.m4a (~64 min)
Writes: .claude/evals/agents-behaving-badly/el_scribe_v2_keyterms.(json|md)
Then re-score:  python3 .claude/evals/score_entities.py

NOTE: this is a PAID transcription (~64 min audio). Verify the installed SDK's convert() signature
(`pip show elevenlabs`) — param names below (keyterms, num_speakers, timestamps_granularity) are the
SDK capabilities confirmed in transcription-quality-scorecard.md, but pin them to your SDK version.
"""
import os, sys, json

ROOT = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3"
SEED = f"{ROOT}/.claude/evals/agents-behaving-badly/keyterms.json"
AUDIO = f"{ROOT}/Event Content/06 25 26_ Agents Behaving Badly/06.25.26.Agents.Behaving.Badly.Recording.m4a"
OUTDIR = f"{ROOT}/.claude/evals/agents-behaving-badly"

def main():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY not set (it lives in the Take-3 .env).")
    cfg = json.load(open(SEED))
    keyterms = cfg["keyterms"]
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        sys.exit("elevenlabs SDK not installed: pip install elevenlabs")
    client = ElevenLabs(api_key=key)
    print(f"transcribing {AUDIO}\n  model=scribe_v2  keyterms={keyterms}")
    with open(AUDIO, "rb") as f:
        r = client.speech_to_text.convert(
            file=f,
            model_id="scribe_v2",
            keyterms=keyterms,
            num_speakers=4,            # scorecard: cap diarization over-segmentation
            timestamps_granularity="word",
        )
    data = r.model_dump() if hasattr(r, "model_dump") else dict(r)
    json.dump(data, open(f"{OUTDIR}/el_scribe_v2_keyterms.json", "w"), indent=0)
    open(f"{OUTDIR}/el_scribe_v2_keyterms.md", "w").write(data.get("text", ""))
    print(f"done: {len(data.get('text',''))} chars, {len(data.get('words',[]))} words")
    print("now re-score: python3 .claude/evals/score_entities.py")

if __name__ == "__main__":
    main()
