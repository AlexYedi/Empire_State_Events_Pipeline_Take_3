# OpenAI seat bake-off — stage 1 result (2026-09-20)

Rule fixed in advance: `bakeoff-preregistration.md`. Nothing below was chosen after seeing the numbers.

## Result as first run: **no arm qualifies** (rule 5 — reported as a negative finding, bar not moved).
## After Alex's ruling on the disputed control: **`gpt-5.4-mini` wins on rule 4 (tie → cheaper).**

> **Ruling, 2026-09-20 (Alex).** The one item disqualifying all three arms, `pos-content-style-guide`, was
> **mislabelled**. The seats were right: the guide claimed 4:5 gives "~65% more vertical space than 16:9" when
> the true figure is **122%** (1.25 / 0.5625), and asserted a 3,000-char cap as "verified June 2026" with no
> source. Both are fixed in `content-style-guide.md`, and the control is relabelled `neg-`. Recomputed from the
> *existing* logged runs — no arm was re-run, nothing was re-scored to taste:
>
> | arm | recall | false-flag | $/run |
> |---|---|---|---|
> | **`gpt-5.4-mini`** | **3/4** | **0/2** | **$0.044** |
> | `gpt-5.4` | 3/4 | 0/2 | $0.113 |
> | `gpt-5.5` | 3/4 | 0/2 | $0.166 |
>
> Identical measured accuracy at 4× the price spread → rule 4 selects the cheapest. `gpt-5.4-mini` is now the
> OpenAI seat's model in `seats.json`. **It changes nothing about trust:** the seat stays in SHADOW and still
> needs ≥25 prospective runs with ≥8 real flags, κ ≥ 0.60 and recall ≥ 0.70 against Alex's labels to vote.
> The honest caveat is that this is n=6; the tie may simply mean the control set is too small to separate them.

Six controls (3 negative = real pre-fix states Alex flagged, 3 positive = states he acked pass), identical
evidence bundle per item, harness-computed verdicts.

| arm | defect recall | false-flag rate | $/run | disqualified by |
|---|---|---|---|---|
| `gpt-5.4-mini` | 2/3 | **1/3** | $0.042 | rule 1 (false flags > 1/6) |
| `gpt-5.4` | 2/3 | **1/3** | $0.127 | rule 1 |
| `gpt-5.5` | 2/3 | **1/3** | $0.166 | rule 1 |

**All three arms scored identically on accuracy.** A 4× price difference bought nothing measurable on this set.

## The finding under the finding: one control is probably mislabelled

Every arm's single false flag is the **same item**, `pos-content-style-guide_md-c46fb8d`, and each reached it
independently with a confidence-honesty cap, citing specific unsourced quantitative claims (two arms named the
same two lines, L98 and L198). Raw scores before the cap were 0.745–0.835, i.e. all three thought the artifact
was otherwise fine.

Three independent models converging on the same lines is better evidence that **the label is wrong** than that
all three are wrong. The manifest's `resolution_caveat` predicts exactly this: an ack is mapped to content by
taking the commit preceding it, which is unsound when the judged content was uncommitted at ack time. Alex may
have acked a *later* version of this guide as passing.

**This is Alex's call, not the harness's.** Relabelling a control because it disqualified every arm is precisely
the rule-bending the pre-registration exists to prevent. So the item stands as-is and the arms stay disqualified
until he rules. If he re-labels it, the conditional result is: all three arms tie at 2/3 recall with 0 false
flags, rule 4 (tie → cheaper) selects **`gpt-5.4-mini` at $0.042/run**, a quarter the cost of the provisional
default. That would be a decision-relevant outcome, which is why it must not be self-awarded.

## Also learned (harness defects this exposed, all fixed)

1. **`check-refs` counted gitignored paths as dangling**, capping three positive controls at 0.60. Absent-by-
   design files (`.claude/.state/`, `settings.local.json`, the private refs) are an environment fact, not a
   defect. This had been silently mis-capping *every* judge run made in a worktree.
2. **A gitignored directory only matches `git check-ignore` with a trailing slash**, so `.claude/.state` slipped
   through the first fix.
3. **The pre-call budget check used `max_output_tokens` as its forecast**, which made `gpt-5.5` look like a
   $0.52 run and blocked that arm entirely. Ceiling and forecast are now separate; real protection is the
   monthly/lifetime caps computed from *actual* ledger spend.
4. **The manifest stored abbreviated blob SHAs** and one resolved ambiguously, so a materialised control did not
   match its claimed blob. The privacy guard caught it and refused to send — working exactly as intended. All
   SHAs are now full length.

Items 1–3 would each have quietly corrupted the numbers. They are the reason this file reports a pilot of six
rather than a verdict on sixteen.

## Spend
$7.49 of the $45 lifetime cap across 66 billed calls (including the three discarded runs above). Stage 2 (the
remaining 10 controls) is deliberately **not** run: it would cost ~$3.50 to refine a comparison whose arms are
currently tied and disqualified.
