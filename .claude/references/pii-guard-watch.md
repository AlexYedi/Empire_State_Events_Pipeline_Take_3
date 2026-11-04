# PII guard watcher — playbook (YED-320)

**What this is.** YED-319 decided to ship the international-phone alternative to `PHONE_RE` (PR #277,
YED-309) and measure its precision in practice rather than argue it further on paper. This page
pre-registers the measurement: six triggers with their thresholds, chosen before any data came in,
plus the response each one arms. A trigger that fires means "run the response below", not "start
a discussion".

**Code.** `.claude/scripts/pii_guard_watch.py` (stdlib; `--selftest` 56/56), the telemetry hook in
`.claude/scripts/spine_client.py`, and the weekly Action `.github/workflows/pii-guard-watch.yml`.
This is a PII-guard area (CLAUDE.md invariant 1): any change to these files gets human review.

Related issues (plain text, not links): YED-319 (the decision), YED-320 (this build), YED-321
(revisit gate), YED-309 (intl-phone regex, PR #277), YED-316, YED-318.

## The two data sources

| Source | Where it lives | What it holds | In CI? |
|---|---|---|---|
| **Shadow scan** (`--shadow`) | Postgres, read-only, every run | Per-column **counts** of LIVE, each alternative, VARIANT_B, VARIANT_C, LOOSE, LOOSE-not-LIVE, EMAIL, asset/code-shaped email, numeric prose. Never text. | Yes (weekly) |
| **Refusal telemetry** | `.claude/.state/pii-refusals.jsonl` (gitignored) on the machine that ran the writer | One line per refusal: `ts, table, path, rule, batch_size, caller, shape, scan_ms`. `shape` = matched text with digit→`9`, letter→`a`, ≤40 chars. Plus every 50th clean row as `{"rule":"ok_sample","scan_ms",…}`. Never the value. | **No** |

A `--selftest` run of any script never writes the real telemetry file. substrate.py, for one, pushes
clean rows through the guard, and those would otherwise pose as writes.

**The CI gap.** Spine writers run in Alex's sessions, so telemetry exists only locally. In CI,
`--evaluate --no-telemetry` reports F1's write-refusal leg, F3 and F6 as
`INSUFFICIENT (no telemetry in CI)`. Those three triggers are only evaluated when someone runs
`--evaluate` locally. A durable refusal store (a spine table the guard writes to) would close the gap,
but it is DDL plus a new write path inside the guard, so it is an open question below and not built.

## Triggers

Below the minimum n, every verdict is `INSUFFICIENT`: no information, never PASS. Rates use the
**Wilson 95% lower bound** (LB), so a few lucky hits can't fire a trigger.

| # | Signal | Fires when | Pre-armed response | Owner |
|---|---|---|---|---|
| **F1** | Alt-3 precision | (a) `n_alt3 ≥ 30` and LB(numeric_prose / n_alt3) > 0.20; **or** (b) phone-refusal rate LB > 0.005 with `n_writes ≥ 500`. Writes ≈ `ok_sample × 50 + refusals`, an approximation (see Caveats). | Swap alt 3 for a variant (below). | Alex decides, session builds |
| **F2** | Recall gap: LOOSE finds phone-like text LIVE does not | `loose_not_live > 0` → **REVIEW** (a human must look; never FIRE) | Run `--local-shapes` locally and read the `loose_not_live` shapes. A real phone shape → open a Linear issue to extend `PHONE_RE` through the YED-309 process (spine + `pii-db-check.sql` + migration + parity + probe 0). Noise only → tighten `LOOSE_RE` in the watcher, record the shape class here, close the issue. | Alex |
| **F3** | Batch blast radius: `guard_body` checks the whole batch before sending, so one refusal aborts every row | ≥ 3 refusals with `batch_size > 1` in 7 days, **or** any refusal with `batch_size > 50` in 7 days | (1) Re-run the aborted batch without the refused row (the shape says which rule). (2) Open a `decision` issue: keep whole-batch abort, or refuse per row and send the rest with a report. That changes guard behaviour, so it goes through branch, PR and human review. | Alex |
| **F4** | Bypass: both layers (spine guard and DB backstop) should refuse, so any LIVE hit in prod means a write skipped them | LIVE matches on any prod column > 0 | Same day. (1) The verdict names the column(s). (2) `spine_client.py --check-writers` to find a writer outside the guard. (3) Locally, read-only, find the row ids and the writer (`source`, `created_at`). (4) Scrub with a nulling PATCH through `spine_write.py`, the way YED-296 did. (5) Check that the DB backstop trigger is installed on that table. (6) Write the incident up on the issue. | Alex |
| **F5** | Email precision | `n_email ≥ 30` and LB(asset- or code-shaped / n_email) > 0.20. Asset/code-shaped = file-extension TLD (`.png`, `.js`, `.py`, …), `@2x.`, `@1.2.3`, `git@`, placeholder domains (`example`/`test`/`domain`/`email`). | Add an exclusion for the dominant shape to `EMAIL_RE` (e.g. a negative lookahead on file-extension TLDs), mirrored in `pii-db-check.sql`, with `check_pii_regex_parity.py` and a spine selftest case per shape. | Alex decides, session builds |
| **F6** | Guard cost | `ok_sample` p95 `scan_ms` > 50 with n ≥ 200 | Profile `_scan_pii` on the slowest table; usual causes are huge metadata strings or regex backtracking on long digit runs. Fix by capping scanned string length per value, or by tightening the lookahead that backtracks. Never by sampling the scan: every row stays fully scanned. | Session |

### F1 response, ready to execute

1. Re-run `--shadow` and compare the `alt3`, `variant_b` and `variant_c` columns. If a variant
   removes most of the `numeric_prose` hits, pick it.
2. Re-run **probe 0** (the 15 strings from migration 0017) against the full candidate pattern
   (alternatives 1 and 2, then the variant), on the twin and read-only on prod, and diff against the
   expected column. Any mismatch means don't ship.
3. Put the variant into `PHONE_RE` alternative 3, `docs/adr/proposals/pii-db-check.sql`, and a new
   migration. Then run `check_pii_regex_parity.py`, `spine_client.py --selftest` and
   `pii_guard_watch.py --selftest`. The selftest pins the probe-0 table below, so it will need its
   expected values updated in the same PR.

**VARIANT_B** (minimum digit count 7 → 9: lookahead `{6,14}` → `{8,14}`):

```
(?<![\w.+-])\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){8,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)
```

**VARIANT_C** (alt 3 plus a negative lookahead that refuses to start on a thousands-style run, i.e.
`+CC` followed only by 3-digit groups; non-capturing groups and nested lookahead only, the same
constructs 0017 already proved on PG17):

```
(?<![\w.+-])(?!\+\d{1,3}(?:[\s.]\d{3}){2,}(?![\s.-]?\d))\+(?=\d(?:(?:[\s.-]?\(0\))?[\s.-]?\d){6,14}(?![\s.-]?\d))\d{1,3}(?:[\s.-]?\(0\)[\s.-]?|[\s.-])\d{1,8}(?:[\s.-]\d{1,8}){1,4}(?![\w]|[\s.-]\d)
```

**Probe 0, expected** (Python `re`, pinned in `pii_guard_watch.py --selftest`; NBSP = `chr(160)`):

| String | #277 | full B | full C |
|---|---|---|---|
| `+44 20 7946 0958` | true | true | true |
| `+44-20-7946-0958` | true | true | true |
| `+49 (0)30 1234 5678` | true | true | true |
| `call +33 1 99 00 12 34 today` | true | true | true |
| `555-123-4567` | true | true | true |
| `+15551234567` | true | true | true |
| `'+44' \|\| chr(160) \|\| '20 7946 0958'` | true | true | true |
| `revenue +12 345 678 EUR` (known FP) | true | **false** | **false** |
| `+1 234 567 890 shares` (known FP) | true | true | **false** |
| `+44 20` | false | false | false |
| `+1.2.3.4.5.6.7` | false | false | false |
| `2026-11-04 12:30:45` | false | false | false |
| `v2.3.4` | false | false | false |
| `+40.7128 -74.0060` | false | false | false |
| `x` | false | false | false |

On probe 0, VARIANT_C dominates: it keeps all 7 real numbers and drops both known false positives.
VARIANT_B costs recall on short real numbers (7–8 digits) that probe 0 doesn't contain. Default to C
unless the shadow counts say otherwise.

### Detector definitions (from `pii_guard_watch.py`)

- **LIVE** = `spine_client.PHONE_RE` as it stands, read at runtime and passed into the SQL as a
  dollar-quoted literal. **ALT3** = LIVE's third alternative once #277 is merged; until then it is
  #277's candidate. The verdict says which (`alt3_source`).
- **LOOSE** (recall detector): 8–15 digits with at most one separator (`space . ( ) -`) between digits,
  either after a `+`, `00` or `tel:` prefix, or crossing at least one separator. ISO dates and plain
  decimals are excluded. *Deviation from the brief:* a fully optional prefix with any 8 digits would
  flag every `created_at` timestamp, unix time and score in `to_jsonb(row)`, so F2 would be REVIEW
  forever and carry no information. The prefix stays optional, but an unprefixed run must cross a
  separator.
- **numeric_prose** (on the first alt-3 match in a row): the next 12 chars contain a currency sign,
  `%` or a unit (`usd eur gbp k m bn b x pp bps pts percent pct ms sec gb mb tb km kg users people
  customers`); or the previous 20 chars contain `revenue growth grew delta up down shares users arr
  mrr yoy qoq increase decrease rose fell gain loss`; or every group after the country code is
  exactly 3 digits.

## Null baselines (as of 2026-11-04)

Every trigger is measured against the do-nothing baseline:

- **0 refusals** recorded (telemetry starts with this PR).
- **0 alt-3 hits on 13,086 prod rows** (the YED-309 prod probe). F1(a) and the F4 bypass check
  start at zero.
- **Only 22 claims contain `+digit`**, so `n_alt3 ≥ 30` may take a while to reach. F1(a) reading
  `INSUFFICIENT` for weeks is the expected state, not a fault.

What a first run is expected to show: F4 PASS, F1/F5 INSUFFICIENT, F3/F6 INSUFFICIENT in CI. F2 is
unknown until the first live `--shadow`. A REVIEW there is information, not an incident.

## Revisit gate

YED-321: re-decide YED-319 at **≥ 500 feed items or 2026-12-04, whichever comes first.** Take the
latest weekly verdict plus a local `--evaluate` (with telemetry) to that review. If F1 is still
`INSUFFICIENT` at the gate, that is the answer: the alternative has met too little international-
looking text in practice to have shown a precision problem.

## How to run

```
# offline, any machine
python3 .claude/scripts/pii_guard_watch.py --selftest

# read-only count scan of prod (needs MI_DB_DSN = session pooler string; PSQL_BIN if psql isn't the libpq default)
python3 .claude/scripts/pii_guard_watch.py --shadow            # writes .claude/.state/pii-shadow.json

# evaluate, locally, with this machine's telemetry
python3 .claude/scripts/pii_guard_watch.py --evaluate          # exit 0 quiet · 2 FIRE · 3 REVIEW only · 1 error

# local only, refuses under CI: masked shapes of the hits, for an F2 review
python3 .claude/scripts/pii_guard_watch.py --local-shapes
```

The Action runs `--shadow` then `--evaluate --no-telemetry` every Monday at 09:00 UTC (and on
`workflow_dispatch`). On FIRE or REVIEW it opens or updates one GitHub issue titled
`PII guard watcher: <FIRE|REVIEW> <F#…>` whose body holds counts only. A failed run opens
`PII guard watcher run FAILED`. It writes nothing to Supabase, Notion or Linear, and uploads no
artifacts.

## Caveats

- **The writes estimate is approximate.** `n_writes ≈ ok_sample × 50 + refusals` counts guarded row
  checks, not unique writes. `spine_client.write()` guards a body before calling `req()`, which
  guards it again, so a clean row through `write()` is counted twice. The F1(b) rate can therefore
  read up to 2× low, which delays that leg firing. It covers every session writer: the feed lane has
  no writer of its own yet.
- **First live run = first ARE execution** of VARIANT_B/C, LOOSE and the classifiers. They are
  written in the constructs 0017's probe 0 already proved on PG17, but they haven't been run there.
  A compile error aborts the run fail-closed (read-only, nothing written) and opens the failure issue.
- **Row-level counts.** Each column counts rows that match, not matches per row. numeric_prose
  classifies only the first alt-3 match in a row.
- **psql error text.** If a query errors, the run prints psql's stderr. The queries hold only
  patterns, and the expected failures (regex compile, syntax, connection, the read-only assert) report
  the query or the connection, not row data.

## Open questions

1. **Durable refusal store.** A spine table (`pii_refusal`: ts, table, rule, shape, batch_size,
   caller) would let CI evaluate F1(b), F3 and F6. It needs DDL plus a guarded write from inside the
   guard's own refusal path. That is a later decision, not built here.
2. **F4 scope.** F4 counts phone (LIVE) hits only, as specified. An email hit in prod is also a
   bypass, unless it's on the noreply allowlist. Should F4 include `email`?
3. **Feed-only F1(b).** Once the feed lane (S-02) writes, should F1(b) filter on its `caller`?
