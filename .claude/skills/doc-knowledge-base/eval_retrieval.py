#!/usr/bin/env python3
"""YED-118 retrieval acceptance gate. recall@k over eval_set.json.

hit = any of the top-k retrieved chunks contains the gold phrase
(whitespace-normalized, case-insensitive). Prints per-case pass/fail + recall@k.
Exit 0 if recall >= --bar (default 0.80), else exit 1.
"""
import argparse, json, os, re, sys
import ask_library as al

HERE = os.path.dirname(os.path.abspath(__file__))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--bar", type=float, default=0.80)
    ap.add_argument("--set", default=os.path.join(HERE, "eval_set.json"))
    args = ap.parse_args()

    spec = json.load(open(args.set))
    cases = spec["cases"]
    hits = 0
    print(f"Retrieval eval: {spec['doc']}  (k={args.k}, bar={args.bar:.0%})\n" + "=" * 66)
    for c in cases:
        rows = al.retrieve(c["q"], args.k)
        g = norm(c["gold"])
        hit_rank = next((i + 1 for i, r in enumerate(rows) if g in norm(r["content"])), None)
        hits += hit_rank is not None
        mark = f"PASS @{hit_rank}" if hit_rank else "MISS   "
        print(f"[{mark}] {c['q']}")
        if not hit_rank:
            print(f"          gold not in top-{args.k}: \"{c['gold']}\"")
    recall = hits / len(cases)
    print("=" * 66)
    print(f"recall@{args.k} = {hits}/{len(cases)} = {recall:.0%}   "
          f"{'>= bar -> PASS' if recall >= args.bar else '< bar -> FAIL'}")
    sys.exit(0 if recall >= args.bar else 1)


if __name__ == "__main__":
    main()
