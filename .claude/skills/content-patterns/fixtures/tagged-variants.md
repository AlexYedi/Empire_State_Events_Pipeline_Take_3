# Fixture — tagged 3-variant experiment with a worked baseline-relative verdict

Synthetic example for the variant-tagging convention in [`goal-tagging.md`](../goal-tagging.md)
(E-09 / YED-220, harvest note row 4). Fictional numbers; no private inputs. The standing
default post is the **control** and supplies the baseline; the three shipped variants each
carry a `variant_tag` recording the single variable they intend to change. Executable
convention check: `python3 .claude/scripts/test_variant_tags.py --selftest`.

## Experiment block

- content_type: linkedin_post_post (3 variants, per the style guide)
- baseline: 2.0% engagement — null baseline, median of the prior 8 posts on the standing format
- launched: 2026-10-01
- judged: 2026-10-22 (21-day wait satisfied)

## Variant A

variant_tag: hook_type
result: 4.5% engagement
verdict: keep — 2.25× baseline (winner ≥ 2×). Promote the contrarian-claim hook to the default for the depth post.

## Variant B

variant_tag: format
result: 0.8% engagement
verdict: kill — 0.40× baseline (loser < 50%). Reason logged: the essay format halves engagement vs the do-nothing baseline at this audience size; reverting to the standing format.

## Variant C

variant_tag: opener
result: 2.6% engagement
verdict: iterate — 1.30× baseline (in band). Discipline slip noted in the log: this variant also changed the hook, so attribution is weaker. Enforcement is tag-only (goal-tagging judgment J3): the convention records the intended variable and does not reject the variant.
