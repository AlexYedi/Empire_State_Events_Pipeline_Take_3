# Worked fixture — reply grading for a `connection` goal (fictional)

**Everything here is fictional** — people, companies, replies and numbers are invented for the
fixture. A real tagging run records the do-nothing baseline with the outcome itself (three
fields in the Outcome Value line — see SKILL.md); this fixture's baseline values are labeled
placeholders demonstrating the *shape*, never real measurements.

Content artifact: a fictional speaker DM (`linkedin_dm_speaker` type) from the fictional event
"Harbor City AI Builders Night" (2026-08-19, fictional). Goal = `connection`, Target = "1 accepted
+ one reply that moves the conversation forward". 10 notes sent.

## Step 2 — realized signal, graded with the 11-label taxonomy

| # | Person (fictional) | Lane | First reply | Label |
|---|---|---|---|---|
| 1 | Dana Reyes | LinkedIn DM | "This is relevant — what times work next week?" | `positive_interested` |
| 2 | Priya Natarajan | LinkedIn DM | "Send over the details, happy to look at it in Q3." | `positive_soft` |
| 3 | Tom Okafor | LinkedIn DM | "Not me — you want our head of growth, Lena Marsh." | `positive_referral` |
| 4 | Sam Whitfield | LinkedIn DM | "Appreciate it, but we're set for this year." | `negative_notfit` |
| 5 | Ada Kowalski | Email | "Not right now — circle back next quarter." | `negative_notnow` |
| 6 | Jules Martin | LinkedIn DM | "Why are you messaging me? Who did you say you were with?" | `negative_hostile` |
| 7 | Robin Chen | LinkedIn DM | "I'm out of the office until the 15th." | `ooo` |
| 8 | Mei Zhou | Email | Delivery failure (invalid address) | `bounce` |
| 9 | Leo Brandt | LinkedIn DM | — (no reply within 21 days) | `no_response` |
| 10 | Ana Duarte | LinkedIn DM | "What does your company actually do?" | `neutral_question` |

## Step 3 — grade (HITL; numbers computed, not vibes)

- **positives** = `positive_interested` (1) + `positive_soft` (1) + `positive_referral` (1) = **3**
- **denominator** = sent (10) − `ooo` (1) − `bounce` (1) = **8**
- **positive reply rate** = 3 ÷ 8 = **37.5%**
- **risk signal**: `negative_hostile` = 1 of 10 sent — one annoyed contact; read it before the next
  send to this cohort.
- **Outcome grade proposal**: `hit` — Target "1 accepted + one reply that moves the conversation
  forward" is met (one `positive_interested`). Alex confirms or overrides.

## Step 4 — Outcome Value line (both halves, per YED-212)

```
[LinkedIn/HubSpot] positives 3/8 sent = 37.5% vs null baseline 5% (do-nothing; method: measured do-nothing reply rate for connection_note; 2026-08-01→08-15)
```

The `5%`, its method and its date range are the **fictional fixture placeholders**. In a real run
the three baseline fields are real: `null_baseline` = the do-nothing rate for the action type,
`baseline_method` = how it was established, `baseline_date` = when it was measured. If no baseline
has been established yet, record `null_baseline: none` and surface the gap — never invent one.

## Baseline fields this fixture demonstrates

| Field | Fixture (fictional) value | What a real run records |
|---|---|---|
| `null_baseline` | 5% | the measured do-nothing reply rate for `connection_note` |
| `baseline_method` | do-nothing | how it was established (e.g. measured reply base rate without the intervention) |
| `baseline_date` | 2026-08-01→08-15 | when it was measured |
