# PROPOSAL — PII Phase 2: the canonical regex set (email · E.164 · US phone)

**Status:** PROPOSAL — not adopted. Alex decides. (S-04, YED-183; docs lane.)
**Guard code is human-only** (CLAUDE.md invariant 1): this document **reads** `spine_client.py`'s patterns and changes nothing. Nothing here is wired into the guard.

## The proposed set

Verbatim from `spine_client.py` (lines 89–95, read 2026-10-30, unmodified):

```python
# Email — with lookbehind/lookahead guards so URLs and handle paths don't false-positive.
EMAIL_RE = re.compile(r"(?<![\w/])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w])")

# Phone — requires separators or a leading +/( so that 10-digit integers
# (unix timestamps, ids) never false-positive.
PHONE_RE = re.compile(
    r"(?<![\w.+-])(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![\w])"   # 555-123-4567 / (555) 123 4567
    r"|(?<![\w.])\+\d{10,15}(?![\w])"                                                        # +15551234567 (E.164 compact)
)

# Bot / no-reply addresses are not personal data.
EMAIL_ALLOWLIST_RE = re.compile(r"^(?:noreply|no-reply|donotreply)@|@users\.noreply\.github\.com$", re.I)
```

**Recommendation: adopt the current patterns verbatim as the documented canonical set.** They are already enforced by 30 selftest cases (`spine_client.py --selftest`), have survived real post-event runs, and the two deliberate design choices — *separators-or-plus required* for phone, *lookbehind excluding `/` and word chars* for email — are what keep timestamps, IDs and `/@handle` URLs from false-positive. A Phase-2 Postgres backstop (`pii-db-check.sql`, sibling proposal) should carry these **same shapes**, not a second dialect.

### Known gaps (verified, accepted trade-offs — or fixes to decide)

Every gap below was verified against the live module by importing `EMAIL_RE`/`PHONE_RE` and probing (not by reading alone):

| # | Input shape | Example (fake) | Caught today? | Verdict |
|---|---|---|---|---|
| G1 | UK/EU *formatted* international (`+dd ddd dddd dddd` grouping) | `+44 20 5555 1234` | **missed** | Out of scope by design — the spec's set is E.164 + US. Events are NYC; accept. |
| G2 | 10-digit US number with **no** separators | `5551234567` | **missed** | Deliberate: the same shape as a unix timestamp. Tightening would trade a real PII leak for false-positive refusals on metadata IDs. Accept; document. |
| G3 | US number with leading country code and dashes | `1-555-123-4567` | **missed** | Genuine near-miss: the `(?<![\w.+-])` lookbehind blocks a match that starts right after `1-`. Small, fixable (`(?:1[\\s.-])?` prefix) but it edits guarded code — needs human review if wanted. |

## Test-string tables

All strings are fake: `*.example` domains, 555 numbers. Every row was **executed** against the current module on 2026-10-30; the "current guard" column is observed behavior, not prediction. "allowlisted" = matched by `EMAIL_RE` but suppressed by `EMAIL_ALLOWLIST_RE`.

### True positives — must be caught (30)

| # | Label | Test string | Current guard |
|---|---|---|---|
| T1 | email basic | `jane.doe@example.com` | caught |
| T2 | email plus-tag | `jane+nyc@example.com` | caught |
| T3 | email uppercase | `JANE@EXAMPLE.COM` | caught |
| T4 | email multi-label TLD | `jane_doe@sub.example.co.uk` | caught |
| T5 | email embedded in bio | `reach me at jane@example.com anytime` | caught |
| T6 | email punct boundary | `email: jane@example.com;` | caught |
| T7 | email in parens | `(jane@example.com)` | caught |
| T8 | email after mailto | `mailto:jane@example.com` | caught |
| T9 | email sentence end | `ping jane@example.com.` | caught |
| T10 | email hyphen domain | `j.doe@ex-ample.example` | caught |
| T11 | email long TLD | `jane.doe@mail.longer.example` | caught |
| T12 | email nyc subdomain | `jane@nyc.example` | caught |
| T13 | email minimal local | `a@b.example` | caught |
| T14 | email digits local | `jane123@example.org` | caught |
| T15 | email hyphen org | `contact@startup-xyz.example` | caught |
| T16 | email io subdomain | `jane@io.example` | caught |
| T17 | phone E.164 compact | `+15551234567` | caught |
| T18 | phone +1 spaced | `+1 555 123 4567` | caught |
| T19 | phone +1 dashed | `+1-555-123-4567` | caught |
| T20 | phone +1 paren | `+1 (555) 123-4567` | caught |
| T21 | phone paren, space seps | `(555) 123 4567` | caught |
| T22 | phone paren, dash seps | `(555) 123-4567` | caught |
| T23 | phone dashes | `555-123-4567` | caught |
| T24 | phone dots | `555.123.4567` | caught |
| T25 | phone spaces | `555 123 4567` | caught |
| T26 | phone tel scheme | `tel:+15551234567` | caught |
| T27 | phone 13-digit E.164 | `+1555123456789` | caught |
| T28 | phone trailing punct | `+15551234567.` | caught |
| T29 | phone nested-metadata style | `+1 (555) 123-4567 (cell)` | caught |
| T30 | phone UK formatted — **gap G1** | `+44 20 5555 1234` | **missed** (accepted) |

### True negatives — must pass clean (17)

| # | Label | Test string | Current guard |
|---|---|---|---|
| N1 | allowlisted noreply | `noreply@example.com` | allowlisted |
| N2 | allowlisted GitHub noreply | `jane@users.noreply.github.com` | allowlisted |
| N3 | unix timestamp | `1757700000` | clean |
| N4 | timestamp in prose | `ts 1757700000 logged` | clean |
| N5 | LinkedIn `/@handle` URL | `https://linkedin.com/in/@janedoe` | clean |
| N6 | semver | `version 1.2.3 shipped` | clean |
| N7 | PR URL | `https://example.com/pr-1234567` | clean |
| N8 | issue number | `ticket #1234567 filed` | clean |
| N9 | ISO date | `due 2023-10-15 ok` | clean |
| N10 | 7-digit local only | `call 5551234 ext 2` | clean |
| N11 | handle | `handle @jane on stage` | clean |
| N12 | incomplete email | `ping jane@ about it` | clean |
| N13 | bare domain | `site example.com works` | clean |
| N14 | long digit run | `order 555123456789012345 ok` | clean |
| N15 | IP address | `server 192.168.1.100 up` | clean |
| N16 | coordinates | `at 40.7128, -74.0060` | clean |
| N17 | 10-digit compact — **gap G2** | `5551234567` | **missed** (deliberate) |

Rows T30 and N17 are the same string classes as G1/G2 above — kept in the tables so any future regex change has its regression cases written down. Any adopted change to the guard must turn the 47 rows here into selftest cases **as test data only** (allowed on guarded paths).

## Adoption decision for Alex

- **A1 (recommended):** ratify the current three patterns as the canonical set, no code change; carry these shapes into the Phase-2 DB backstop.
- **A2 (optional):** also fix gap G3 (`1-555-…`) in `spine_client.py` — guarded-path change, human review required, plus the 3 new selftest rows.
- **A3 (reject):** closing gap G2 by matching separator-less 10-digit numbers — rejected in this document because timestamps and IDs share the exact shape; a metadata-scan false-positive fails closed on legitimate writes.

## Relations

Refines **ADR-9** (tier-2 scan, the "scans recursively" property). Feeds `pii-db-check.sql` (same proposal set). If A2 is adopted it touches the guarded `spine_client.py` — invariant 1's human-review rule applies.
