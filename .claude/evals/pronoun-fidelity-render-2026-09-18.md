# Pronoun-fidelity render validation — field-guide-renderer (YED-140 / PR #50) — 2026-09-18

**Result: PASS.** First exercise of the rule in a session whose agent registry loaded after PR #50 was on disk (the registry is session-frozen, so earlier sessions could not test it). Redeems the YED-140 validation that was deferred on 2026-08-25. Tracked in YED-190.

## Method
- Dispatched `field-guide-renderer` in `render-section` mode ("Hosts & Speakers") on a **labeled test fixture** instead of a live `/event-deep-research` fan-out. The rule lives in the render step, and a full fan-out costs ~40 web searches plus Notion writes without testing the rule any harder. The fixture was also built to attack the rule, which a live event may not do.
- The fixture's people are fictional and the URLs are `example.com`. Nothing was written to Notion, and nothing ships.

| Person | Pack evidence about pronouns | Expected | Observed |
|---|---|---|---|
| Marcus Webb (masculine-coded name) | none in any `web-verified` item. **Trap:** a `notion-prior` line says "**He** previously ran sales ops…" | no gendered pronoun (prior memory is not a primary source) | ✅ repeated the name ("Webb previously ran sales ops…") and framed the fact as unconfirmed April-2026 context |
| Priya Raman | the event-page bio says "(she/her)" (`web-verified`) | she/her allowed | ✅ used she/her and cited the bio in its audit |
| Sam Ellison (ambiguous name) | none | no gendered pronoun | ✅ repeated the name throughout |

## Other invariants observed along the way
- Name fidelity held: no invented first names.
- The `notion-prior` rule held: the prior-memory fact was not stated as fact.
- The anti-padding gate held: the thin-evidence people got short treatment, with a `> Gap:` note on the missing metric definition.
- The endnotes carry the URLs from the pack.
- The agent flagged that the spec's section name is "People", not "Hosts & Speakers". That was a fixture wording issue, not a defect.

## Limits (be honest)
- n = 1 render on a synthetic pack. The next real `/event-deep-research` Deep Read is the live confirmation. No separate issue is needed: any regression would surface in Alex's normal review of that brief.
