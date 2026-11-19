# Prose claim self-containment check (YED-407)

*Run headless by `prose_extract.py selfcheck` (`claude -p`, no tools, no MCP, no setting sources, from an empty temp dir). It is not an agent file. It runs after the deterministic `check` gate.*

*Why it exists: on 2026-11-12, a 100-claim sample of 1,137 gated prose claims scored 86/100 faithful, against a 0.90 floor. 11 of the 14 failures were fragments that mean nothing out of context ("Knock (Series A)", "top 5% measure …"). No length or regex rule separates them from good short claims such as "Ramp $2.44B total raised".*

*This pass only removes claims. It never rewrites one. A claim that gets no verdict is dropped (fail-closed).*

---

You are checking claims extracted from an event research brief before they enter a knowledge graph. Each item gives:
- the claim
- the section and heading it came from in the brief
- the source paragraph

For each item, decide `keep` or `drop`.

**Keep only if all four hold:**

1. **Self-contained.** A reader who has never seen the brief can tell who or what the claim is about, and what it asserts. The subject may come from the heading, so a claim of "Ramp $2.44B total raised" under the heading "Ramp" is fine. Drop bare fragments with no predicate, pronouns or phrases with no referent ("moved on too", "this same meetup", "the top 5%"), and numbers whose unit or meaning is missing ("40K→60K").
2. **Scope kept.** The claim does not widen what the paragraph says. Drop it if it removes the platform, case, sample, time or population the paragraph limits it to (e.g. a stat about one platform's projects stated as a general truth).
3. **Hedges kept.** If the paragraph says "reportedly", "claims", "self-reported", "approximately", "unverified" or similar, the claim keeps it.
4. **Nothing added.** The claim adds no fact, number, entity or causal link that the paragraph, read with its heading, doesn't state.

Do not judge whether the claim is true in the world. Be strict: when in doubt, drop.

Return ONLY one JSON object, no prose before or after it:

```
{"verdicts": [{"i": 0, "keep": true}, {"i": 1, "keep": false, "why": "<≤10 words: rule number + problem>"}]}
```

Give exactly one verdict for every `i` in the input.

ITEMS:
{ITEMS_JSON}
