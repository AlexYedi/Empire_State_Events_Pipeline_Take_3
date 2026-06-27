#!/usr/bin/env python3
"""Entity-accuracy scorer — corrected method (YED-95; regraded 2026-06-27).

Why corrected (per the scorecard's first-run findings):
  1. The file labeled '…Transcript.md' is the pre-event RESEARCH BRIEF, not a transcript —
     so there is NO real phone baseline. Lift is therefore measured EL-plain -> EL+keyterms.
  2. Score only SPOKEN proper nouns. Roster names speakers never say aloud (their own name /
     company, host affiliations) must not penalize a transcript. 'Spoken' is inferred from
     presence in >=1 EL transcript (LIMIT: no audio access — not verified against the .m4a).
  3. Variant-aware: a HIT = any accepted variant appears (word-boundary, case-insensitive).
     Mangles (e.g. Arklex -> 'Arc'/'Archlex') are reported but do NOT count as hits.
"""
import os, re

BASE = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/Event Content/06 25 26_ Agents Behaving Badly"

TRANSCRIPTS = {
    "EL plain (scribe_v1)":     f"{BASE}/ElevenLabs Scribe Transcript.md",
    "EL +keyterms (scribe_v2)": f"{BASE}/ElevenLabs Scribe Transcript (keyterms).md",
}

# Spoken proper nouns (appear in >=1 EL transcript). Full-roster names never verbalized are excluded.
SPOKEN = {
    "Arklex":        ["Arklex"],                    # correct only; mangles below are NOT hits
    "Datadog":       ["Datadog"],
    "Columbia":      ["Columbia"],                  # short form is what's spoken
    "Kilian":        ["Kilian"],                    # first name spoken; surname 'Lieret' not
    "AccelGentic":   ["AccelGentic", "Accel Gentic"],
    "Arielle Mella": ["Arielle", "Mella"],
}
MANGLES = {"Arklex": ["Archlex", "Arc"]}
EXCLUDED_UNSPOKEN = ["Meta Superintelligence", "Zhou Yu", "John Mark", "Yi Ju", "Lieret"]  # research-brief-only

def load(p):
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else None

def n(text, s):
    return len(re.findall(r"\b" + re.escape(s) + r"\b", text, flags=re.I))

print("Entity accuracy — SPOKEN proper nouns only, variant-aware (YED-95 regrade)")
for label, path in TRANSCRIPTS.items():
    t = load(path)
    if t is None:
        print(f"\n=== {label} ===\n  (missing: {path})")
        continue
    print(f"\n=== {label} ===")
    hits = 0
    for ent, variants in SPOKEN.items():
        c = sum(n(t, v) for v in variants)
        ok = c > 0
        hits += ok
        extra = ""
        if ent in MANGLES:
            mc = sum(n(t, m) for m in MANGLES[ent])
            if mc:
                extra = f"   (mangled x{mc}: {'/'.join(MANGLES[ent])})"
        print(f"  {'HIT ' if ok else 'MISS'} {ent:<14} count={c}{extra}")
    print(f"  -> spoken-entity accuracy = {hits}/{len(SPOKEN)} = {hits/len(SPOKEN):.0%}")

print(f"\nExcluded (never spoken; research-brief-only): {', '.join(EXCLUDED_UNSPOKEN)}")
print("Limit: 'spoken' inferred from transcript presence, not the .m4a audio.")
