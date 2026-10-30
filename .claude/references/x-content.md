# X (Twitter) content contract — E-05

The rules every X draft follows before it reaches Notion `needs_review`. Companion to the
LinkedIn rules in `content-style-guide.md`; the channel plan of record is
`docs/spec-distribution-channels.md` (X row: Core channel, Pilot status). Nothing posts
automatically — drafts only, Alex publishes by hand.

**Rule marking.** Every rule below is tagged one of two ways, per E-05:

- **X platform rule** — enforced or defined by X itself; the source URL is cited and was
  verified 2026-10-30 (re-verify before citing a changed limit in a draft).
- **House style** — our rule, chosen for this pipeline. Traced to E-05 or
  `docs/spec-distribution-channels.md`.

## The rules

| # | Rule | Marking | Source |
|---|---|---|---|
| 1 | **280 characters per post.** Every post in a thread and every standalone post counts separately, including spaces and line breaks. | X platform rule | [How to post — "Compose your message (up to 280 characters)"](https://help.x.com/en/using-x/how-to-post) |
| 2 | **X Premium long posts are out of scope.** Premium extends posts up to 25,000 characters, but the account's Premium status is an open decision (`spec-distribution-channels.md` §6, item 3). Draft to 280 until Alex confirms the handle. | X platform rule (the feature) + house style (our scoping) | [About different types of posts](https://help.x.com/en/using-x/types-of-posts) |
| 3 | **Thread hook under 200 characters.** Post 1 must land the hook well under the 280 cap — it competes with the "show more" fold. | House style (E-05) | — |
| 4 | **Thread length 4–7 posts** (post-event and pre-event threads). Post 1 stands alone for readers who never expand the thread. | House style (`spec-distribution-channels.md` §3, channel map; E-05) | — |
| 5 | **At most 1 link per thread, in the last post.** Links belong at the end, not the hook. When the thread follows up a post-event recap, the link is the Hub long read (owned beats rented). | House style (`spec-distribution-channels.md` §3; §2 principle 2) | — |
| 6 | **At most 1 hashtag per post.** No hashtag walls. | House style (E-05; X best practice of 1–2, made stricter) | — |
| 7 | **Alt text on every image.** X supports image descriptions (alt text) on photos; the description limit is 1,000 characters. We require it on 100% of images — accessibility, and it was a LinkedIn failure mode too. | X platform rule (the capability and limit) + house style (the every-image requirement) | [How to add image descriptions](https://help.x.com/en/using-x/add-image-descriptions) · [How to make images accessible](https://help.x.com/en/using-x/picture-descriptions) |
| 8 | **@handles only when verified.** Write plain names by default, as on LinkedIn. An @-mention goes in only when the handle has been verified as the real account, because a wrong-handle mention is a misdirected public message. | House style (E-05; extends `content-style-guide.md` → Formatting, "Alex applies @-mentions manually") | — |
| 9 | **Native X formats, never reformatted LinkedIn copy.** Pre-event: 1 single post + 1 thread (4–7). In-event: 2–3 live-post templates. Post-event: 1 thread + 1 quote-post of the LinkedIn recap. Each is cut from the approved Notion draft / event brief (COPE — no net-new claims that skipped review). | House style (E-05 product decision; COPE per `spec-distribution-channels.md` §2 principle 1) | — |
| 10 | **Every X post ships 3 variants** to Notion `needs_review`, Platform = X. Never pre-select. First X thread under this spec is a **pilot**: one pilot draft, then Alex's verdict before X becomes a default format. | House style (CLAUDE.md §6 variants rule; pilot per `spec-distribution-channels.md` §2 principle 4) | — |

## Checks (deterministic pre-pass)

Rules 1, 3, 5 and 6 are machine-checkable before the evaluator ever reads a draft:

```
python3 .claude/scripts/output_checks.py x --draft <thread-draft.md>
```

The draft is one thread: posts separated by lines of `---` (the hook is post 1). It reports
per-post character counts, hashtag counts and link placement as JSON. Rules 2, 4, 7–10 are
judgment calls for the output-evaluator / Alex.

## Media

X has no PDF carousels: `python3 .claude/scripts/render_carousel.py <in.html> --x` also
exports each slide as a 1:1 PNG (fit-inside letterbox on a square canvas, no cropping) for
posting slide-by-slide. Alt text (rule 7) is written per image at hand-off.
