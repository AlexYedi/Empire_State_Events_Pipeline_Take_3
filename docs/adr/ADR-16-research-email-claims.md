# ADR-16: Gmail-derived evidence from research briefs may stay in the graph as `email_signal` claims

**Status:** **Proposed 2026-11-19.** Alex decided to keep these claims (Command Center g1118-t2, "Keep them: research-lane email context is allowed"); this ADR records that decision and the conditions it needs. Builds on [ADR-11](ADR-11-retire-inbox-signal-lane.md) and does not reverse it.
**Governs:** whether claims whose evidence came from Alex's Gmail, through the research specialists' Gmail-first reads, may live in the Market-Intelligence graph, and on what terms.

## Context

ADR-11 retired the inbox *signal lane*: the `/scan-inbox` miner and its writer. It kept Gmail **reads** for `company-researcher` and `person-researcher` (Decision 5). Those reads feed research briefs, and the research-lane claim parser (`substrate.py`, extractor `parse`) tags claims that rest on that evidence with `provenance_tier = 'email_signal'`.

On 2026-11-18, the 20 `email_signal` claims that existed on 10-30 were purged (exported first, then deleted; Alex approved). 21 more exist, created after ADR-11: 3 on 11-01, 16 on 11-10 and 2 on 11-15. All 21 are in the research lane; 19 are approved and 2 are candidates. They come from the path ADR-11 deliberately kept, not from the retired miner. So the open question was whether that path may keep writing claims at all.

Alex decided 2026-11-19: keep them. Email context is real signal for research (who is talking to whom, what a vendor told him directly), and the research lane is allowed to use it.

## Decision

1. **Research-lane `email_signal` claims are allowed.** The 21 stay. The research parser may keep emitting the tier. Nothing is purged.
2. **They are private by construction.** An `email_signal` claim is never used in public output: no post, carousel, hub page or anything else that leaves Alex's private surfaces. Evidence from private correspondence is other people's confidences unless proven otherwise (CLAUDE.md invariant 4). `output-evaluator`'s source check treats an `email_signal` claim as unsourced for public copy.
3. **The PII boundary still applies in full.** Email addresses and phone numbers never enter the spine (ADR-9). Every write goes through `spine_client.py`, whose guard and tier-0 denylist check are unchanged.
4. **Apply the 11-19 claim-judge rule as for any other claim.** Approval requires the evidence to say the claim, as with `web_verified` claims under the 11-19 judge decision (g1118-t1). Where a page can't be fetched to check an `email_signal` claim, it stays candidate unless Alex approves it.

## Consequences

- YED-263's `email_signal` question closes with "keep, private-only". The 11-18 purge of the pre-10-30 rows stands: those came from the retired miner.
- **Follow-up (separate PR, guarded):** enforce Decision 2 in code. Readers that build public output exclude `email_signal`, and `output-evaluator` flags any figure that traces to one. Until that lands, Decision 2 is enforced by review only. That is a gap in one layer of a privacy control, which counts as a defect even with review behind it, so the follow-up is owed, not optional.
- Reversing this (purging the tier again, or stopping the parser emitting it) means a new ADR.
