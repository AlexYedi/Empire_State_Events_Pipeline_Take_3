# PRD: Company dossier, the first reader of the MI graph

Status: proposed (2026-10-17) · Owner: Alex · Linear: to open (auth down this session) · Thread: P · Pipeline → P1

## 1. Problem

The MI graph is write-only. On 2026-10-17 it held 3,337 claims (921 written in the last 14 days), and `claim_usage` had 0 rows: nothing reads it. Before a warm DM, a recruiter screen or an interview, Alex rebuilds what he knows about a company by hand from Notion briefs, which is the same People × Companies × Events join that produced the roadmap's warm-paths table. The Dec 12 go/no-go asks whether anything uses the graph, and today the answer is no.

## 2. Who and when

Alex, 10–30 minutes before a touch at a target company: a DM, a referral ask, a screen, or an `/interview-prep` run. The output is private and is never published.

## 3. What it changes

One command returns one private page for one company:

1. **People in the graph:** everyone at the company Alex has been in a room with, with title, where they met, and what each person said (their `asserted_by` claims, first-hand first).
2. **What the company says about itself, from the room:** first-hand claims about the company from any speaker, newest first, each with event, date and timestamp locator.
3. **Outside view:** web-verified facts such as funding, launches and open roles, each labelled with its tier.
4. **Continuity:** the events and dates where the company came up, plus counts of tracked roles.
5. **Hooks:** three openers grounded in specific claims, each citing a claim id `c:xxxxxxxx`.

## 4. Approach: a lens, not a new reader

`.claude/scripts/retrieve.py` is already ADR-10 D4's single retrieval path. It already resolves entities, pulls a relational neighbourhood plus a hybrid semantic match, scores by provenance and recency, fills a token budget, and fails loudly (exit 5) when the graph has claims but the pack keeps none. Nothing calls it today. The build adds a **`company` lens** to it rather than a new script, and needs no DDL:

- **People pull:** `person.company_id = seed` → those people's `asserted_by` and `about` claims. This is the missing hop; see §6.
- **Text pull:** first-hand claims whose text names the company, catching speakers from other companies who talk about it.
- **Ordering:** company-specific claims first, then room context from the same events, within the budget.
- **Weights:** relational and provenance up, semantic down. The lens weights are the only knob (ADR-10).

A thin `/company-dossier <name>` command runs the lens and renders the page locally. The page stays out of git. It can go to Notion only if Alex asks.

## 5. Out of scope

No schema change, no new store, no hook. No `claim_usage` writes in V1 (ADR-10 decision 5 keeps `w_use = 0` until ≥20 outcome rows). No fixes to the producers. The missing company and topic links on first-hand claims (§6) are a separate follow-up and are not in this build. No web research: the dossier reads only what the graph already holds.

## 6. Dry-run evidence (one T1 target, 2026-10-17)

- **Direct company link misses the room.** Of 1,159 first-hand claims, 55 (5%) link to any company and 0 link to a topic; 435 link to a person. For the target, 36 claims link directly to the company and all 36 are `web_verified`, even though Alex attended 7 events where the company was the subject.
- **Two-hop SQL recovers it.** Following person → company and claim text gave about 40 company-specific first-hand claims across 7 events and 5 months: practices, statistics, hot takes and attributed quotes.
- **The current `event` lens is close, but drops the people.** Its pack kept 96 claims (87 first-hand) in 5,973 of 6,000 tokens, and 28 of them name the company or its people. But the People section listed **0 of the 8** people at the company Alex has met, and none of the claims they asserted made the cut. That person hop is the gap this build closes.

## 7. Success test (null baseline included)

**Baseline:** Alex's own recall. Before running the dossier, he writes down what he remembers about the company and its people in 3 minutes.

**Test:** run the dossier on 3 target companies he'll touch next week. Count two things:
- items in the dossier that he'd use in the touch but didn't write down;
- errors: misattributions or stale facts.

| Result | Meaning |
|---|---|
| ≥3 usable new items per company and 0 misattributions | Pass: keep it, use it before every touch |
| Fewer than 3 new items, or within noise of his recall | The graph adds nothing, which is evidence for "no-go" on Dec 12 |
| Any misattribution | Fix it before the dossier is used again |

## 8. One-in-one-out

It replaces the hand-run People × Companies × Events join, and it puts the dormant `retrieve.py` to work rather than adding a reader. No new hook, store or agent.

## 9. Risks

- **Common-word names.** Text match on a company whose name is also an ordinary English word can over-match. Mitigation: match whole words, and require that the claim's event also lists the company or that a person at the company is linked.
- **Stale titles.** `person.title` is never updated after people change jobs. The dossier labels each person with the date Alex last saw them, not as a current fact.
- **Privacy.** Dossiers contain other people's statements and Alex's target list. They are written to a gitignored path and never committed.
