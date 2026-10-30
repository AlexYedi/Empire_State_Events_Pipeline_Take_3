#!/usr/bin/env python3
"""Deterministic pre-pass for the output-evaluator (YED-259): the checks a model shouldn't be trusted with.

  quotes   Every double-quoted span of 2+ words in a draft, matched against the transcript(s).
           Reports the best-matching transcript window, its score (0-1) and the speaker tag nearest it.
  sources  Every sentence carrying a figure (number, %, $, multiplier) or a funding/valuation verb,
           and whether the draft cites a URL anywhere. The evaluator judges each one; this only lists.
  x        An X (Twitter) thread draft (posts separated by lines of ---). Checks per-post length
           (280), hook length (post 1 < 200), link placement (at most 1 link, in the last post)
           and hashtag count (at most 1 per post) — rules in .claude/references/x-content.md.

The output is JSON for the evaluator agent to read. It never edits the draft.

Usage:
  output_checks.py quotes  --draft DRAFT.md --transcript T1.md [--transcript T2.md ...] [--min 0.85]
  output_checks.py sources --draft DRAFT.md
  output_checks.py x       --draft THREAD.md
"""
import argparse
import difflib
import json
import re
import sys

QMARK = re.compile(r'["“”]')


def quoted_spans(text):
    """Pair double quotes in order within each line, so a short quote ("world model") can't
    swallow the text up to the next real quote. Yields (start, quote_text)."""
    offset = 0
    for line in text.split("\n"):
        marks = [m.start() for m in QMARK.finditer(line)]
        for a, b in zip(marks[0::2], marks[1::2]):
            yield offset + a, line[a + 1:b]
        offset += len(line) + 1
SPEAKER = re.compile(r"\[(speaker_\d+)\]")
FIGURE = re.compile(r"(\$\s?\d|\d[\d,.]*\s?(%|percent|x\b|k\b|m\b|bn\b|million|billion|thousand|tokens)|\b\d{2,}[\d,]*\b)", re.I)
MONEY_VERB = re.compile(r"\b(raised|valuation|valued|series [a-e]|acquired|acquisition|revenue|arr|funding|ipo)\b", re.I)
URL = re.compile(r"https?://\S+")
FILLER = {"uh", "um", "uh,", "um,", "like,", "mm"}


def words(text):
    return [w for w in re.sub(r"[^\w\s']", " ", text.lower()).split() if w not in FILLER]


