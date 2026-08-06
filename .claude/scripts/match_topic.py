#!/usr/bin/env python3
"""
Fuzzy topic-matcher for the Market-Intelligence graph (YED-115 — match-before-create helper).

Given a candidate topic name, returns the closest EXISTING graph topics by string/token similarity —
so the match-before-create step (in /scan-trends, /morning-refresh) surfaces "did you mean this existing
topic?" candidates instead of blindly minting a duplicate. Reduces the fragmentation the 2026-08-06 run
exposed (9 of 10 topics created new because names didn't exactly match the 153-topic taxonomy).

**Subscription-only — pure string math, no embeddings, no API, no tokens.** It ASSISTS the Claude-in-loop
match (Claude still makes the final call on semantic equivalence); it is NOT the automated embedding merge
(that's only needed for unattended runs — deferred on YED-115). Token-overlap catches most near-duplicates
("LLM Evaluation" ~ "Agent Evaluation & Reliability"); Claude handles the no-token-overlap semantic cases
("Open-Weight LLMs" ~ "Open-source AI Infrastructure").

Usage:
    python3 .claude/scripts/match_topic.py "AI Agent Security"        # top matches for one name
    python3 .claude/scripts/match_topic.py "LLM Evaluation" --top 8
    python3 .claude/scripts/match_topic.py --threshold 0.4 "Agentic AI"   # only show ties >= threshold

Reads SUPABASE_API_KEY from .env (never printed). Read-only — never writes.
"""
import json, os, re, sys, urllib.request, urllib.error

BASE = "https://oicikjyzmxqfomrrqkvf.supabase.co/rest/v1"
STOP = {"the", "a", "an", "of", "for", "in", "and", "to", "with", "on", "&", "ai", "-"}

def load_key():
    for line in open(os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
        if line.startswith("SUPABASE_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip()
    sys.exit("SUPABASE_API_KEY not found in .env")

def tokens(name):
    # lowercase, strip parentheticals, split on non-alphanumerics, drop stopwords
    name = re.sub(r"\(.*?\)", " ", name.lower())
    toks = [t for t in re.split(r"[^a-z0-9]+", name) if t and t not in STOP]
    return set(toks)

def score(a_tokens, a_raw, b_name):
    b_tokens = tokens(b_name)
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    jaccard = inter / union if union else 0.0
    # substring bonus: one core name contained in the other
    a_core, b_core = a_raw.lower().strip(), b_name.lower().strip()
    sub = 0.25 if (a_core in b_core or b_core in a_core) else 0.0
    # containment: all of the smaller token set inside the larger
    contain = 0.15 if a_tokens and (a_tokens <= b_tokens or b_tokens <= a_tokens) else 0.0
    return round(min(1.0, jaccard + sub + contain), 3)

def main():
    args = [a for a in sys.argv[1:]]
    top_n, threshold = 5, 0.0
    if "--top" in args:
        i = args.index("--top"); top_n = int(args[i + 1]); del args[i:i + 2]
    if "--threshold" in args:
        i = args.index("--threshold"); threshold = float(args[i + 1]); del args[i:i + 2]
    if not args:
        sys.exit('usage: match_topic.py "Candidate Topic Name" [--top N] [--threshold X]')
    query = args[0]

    key = load_key()
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        rows = json.load(urllib.request.urlopen(
            urllib.request.Request(BASE + "/topic?select=name&limit=2000", headers=h)))
    except urllib.error.HTTPError as e:
        sys.exit(f"graph read failed: {e.code} {e.read().decode()[:120]}")

    q_tokens = tokens(query)
    scored = sorted(((score(q_tokens, query, r["name"]), r["name"]) for r in rows),
                    key=lambda x: x[0], reverse=True)
    hits = [(s, n) for s, n in scored if s >= threshold][:top_n]

    print(f'Closest existing topics to: "{query}"')
    if not hits or hits[0][0] == 0.0:
        print("  (no similar existing topic — likely genuinely NET-NEW)")
        return
    for s, n in hits:
        flag = "  ← strong match, likely same topic" if s >= 0.5 else ""
        print(f"  {s:>5.3f}  {n}{flag}")
    if hits[0][0] < 0.5:
        print("  (best match is weak — Claude should judge if it's the same topic or net-new)")

if __name__ == "__main__":
    main()
