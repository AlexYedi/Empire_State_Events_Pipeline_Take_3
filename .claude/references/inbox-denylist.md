# Inbox denylist — the scan-boundary control for `inbox-miner`

**Status: v1 ACCEPTED — reviewed by Alex 2026-09-15 (ADR-7 Decision 3 gate satisfied).**

> **This status line is machine-read (YED-161).** `python3 .claude/scripts/inbox_boundary.py gate --stage discover`
> refuses to run the whole-inbox pass until it reads `**Status: v1 ACCEPTED**` here. Entries below are parsed
> by section: backticked domains/globs/senders under the *domains*, *senders*, and *spam* headings; backticked
> label paths under the *Gmail labels* heading (children match). Bare words are ignored and listed by
> `report`. Rules, markers, the protected-senders list, and the review log contribute no entries.

The scan boundary is **whole inbox minus this denylist** (Alex's choice). This file is the *first* thing
`/scan-inbox` reads. Anything matching an entry here is **never fetched, distilled, classified, logged,
or written** — it does not enter the pipeline at any stage. This is the primary PII/SEC control
(YED-81). It is version-controlled so the boundary is auditable and changes leave a trace.

## Matching rules (how the miner applies this)

1. **Order:** denylist check happens on the thread's `From`, the sender **domain**, and the thread's
   **Gmail labels** — *before* any body is read. A match at any level → skip entirely.
2. **Domain match** = the part after `@`, case-insensitive, incl. subdomains (`@chase.com` matches
   `alerts.chase.com`).
3. **Sender match** = exact address, case-insensitive.
4. **Label match** = the thread carries a Gmail label whose full nested path is listed here.
5. **Conservative default (the tie-breaker):** if a thread looks personal / 1:1 / sensitive and matches
   nothing on the *allow* side (no company-signal / event / job markers), **skip it** rather than
   classify it. Coverage is a Phase-1 tuning dial; leakage is not. When in doubt, exclude.
6. The denylist is a **skip list, not a delete list** — nothing is ever removed from Gmail.

## Denylisted domains — institutional + Alex-reviewed (2026-09-15)

These categories are almost never AI/tech market signal and frequently carry PII/financial/health data.
Seeded 2026-09-08 as safe defaults; extended 2026-09-15 with the real sender domains found behind Alex's
private labels (metadata-only pull), so unlabeled mail from the same institutions is skipped too.

- **Financial / banking / payments / retirement:** `chase.com`, `bankofamerica.com`, `wellsfargo.com`,
  `citi.com`, `amex.com`, `americanexpress.com`, `capitalone.com`, `fidelity.com`, `schwab.com`,
  `vanguard.com`, `paypal.com`, `venmo.com`, `wise.com`, `stripe.com` *(receipts)*, `intuit.com`,
  `turbotax.com`, `massmutual.com`, `empowermyretirement.com`, `adp.com`.
- **Health / insurance / pharmacy:** `myhealth*`, `*insurance*`, `cvs.com`, `walgreens.com`, `zocdoc.com`,
  `getcerebral.com`, `citymd.net`.
- **Government / legal / tax:** `irs.gov`, `*.gov`, `ssa.gov`, `usps.com`, `docusign.net`, `cdlawfirm.net`.
- **Utilities / housing / personal services:** `verizon.com`, `anmgroup.com`, `anmmanagement.com`,
  `lightstonemanagement.com`, `myzion.com`, `onlineportal.appfolio.com`, `appfolio.us`, `key.me`,
  `onboardingsystems.com`, `*.edu`.

> **Target-company resolution (Alex, 2026-09-15).** Ramp and Brex were REMOVED from this list: their events,
> products, tech, and growth stories are signal, and Ramp is a job-search target. Mercury and Plaid are
> companies of interest and were never listed. AppFolio is denylisted only at its tenant-portal subdomain
> and specific no-reply senders, so AppFolio company news stays minable. For every entry still listed, the
> rule is unchanged: **a denylist match wins → skip**.

## Denylisted Gmail labels (from Alex's live label taxonomy; reviewed 2026-09-15)

Any thread carrying one of these labels — or a child under it — is skipped.

- `Me` and every child: `Me/Personal Finance` (Fidelity, 401k, Amex, Charles Schwab, Taxes, Credit,
  Donations), `Me/Health` (Cerebral - ADHD, Gym, Dental, Primary Care), `Me/Apartments` (+ all
  addresses), `Me/IDs`, `Me/NJ IDs`, `Me/NJ Drivers License`, `Me/Cell Phone`, `Me/Personal Info`.
- `Experiences/Travel Documents`, `Experiences/Vacation`, `Experiences/Dinner`, `Experiences/Movies`
  (personal, not signal).
- `Job Hunting` and `Job Hunting/Rejection` — **not private, but out of v1 scope** (job lens is a later
  phase); skip in the company-signal run to avoid mis-routing.
- `Companies/New York Life` — an interview Alex withdrew from; job history, not signal.
- `Companies/Macbook` — a personal purchase.
- `Companies/Square Space` — domain purchases / billing.
- `Companies/TopResume`, `Companies/Resumeble`, `Companies/Jobscan` — resume-writing services; noise.
- `Companies/Network(ing)/Gianna Scorsone` — a personal 1:1 check-in thread (2020).

> Reviewed 2026-09-15: every other `Companies/*` label stays minable, including Mercury, Brex, Ramp, Plaid,
> the expert networks (see Protected senders), and GKY (not denylisted).

## Denylisted senders — specific addresses

- `hello@alerts.hims.com` — Hims (telehealth / health PII).
- `noreply@robinhood.com` — Robinhood (financial / brokerage promos).
- `nysdmv.reservations@qmatic.cloud` — NYS DMV appointment booking (government ID).
- `donotreply@appfolio.com`, `surveys@appfolio.com` — apartment tenant-portal notices.
- `massmutualretirement@digital-delivery.com` — retirement-plan statements.

Personal correspondents (friends, family, neighbors, the tenant association) are **deliberately not listed
by address**: writing third parties' personal email addresses into git history is its own PII leak. Their
threads are covered by the `Me/*` and `Companies/Network(ing)/*` labels above plus matching rule 5
(conservative default). Add an address here only if a real run shows one slipping through.

## Protected senders — never skip, never mark spam (Alex, 2026-09-15)

Informational, not parsed as entries. These are paid expert-network requests Alex does not want lost in the
noise. They must never be added to this denylist or approved into a mark-spam batch, and Stage-A
worksheets should list them at the top rather than in the frequency tail.

- Guidepoint: `guidepointglobal.com`, `guidepoint.com`
- AlphaSights: `alphasights.com`
- Dialectica: `dialecticanet.com`

*(v1 enforcement is the HITL spam-batch review. A machine check that refuses to deny or spam-mark these
domains is a deferred follow-up.)*

## Always-allowed markers (the other side of the boundary — informational, not part of matching)

For orientation only — these are what the classifier looks *for* (company-signal path v1):
- Product-update / changelog / release senders from company/product domains.
- Newsletters are **already handled** by `trend-radar` (`label:Content/newsletters`) → the miner skips
  that label to avoid double-processing.

## Spam / noise senders (populated by Stage-A discovery, then batch-approved)

**Goal: reduce noise while increasing signal (Alex, 2026-09-09).** Stage-A discovery flags high-volume,
low-value senders (promotional blasts, cold outbound, dead subscriptions) as **suspected spam**. These are
presented as a worksheet; **on Alex's explicit en-masse approval**, each approved sender is:
1. **added here** (pipeline denylist — never read again), and
2. **`mark_thread_spam` in Gmail** (trains the filter — the "block" action; reversible spam→inbox), and
3. if it needs a real unsubscribe click or a filter rule (no MCP tool), added to the **unsubscribe worksheet**.

Never marked spam without the batch approval, and never a Protected sender. Entries land below once approved:

- `# --- approved spam/deny+block senders (appended after each Stage-A review) ---`

## Review log

- 2026-09-08 — v1 draft seeded (institutional categories + conservative default). **Pending Alex review**
  of: personal-sender list, private-label list, and the Ramp/target-company caveat.
- 2026-09-09 — added the spam/noise batch-approval mechanism (deny + Gmail mark-spam + unsubscribe worksheet)
  per Alex's "reduce noise while increasing signal" steer. Discovery window set to last 12 months.
- 2026-09-15 — **v1 ACCEPTED (Alex).** Ramp + Brex removed (signal); Mercury, Plaid, expert networks, and GKY
  confirmed minable. Denylisted labels added: New York Life, Macbook, Square Space, TopResume, Resumeble,
  Jobscan, Gianna Scorsone. Institutional domains + senders extended from a metadata-only pull of the
  `Me/*` labels (Amex's real sending domain, retirement/payroll, Cerebral, CityMD, Verizon, landlords and
  property managers, KeyMe, DocuSign, a law firm, NYS DMV booking). `docusign` bare word replaced by
  `docusign.net`; duplicate `Me/Personal Info` removed. Personal correspondents intentionally not listed by
  address. Expert networks recorded as Protected senders. The whole-inbox `discover` gate is now open.
