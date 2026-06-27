#!/usr/bin/env python3
"""Entity-accuracy scorer — YED-95. Fully redone 2026-06-27 with the REAL recorder-app baseline.

History: the file once labeled '…Transcript.md' was the pre-event research brief (deleted). The
actual recorder-app transcript is now in the folder, so we measure TRUE lift:
   recorder-app baseline  ->  EL plain (scribe_v1)  ->  EL +keyterms (scribe_v2).

Method: HIT = an accepted variant appears (word-boundary, case-insensitive). Score only SPOKEN
proper nouns (appear in >=1 transcript of the same audio). Mangles are reported, NOT counted as hits
(cleaner != correct). LIMIT: 'spoken' inferred from the 3 transcripts, not hand-checked vs the .m4a.
"""
import os, re

BASE = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/Event Content/06 25 26_ Agents Behaving Badly"
EVAL = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/.claude/evals/agents-behaving-badly"

TRANSCRIPTS = {
    "Baseline (recorder app)":   f"{BASE}/06 25 26_Transcript_Agents Behaving Badly.md",
    "EL plain (scribe_v1)":      f"{EVAL}/el_scribe_v1_plain.md",
    "EL +keyterms (scribe_v2)":  f"{EVAL}/el_scribe_v2_keyterms.md",
}

# Spoken proper nouns (appear in >=1 transcript of the same audio). Roster names never verbalized excluded.
SPOKEN = {
    "Arklex":        ["Arklex"],
    "Datadog":       ["Datadog"],
    "Columbia":      ["Columbia"],
    "Kilian":        ["Kilian"],
    "AccelGentic":   ["AccelGentic", "Accel Gentic"],
    "Arielle Mella": ["Arielle", "Mella"],
}
MANGLES = {"Arklex": ["Archlex", "Arc"], "Arielle Mella": ["Ariel"]}  # reported; NOT hits
EXCLUDED_UNSPOKEN = ["Meta Superintelligence", "Zhou Yu", "John Mark", "Yi Ju", "Lieret"]

def load(p):
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else None
def n(text, s):
    return len(re.findall(r"\b" + re.escape(s) + r"\b", text, flags=re.I))

print("Entity accuracy — SPOKEN proper nouns, variant-aware (YED-95, real-baseline redo)")
scores = {}
for label, path in TRANSCRIPTS.items():
    t = load(path)
    if t is None:
        print(f"\n=== {label} ===  (missing: {path})"); continue
    print(f"\n=== {label} ===")
    hits = 0
    for ent, variants in SPOKEN.items():
        c = sum(n(t, v) for v in variants)
        ok = c > 0; hits += ok
        extra = ""
        if ent in MANGLES:
            mc = sum(n(t, m) for m in MANGLES[ent])
            if mc: extra = f"   (mangled x{mc}: {'/'.join(MANGLES[ent])})"
        print(f"  {'HIT ' if ok else 'MISS'} {ent:<14} count={c}{extra}")
    acc = hits / len(SPOKEN)
    scores[label] = acc
    print(f"  -> spoken-entity accuracy = {hits}/{len(SPOKEN)} = {acc:.0%}")

if "Baseline (recorder app)" in scores:
    base = scores["Baseline (recorder app)"]
    print("\n--- LIFT vs recorder-app baseline ---")
    for label, acc in scores.items():
        if label != "Baseline (recorder app)":
            print(f"  {label}: {acc:.0%}  ({(acc-base)*100:+.0f} pts)")
print(f"\nExcluded (never spoken): {', '.join(EXCLUDED_UNSPOKEN)}")
print("Limit: 'spoken' inferred from the 3 transcripts, not hand-checked vs the .m4a.")