def best_window(q_words, t_words):
    n = len(q_words)
    if n == 0 or len(t_words) < n:
        return 0.0, 0
    best, at = 0.0, 0
    sm = difflib.SequenceMatcher(autojunk=False)
    sm.set_seq2(q_words)
    # coarse pass on stride, then refine around the best hit
    stride = max(1, n // 4)
    for i in range(0, len(t_words) - n + 1, stride):
        sm.set_seq1(t_words[i:i + n])
        r = sm.ratio()
        if r > best:
            best, at = r, i
    for i in range(max(0, at - stride), min(len(t_words) - n, at + stride) + 1):
        for size in (n - 1, n, n + 1, n + 2):
            if size <= 0 or i + size > len(t_words):
                continue
            sm.set_seq1(t_words[i:i + size])
            r = sm.ratio()
            if r > best:
                best, at = r, i
    return round(best, 3), at


def cmd_quotes(args):
    draft = open(args.draft, errors="ignore").read()
    corpora = []
    for path in args.transcript:
        raw = open(path, errors="ignore").read()
        # keep a per-word speaker tag so a match can name its speaker
        # keep a per-word speaker tag and section heading, so a match can name who said it
        # (speaker ids restart per recording, so the section disambiguates them)
        toks, spk, cur, section = [], [], None, None
        for piece in re.split(r"(\[speaker_\d+\]|^## .*$)", raw, flags=re.M):
            stripped = piece.strip()
            if stripped.startswith("## "):
                section, cur = stripped[3:120], None
                continue
            m = SPEAKER.fullmatch(stripped) if stripped else None
            if m:
                cur = m.group(1)
                continue
            for w in words(piece):
                toks.append(w)
                spk.append((cur, section))
        corpora.append((path, toks, spk))
    results = []
    for start, q in quoted_spans(draft):
        q = q.strip()
        qw = words(q)
        if len(qw) < 2:  # 2-word phrases matter: "autonomous production" was a real misquote
            continue
        line_start = draft.rfind("\n", 0, start) + 1
        context = draft[line_start:start][-120:]
        best = {"score": 0.0}
        for path, toks, spk in corpora:
            score, at = best_window(qw, toks)
            if score > best["score"]:
                best = {"score": score, "transcript": path,
                        "speaker": spk[at][0] if spk else None, "section": spk[at][1] if spk else None,
                        "matched_text": " ".join(toks[at:at + len(qw) + 2])}
        results.append({"quote": q, "lead_in": context.strip(), **best,
                        "verdict": "match" if best["score"] >= args.min else "no-match"})
    out = {"check": "quotes", "draft": args.draft, "threshold": args.min, "quotes": results,
           "summary": {"total": len(results), "no_match": sum(r["verdict"] == "no-match" for r in results)}}
    print(json.dumps(out, indent=1))


def cmd_sources(args):
    draft = open(args.draft, errors="ignore").read()
    sentences = re.split(r"(?<=[.!?])\s+|\n+", draft)
    claims = []
    for s in sentences:
        s = s.strip()
        if len(s) < 12 or s.startswith(("#", "http", "- **", "**Source")):
            continue
        if FIGURE.search(s) or MONEY_VERB.search(s):
            claims.append({"sentence": s[:300], "has_url_inline": bool(URL.search(s))})
    out = {"check": "sources", "draft": args.draft, "urls_in_draft": len(set(URL.findall(draft))),
           "claims": claims, "summary": {"claim_candidates": len(claims)}}
    print(json.dumps(out, indent=1))


# ---------------------------------------------------------------------------
# x — X (Twitter) thread checks (E-05). Rules: .claude/references/x-content.md
# ---------------------------------------------------------------------------
X_POST_LIMIT = 280   # rule 1, X platform rule
X_HOOK_LIMIT = 200   # rule 3, house style: the hook must land UNDER 200
HASHTAG = re.compile(r"(?<!\w)#[A-Za-z0-9_]+")


def split_thread(text):
    """A thread draft is one or more posts separated by lines of ---."""
    return [p.strip() for p in re.split(r"^---+\s*$", text, flags=re.M) if p.strip()]


def check_x_thread(text):
    """Pure check: per-post length, hook length, link placement, hashtag count (x-content.md
    rules 1, 3, 5, 6). Lists findings as JSON; never edits the draft."""
    posts = split_thread(text)
    findings = []
    if not posts:
        return {"check": "x", "posts": [], "findings": [{"check": "empty_draft"}],
                "summary": {"posts": 0, "findings": 1}}
    report = []
    for i, post in enumerate(posts):
        n = len(post)
        tags = HASHTAG.findall(post)
        report.append({"post": i + 1, "chars": n, "hashtags": len(tags),
                       "links": len(URL.findall(post))})
        if n > X_POST_LIMIT:
            findings.append({"post": i + 1, "check": "post_length",
                             "detail": f"{n} chars > {X_POST_LIMIT} (x-content.md rule 1)"})
        if i == 0 and n >= X_HOOK_LIMIT:
            findings.append({"post": 1, "check": "hook_length",
                             "detail": f"{n} chars, must be under {X_HOOK_LIMIT} (rule 3)"})
        if len(tags) > 1:
            findings.append({"post": i + 1, "check": "hashtag_count",
                             "detail": f"{len(tags)} hashtags, at most 1 (rule 6)"})
    links = [(i + 1, m.group()) for i, p in enumerate(posts) for m in URL.finditer(p)]
    if len(links) > 1:
        findings.append({"post": None, "check": "link_count",
                         "detail": f"{len(links)} links in thread, at most 1 (rule 5)"})
    if links and links[0][0] != len(posts):
        findings.append({"post": links[0][0], "check": "link_placement",
                         "detail": "link not in the last post (rule 5)"})
    return {"check": "x", "posts": report, "findings": findings,
            "summary": {"posts": len(posts), "findings": len(findings)}}


def cmd_x(args):
    draft = open(args.draft, errors="ignore").read()
    print(json.dumps(check_x_thread(draft) | {"draft": args.draft}, indent=1))


def main():
    if "--selftest" in sys.argv:
        return selftest()
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quotes")
    q.add_argument("--draft", required=True)
    q.add_argument("--transcript", action="append", required=True)
    q.add_argument("--min", type=float, default=0.85)
    s = sub.add_parser("sources")
    s.add_argument("--draft", required=True)
    x = sub.add_parser("x")
    x.add_argument("--draft", required=True)
    a = p.parse_args()
    {"quotes": cmd_quotes, "sources": cmd_sources, "x": cmd_x}[a.cmd](a)


# ---------------------------------------------------------------------------
# selftest — one passing and one failing input per check (E-07)
# ---------------------------------------------------------------------------
def selftest():
    """--selftest: run the quotes and sources checks on inline fixtures — one passing and
    one failing input per check. Temp files only; no network; no model; nothing edited."""
    import contextlib
    import io
    import json
    import os
    import shutil
    import tempfile

    checks = []

    def ck(name, cond):
        checks.append((name, bool(cond)))

    def run(argv):
        old_argv = sys.argv
        sys.argv = ["output_checks.py", *argv]
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                main()
            return json.loads(buf.getvalue())
        finally:
            sys.argv = old_argv

    td = tempfile.mkdtemp(prefix="output_checks_selftest_")
    try:
        transcript = os.path.join(td, "transcript.md")
        with open(transcript, "w") as fh:
            fh.write("## Keynote\n"
                     "[speaker_0] We believe the world model is the next platform, and every "
                     "company will be rebuilt on top of it within five years.\n")

        # quotes — passing input: a quote lifted verbatim from the transcript
        passing = os.path.join(td, "pass.md")
        with open(passing, "w") as fh:
            fh.write('On stage, he argued that "the world model is the next platform" twice.\n')
        out = run(["quotes", "--draft", passing, "--transcript", transcript])
        ck("quotes: verbatim quote scores above the threshold and reports its speaker",
           out["summary"]["no_match"] == 0 and out["quotes"][0]["verdict"] == "match"
           and out["quotes"][0]["score"] >= out["threshold"]
           and out["quotes"][0]["speaker"] == "speaker_0")

        # quotes — failing input: a quote that appears in no transcript
        failing = os.path.join(td, "fail.md")
        with open(failing, "w") as fh:
            fh.write('He also claimed that "quantum synergy redefines everything" off stage.\n')
        out = run(["quotes", "--draft", failing, "--transcript", transcript])
        ck("quotes: fabricated quote is flagged no-match",
           out["summary"]["no_match"] == 1 and out["quotes"][0]["verdict"] == "no-match"
           and out["quotes"][0]["score"] < out["threshold"])

        sources_draft = os.path.join(td, "sources.md")
        with open(sources_draft, "w") as fh:
            fh.write("Acme raised $20M in Series A funding (https://acme.example/round).\n"
                     "Valuation tripled across the category last year.\n"
                     "A plain closing sentence with no figures at all.\n")
        out = run(["sources", "--draft", sources_draft])
        claims = out["claims"]
        # quotes — sources: passing input: the figure sentence is listed and its inline URL counted
        ck("sources: the funding sentence is a claim candidate with its inline URL counted",
           out["summary"]["claim_candidates"] == 2 and len(claims) == 2
           and claims[0]["has_url_inline"] is True and out["urls_in_draft"] == 1)
        # sources — failing input: the unattributed claim is listed without a URL; the plain sentence is not
        ck("sources: the unattributed valuation claim is listed with no URL, the plain sentence is not",
           claims[1]["has_url_inline"] is False and all("plain closing" not in c["sentence"] for c in claims))

        # ---- x (E-05): one passing thread, one failing input per check ----
        hook = "Last night a founder said the quiet part: their AI stack costs more than the team it replaced."
        good_thread = "\n---\n".join([
            hook,
            "Every vendor demo showed the same three slides. Nobody showed the invoice.",
            "The pattern to watch: budgets moving from seats to outcomes, with no baseline to compare against.",
            "More on what the room agreed and argued about: https://recap.example/room-12",
        ])
        ok_thread = os.path.join(td, "thread_ok.md")
        with open(ok_thread, "w") as fh:
            fh.write(good_thread)
        out = run(["x", "--draft", ok_thread])
        ck("x: a 4-post thread with one last-post link and no hashtags reports zero findings",
           out["summary"]["posts"] == 4 and out["summary"]["findings"] == 0)

        long_post = os.path.join(td, "thread_long.md")
        with open(long_post, "w") as fh:
            fh.write(hook + "\n---\n" + "word " * 60)  # 300 chars > 280
        out = run(["x", "--draft", long_post])
        ck("x: a post over 280 chars is flagged post_length",
           any(f["check"] == "post_length" and f["post"] == 2 for f in out["findings"]))

        long_hook = os.path.join(td, "thread_hook.md")
        with open(long_hook, "w") as fh:
            fh.write("Takeaway " * 25 + "\n---\nnext post")  # 225 chars, < 280 but >= 200
        out = run(["x", "--draft", long_hook])
        ck("x: a hook of 200+ chars is flagged hook_length even under the 280 cap",
           any(f["check"] == "hook_length" and f["post"] == 1 for f in out["findings"]))

        early_link = os.path.join(td, "thread_link.md")
        with open(early_link, "w") as fh:
            fh.write("Hook with the link up front: https://recap.example/room-12\n---\npost two")
        out = run(["x", "--draft", early_link])
        ck("x: a link in a non-last post is flagged link_placement",
           any(f["check"] == "link_placement" and f["post"] == 1 for f in out["findings"]))

        two_links = os.path.join(td, "thread_2links.md")
        with open(two_links, "w") as fh:
            fh.write("Hook post\n---\nmiddle post https://a.example/one\n---\nlast post https://b.example/two")
        out = run(["x", "--draft", two_links])
        ck("x: two links in one thread are flagged link_count",
           any(f["check"] == "link_count" for f in out["findings"]))

        tag_wall = os.path.join(td, "thread_tags.md")
        with open(tag_wall, "w") as fh:
            fh.write(hook + "\n---\npost two #AgenticAI #MLOps")
        out = run(["x", "--draft", tag_wall])
        ck("x: two hashtags on one post are flagged hashtag_count",
           any(f["check"] == "hashtag_count" and f["post"] == 2 for f in out["findings"]))
    finally:
        shutil.rmtree(td, ignore_errors=True)

    fails = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  {'✓' if ok else '✗'} {n}")
    print(f"selftest: {len(checks) - len(fails)}/{len(checks)} output-checks cases pass")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
