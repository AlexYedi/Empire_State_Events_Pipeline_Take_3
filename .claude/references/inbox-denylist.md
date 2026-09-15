# Inbox denylist — the scan-boundary control for `inbox-miner`

**Status: v1 DRAFT — requires Alex's review before the first real whole-inbox scan (ADR-7 Decision 3 gate).**

> **This status line is machine-read (YED-161).** `python3 .claude/scripts/inbox_boundary.py gate --stage discover`
> refuses to run the whole-inbox pass until it reads `**Status: v1 ACCEPTED**` here. Entries below are parsed
> by section: backticked domains/globs/senders under the *domains*, *senders*, and *spam* headings; backticked
> label paths under the *Gmail labels* heading (children match). Bare words like `docusign` are ignored and
> listed by `report`. Rules, markers, and the review log contribute no entries.

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

## Denylisted domains — institutional (safe defaults, seeded)

These categories are almost never AI/tech market signal and frequently carry PII/financial/health data.
**Seeded as safe defaults — Alex: confirm, prune, or extend.**

- **Financial / banking / payments:** `chase.com`, `bankofamerica.com`, `wellsfargo.com`, `citi.com`,
  `amex.com`, `capitalone.com`, `fidelity.com`, `schwab.com`, `vanguard.com`, `paypal.com`, `venmo.com`,
  `wise.com`, `ramp.com` *(⚠️ NOTE: Ramp is also a job-search target — see caveat below)*, `brex.com`,
  `stripe.com` *(receipts)*, `intuit.com`, `turbotax.com`.
- **Health / insurance / pharmacy:** any provider portal, `myhealth*`, `*insurance*`, `cvs.com`,
  `walgreens.com`, `zocdoc.com`, health-plan domains. *(Alex to add specific providers.)*
- **Government / legal / tax:** `irs.gov`, `*.gov`, `ssa.gov`, `usps.com`, law-firm domains, `docusign`
  *(when tied to legal/financial, not a contract you want tracked)*.
- **Utilities / housing / personal services:** electric/gas/water, ISP/telecom billing, landlord /
  property-management, `*.edu` personal, delivery/shipping receipts.

> **⚠️ Target-company caveat.** Some denylisted-*category* domains are also job-search targets (e.g.
> `ramp.com` — Alex's first application). A **transactional** email from such a domain (a payment receipt)
> is denylisted; a **careers/recruiter/product-update** email from the same domain is signal. v1 resolves
> this conservatively: **domain on the denylist wins → skip**, and target-company signal is captured via
> the `scan-roles` / event paths and the *newsletter/product* sender lists instead. Revisit with a
> per-purpose allowlist-override in a later phase if this drops real signal. Alex: flag any target-company
> domain you'd rather allow-through now.

## Denylisted Gmail labels (POPULATED 2026-09-09 from Alex's live label taxonomy via list_labels)

Any thread carrying one of these labels — or a child under it — is skipped. These are Alex's real
private-organizing labels (confirmed present in the account):

- `Me` and every child: `Me/Personal Finance` (Fidelity, 401k, Amex, Charles Schwab, Taxes, Credit,
  Donations), `Me/Health` (Cerebral - ADHD, Gym, Dental, Primary Care), `Me/Apartments` (+ all
  addresses), `Me/IDs`, `Me/NJ IDs`, `Me/NJ Drivers License`, `Me/Cell Phone`, `Me/Personal Info`,
  `Me/Personal Info`.
- `Experiences/Travel Documents`, `Experiences/Vacation`, `Experiences/Dinner`, `Experiences/Movies`
  (personal, not signal).
- `Job Hunting` and `Job Hunting/Rejection` — **not private, but out of v1 scope** (job lens is a later
  phase); skip in the company-signal run to avoid mis-routing.

> Confirm: is any `Companies/*` label actually a *personal/financial* relationship (e.g.
> `Companies/New York Life`, `Companies/Mercury`, `Companies/Brex`, `Companies/Ramp`) you'd want
> skipped rather than mined? Flag any to move here.

## Denylisted senders — specific addresses

*(Add exact addresses of individuals / personal correspondents / sensitive services. Alex-owned.)*

- `hello@alerts.hims.com` — Hims (telehealth / health PII) — spotted in the scan, health category.
- `noreply@robinhood.com` — Robinhood (financial / brokerage promos) — finance category.
- `# (Alex to add personal contacts, family, 1:1 correspondents)`

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

Never marked spam without the batch approval. Entries land below once approved:

- `# --- approved spam/deny+block senders (appended after each Stage-A review) ---`

## Review log

- 2026-09-08 — v1 draft seeded (institutional categories + conservative default). **Pending Alex review**
  of: personal-sender list, private-label list, and the Ramp/target-company caveat.
- 2026-09-09 — added the spam/noise batch-approval mechanism (deny + Gmail mark-spam + unsubscribe worksheet)
  per Alex's "reduce noise while increasing signal" steer. Discovery window set to last 12 months.
