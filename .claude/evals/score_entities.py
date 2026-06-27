#!/usr/bin/env python3
"""Entity-accuracy scorer for the transcription quality scorecard (YED-95).

Rule: an entity is a HIT if its canonical string appears correctly (case-insensitive)
at least once in the transcript — i.e., the name is recoverable. Score = hits / total.
The phone transcript is the baseline; ElevenLabs is scored the same way; the delta is the lift.
Limitation: 'appears once correctly' can over-credit inconsistent transcripts — note it.
"""
import os, sys

BASE = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/Event Content"

EVENTS = {
    "NYC AI Demos #10 (06-24)": {
        "entities": ["Spring Health", "Spara", "Pace", "Uncovr", "Pensar",
                      "Thrive", "First Round", "Index Ventures", "Inspired Capital", "Able Partners",
                      "Kyle Bhiro", "John de Lorenzo", "Dave Walker", "Tristan", "Karem"],
        "transcripts": {
            "phone": f"{BASE}/06 24 26_ NYC AI Demos #10/06 24 26 AI Demo #10 Transcript.txt",
            "elevenlabs": None,  # no audio
        },
    },
    "Agents Behaving Badly (06-25)": {
        "entities": ["Arklex", "Datadog", "Meta Superintelligence", "Columbia University", "AccelGentic",
                      "Kilian Lieret", "Zhou Yu", "John Mark", "Yi Ju", "Arielle Mella"],
        "transcripts": {
            "phone": f"{BASE}/06 25 26_ Agents Behaving Badly/06.25.26.Agents.Behaving.Badly.Transcript.md",
            "elevenlabs": f"{BASE}/06 25 26_ Agents Behaving Badly/ElevenLabs Scribe Transcript.md",
        },
    },
}

import re

def load(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()

def count(text, ent):
    # word-boundary, case-insensitive: kills 'Pace'-in-'space' false positives
    return len(re.findall(r"\b" + re.escape(ent) + r"\b", text, flags=re.I))

for event, cfg in EVENTS.items():
    print(f"\n=== {event} ===")
    ents = cfg["entities"]
    for label, path in cfg["transcripts"].items():
        text = load(path)
        if text is None:
            print(f"  [{label}] (no transcript)")
            continue
        counts = {e: count(text, e) for e in ents}
        hits = [e for e in ents if counts[e] > 0]
        miss = [e for e in ents if counts[e] == 0]
        print(f"  [{label}] entity acc = {len(hits)}/{len(ents)} = {len(hits)/len(ents):.0%}  (word-boundary, >=1 correct)")
        print("      counts: " + ", ".join(f"{e}={counts[e]}" for e in ents))
        if miss:
            print(f"      miss(0 correct): {', '.join(miss)}")
