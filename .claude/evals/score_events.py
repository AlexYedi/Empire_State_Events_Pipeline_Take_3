#!/usr/bin/env python3
"""n=4 entity-accuracy scorecard — baseline (recorder app) vs ElevenLabs (scribe_v2 + keyterms).
Spoken proper nouns only (from each event's verified brief). HIT = any accepted variant appears
(word-boundary, case-insensitive). Lift = EL_acc - baseline_acc."""
import os, re
EC = "/Users/sameoldexpressions/Documents/GitHub/Empire_State_Events_Pipeline_Take_3/Event Content"

EVENTS = {
  "AI Demo Night (05-21)": {
    "baseline": f"{EC}/05 21 26 AI Demo Night/05 21 26 AI Demo Night Transcript.txt",
    "el":       f"{EC}/05 21 26 AI Demo Night/05 21 26 AI Demo Night Recording — Transcript (ElevenLabs).md",
    "ents": {"Docker":["Docker"],"Red Hat":["Red Hat","RedHat"],"OpenShift":["OpenShift","Open Shift"],
             "cBioPortal":["cBioPortal","bioportal"],"Qwen":["Qwen"],"ClickHouse":["ClickHouse","Click House"],
             "RoleMate":["RoleMate","Role Mate"]},
  },
  "2x AI by Fin (06-04)": {
    "baseline": f"{EC}/06 04 26_ 2x AI_ We gave everyone the tools, and it worked/06 04 26 2x AI by Fin Transcript.txt",
    "el":       f"{EC}/06 04 26_ 2x AI_ We gave everyone the tools, and it worked/06 04 26 2x AI by Fin Recording — Transcript (ElevenLabs).md",
    "ents": {"Fin":["Fin"],"Intercom":["Intercom"],"Anthropic":["Anthropic"],"Claude":["Claude"],
             "Donohue":["Donohue"],"Prithvi":["Prithvi"],"Curran":["Curran","Darragh"]},
  },
  "GTM+AI Masterclass #5 (06-03)": {
    "baseline": f"{EC}/06 03 26_ NYC GTM+AI Masterclass #5 - NY Tech Week Special/06 03 26 NYC GTM+AI Masterclass #5 Transcript.txt",
    "el":       f"{EC}/06 03 26_ NYC GTM+AI Masterclass #5 - NY Tech Week Special/06 03 26 NYC GTM+AI Masterclass #5 Recording — Transcript (ElevenLabs).md",
    "ents": {"Sangram":["Sangram","Vajre"],"GTM Partners":["GTM Partners"],"Nowoslawski":["Nowoslawski"],
             "Growth Engine":["Growth Engine"],"Nikita":["Nikita","Bokil"],"Optimizely":["Optimizely"],
             "Opal":["Opal"],"Nimo":["Nimo"],"Swan":["Swan"],"CoverForce":["CoverForce","Cover Force"],
             "Kenny/Tsai":["Tsai","Kenny","Kenneth"],"Clay":["Clay"],"Insight Partners":["Insight Partners"]},
  },
}

def load(p): return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else None
def hit(text, variants): return any(re.search(r"\b"+re.escape(v)+r"\b", text, re.I) for v in variants)

print("n=4 entity-accuracy scorecard — baseline (recorder app) vs ElevenLabs (scribe_v2 + keyterms)\n")
rows = []
for ev, c in EVENTS.items():
    b, e = load(c["baseline"]), load(c["el"])
    if b is None or e is None:
        print(f"{ev}: MISSING ({'baseline' if b is None else ''} {'el' if e is None else ''})"); continue
    tot = len(c["ents"])
    bh = sum(hit(b, v) for v in c["ents"].values())
    eh = sum(hit(e, v) for v in c["ents"].values())
    missB = [k for k,v in c["ents"].items() if not hit(b,v)]
    missE = [k for k,v in c["ents"].items() if not hit(e,v)]
    rows.append((ev, bh, eh, tot))
    print(f"=== {ev} ===")
    print(f"  baseline: {bh}/{tot} = {bh/tot:.0%}   miss: {', '.join(missB) or '—'}")
    print(f"  EL:       {eh}/{tot} = {eh/tot:.0%}   miss: {', '.join(missE) or '—'}")
    print(f"  LIFT: {(eh-bh)/tot*100:+.0f} pts\n")

print("--- n=4 summary (incl. Agents Behaving Badly from prior run) ---")
print(f"  {'Agents Behaving Badly (06-25)':32} baseline 50%  ->  EL+kt 100%  (+50)")
for ev, bh, eh, tot in rows:
    print(f"  {ev:32} baseline {bh/tot:.0%}  ->  EL {eh/tot:.0%}  ({(eh-bh)/tot*100:+.0f})")
