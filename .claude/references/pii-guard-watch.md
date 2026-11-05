# PII guard watcher — playbook (YED-320)

**What this is.** YED-319 decided to ship the international-phone alternative to `PHONE_RE` (PR #277,
YED-309) and measure its precision in practice rather than argue it further on paper. This page
pre-registers the measurement: six triggers with their thresholds, chosen before any data came in,
plus the response each one arms. A trigger that fires means "run the response below", not "start
a discussion".

**Code.** `.claude/scripts/pii_guard_watch.py` (stdlib; `--selftest` 76/76), the telemetry hook in
`.claude/scripts/spine_client.py` (`--selftest` 51/51), and the weekly Action
`.github/workflows/pii-guard-watch.yml`. This is a PII-guard area (CLAUDE.md invariant 1): any change
to these files gets human review.

Related issues (plain text, not links): YED-319 (the decision), YED-320 (this build), YED-321
(revisit gate), YED-309 (intl-phone regex, PR #277), YED-316, YED-318.

## The two data sources, and what each one can see

| Source | Where it lives | What it holds | In CI? |
|---|---|---|---|
| **Shadow scan** (`--shadow`) | Postgres, read-only, every run | Per-column **counts** of LIVE, each alternative, VARIANT_B, VARIANT_C, LOOSE, LOOSE-not-LIVE, bare 10/11-digit numbers (prose columns), non-allowlisted EMAIL, numeric prose. Never text. | Yes (weekly) |
| **Refusal telemetry** | `.claude/.state/pii-refusals.jsonl` (gitignored) on the machine that ran the writer | One line per refusal: `ts, table, path, rule, batch_size, caller, shape, scan_ms`, plus `prose_hint` (phone) or `asset_code` (email). Every 50th clean row that `req()` sends adds `{"rule":"ok_sample","scan_ms",…}`. | **No** |

**What telemetry never records.**
- No value. `shape` is the matched text with digit→`9`, letter→`a`, ≤40 chars.
- `prose_hint` and `asset_code` are booleans computed in memory. The surrounding text is never stored.
- `table` and the top-level column are recorded only when they are in the allowlist (or are a
  known forbidden column), else `<unlisted>`. Every nested key becomes `*`, with list indices kept
  (`metadata.*[2].*`).
- Switch it off with `SPINE_TELEMETRY=off` or `spine_client.telemetry(False)`. Either switch stops
  the recording only; the refusals still happen.

**Survivorship.** This is why the sources split the work. Before #277 is live, alt-3 text can still
reach prod, so the shadow can measure alt-3 precision (F1a). Once it is live, the guard and the DB
backstop keep alt-3 text and non-allowlisted emails *out* of prod. The shadow then sees only
survivors and can no longer measure precision. **Post-merge precision comes from telemetry only**:
F1(b) for phones, F5 for emails.

**The CI gap.** Spine writers run in Alex's sessions, so telemetry exists only locally. In CI,
`--evaluate --no-telemetry` reports F1(b), F3, F5 and F6 as `INSUFFICIENT (no telemetry in CI)`.
Those triggers are only evaluated when someone runs `--evaluate` locally. A durable refusal store (a
spine table the guard writes to) would close the gap. It needs DDL plus a new write path inside the
guard, so it is an open question below and not built.

## Triggers

Below the minimum n, every verdict is `INSUFFICIENT`: no information, never PASS. Rates use the
**Wilson 95% lower bound** (LB), so a few lucky hits can't fire a trigger. A shadow file that is
missing, or older than 8 days, gives `NOT EVALUATED` and exit 1, never QUIET.

| # | Signal | Fires when | Pre-armed response | Owner |
|---|---|---|---|---|
| **F1** | Alt-3 precision | (a) **pre-merge shadow only:** `n_alt3 ≥ 30` and LB(numeric_prose / n_alt3) > 0.20. (b) **telemetry:** `≥ 30` `phone_alt3` refusals and LB(prose_hint / n) > 0.20. Alt-1/alt-2 refusals never count: refusing a real US number is the guard working. Either leg can fire. The PASS/INSUFFICIENT verdict comes from (a) before the merge and (b) after it. | Swap alt 3 for a variant (below). | Alex decides, session builds |
| **F2** | Recall gap: text LIVE does not refuse but a human should look at | A column's `loose_not_live` or `bare_digits_10_11` count **exceeds its acknowledged count** in `.claude/references/pii-guard-baseline.json` (YED-326), **or a corpus column is new or no longer scanned**, **or the baseline is missing / unparseable / older than 90 days** → **REVIEW** (a human must look; never FIRE). At or below the acknowledged count → PASS, so a known-clean scan cannot reopen the same review weekly. | Run `--local-shapes` locally and read the `loose_not_live` and `bare_digits` shapes (column detail is in the run's local output, not the issue). A real phone shape → open a Linear issue to extend `PHONE_RE` through the YED-309 process (spine + `pii-db-check.sql` + migration + parity + probe 0). For bare digits that is the A3 decision (YED-183) reopened with data. Acknowledged noise → hand-check it, update the baseline's per-column counts with a fresh `checked_by` / `checked_at` / `method` in one commit, close the issue. A stale baseline means the same: a fresh hand-check, then re-baseline. | Alex |
| **F3** | Batch blast radius: `guard_body` checks the whole batch before sending, so one refusal aborts every row | ≥ 3 refusals with `batch_size > 1` in 7 days, **or** any refusal with `batch_size > 50` in 7 days | (1) Re-run the aborted batch without the refused row (the rule and shape say why). (2) Open a `decision` issue: keep whole-batch abort, or refuse per row and send the rest with a report. That changes guard behaviour, so it goes through branch, PR and human review. | Alex |
| **F4** | Bypass: the guard refuses LIVE phones and non-allowlisted emails, so any in prod means a write skipped it (or pre-dates it) | LIVE phone matches **or** non-allowlisted email matches on any scanned prod column > 0 | Same day. (1) The column names are in the run's local output, not the issue; re-run `--shadow` locally to see them. (2) `spine_client.py --check-writers` to find a writer outside the guard. (3) Locally, read-only, find the row ids and the writer (`source`, `created_at`). A `created_at` before the guard means legacy, not a live bypass. (4) Scrub with a nulling PATCH through `spine_write.py`, the way YED-296 did. (5) Check that the DB backstop trigger is installed on that table. (6) Write the incident up on the Linear issue. | Alex |
| **F5** | Email precision (telemetry) | `≥ 30` email refusals and LB(asset_code / n) > 0.20. Asset/code-shaped = file-extension TLD (`.png`, `.js`, `.py`, …), `@2x.`, `@1.2.3`, `git@`, placeholder domains (`example`/`test`/`domain`/`email`). | Add an exclusion for the dominant shape to `EMAIL_RE` (e.g. a negative lookahead on file-extension TLDs), mirrored in `pii-db-check.sql`, with `check_pii_regex_parity.py` and a spine selftest case per shape. | Alex decides, session builds |
| **F6** | Guard cost | `ok_sample` p95 `scan_ms` > 50 with n ≥ 200 | Profile `_scan_pii` on the slowest table; usual causes are huge metadata strings or regex backtracking on long digit runs. Fix by capping scanned string length per value, or by tightening the lookahead that backtracks. Never by sampling the scan: every row stays fully scanned. | Session |

### F1 response, ready to execute

1. **Pre-merge:** re-run `--shadow` and compare the `alt3`, `variant_b` and `variant_c` columns. If a
   variant removes most of the `numeric_prose` hits, pick it. **Post-merge:** the shadow can't
   compare variants on refused text. Instead read the `shape` and `prose_hint` of the `phone_alt3`
   refusals in the local telemetry file, then test each shape against VARIANT_B and VARIANT_C in
   Python.
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
unless the counts or shapes say otherwise.

### Detector definitions (from `pii_guard_watch.py` and `spine_client.py`)

- **LIVE** = `spine_client.PHONE_RE` as it stands, read at runtime and passed into the SQL as a
  dollar-quoted literal. **ALT3** = LIVE's third alternative once #277 is merged; until then it is
  #277's candidate. The verdict says which (`alt3_source`).
- **LOOSE** (recall detector): 8–15 digits with at most one separator (`space . ( ) -`) between digits,
  either after a `+`, `00` or `tel:` prefix, or crossing at least one separator. ISO dates and plain
  decimals are excluded. *Deviation from the brief:* a fully optional prefix with any 8 digits would
  flag every `created_at` timestamp, unix time and score in `to_jsonb(row)`, so F2 would be REVIEW
  forever and carry no information. The prefix stays optional, but an unprefixed run must cross a
  separator.
- **BARE** (the known A3 miss class, YED-183): a separator-less 10- or 11-digit number with word
  guards on both sides. It is counted only on prose columns (`claim.claim_text`, `claim.quote`,
  `documents.title`, person `bio`), because in jsonb rows it would be every timestamp and id.
- **numeric_prose** / **prose_hint**: the same classifier in SQL (shadow) and in memory (telemetry),
  built from one word list in `spine_client.py`. A match counts when the next 12 chars contain a
  currency sign, `%` or a unit (`usd eur gbp k m bn b x pp bps pts percent pct ms sec gb mb tb km kg
  users people customers`), or the previous 20 chars contain `revenue growth grew delta up down
  shares users arr mrr yoy qoq increase decrease rose fell gain loss`, or every group after the
  country code is exactly 3 digits. In SQL the match position comes from `regexp_instr` (Postgres
  15+; prod is 17).
- **asset_code** (telemetry, F5): `spine_client.EMAIL_ASSET_CODE_RE` on the refused email.

## Null baselines (as of 2026-11-04), per signal

These are the do-nothing baselines. A trigger's reading means something only against its own:

| Signal | Baseline | What it implies |
|---|---|---|
| F1(a) shadow alt-3 hits | **0 on 13,086 prod rows**; only **22 claims contain `+digit`** | `n_alt3 ≥ 30` may never be reached pre-merge. INSUFFICIENT is the expected reading. |
| F1(b) / F3 / F5 / F6 telemetry | **0 refusals, 0 ok_samples** (telemetry starts with this PR) | Every telemetry leg starts INSUFFICIENT. |
| F2 LOOSE-not-LIVE, bare digits | **acknowledged baseline 2026-11-04** (`.claude/references/pii-guard-baseline.json`): the F2 hand-check cleared 61 rows on prod with **0 real phones**; per-column counts from the same-day read-only twin scan total 54 rows | F2 reviews only the delta over the baseline. The twin lags prod, so a first REVIEW on a small delta is expected, not an incident: hand-check it, then re-baseline. |
| F4 bypass | **0 LIVE hits** on the YED-309 probe's 13,086 rows; emails and the newly added columns (doc_chunks, doc_claims, claim.locator / proposed_entities, documents.author / external_ref) **unmeasured** | A first-run F4 FIRE on those columns may be legacy rows from before the guard. Check `created_at` before calling it a bypass. |

## Revisit gate

YED-321: re-decide YED-319 at **≥ 500 feed items or 2026-12-04, whichever comes first.** Take the
latest weekly verdict plus a local `--evaluate` (with telemetry) to that review.

An `INSUFFICIENT` F1 at the gate is **not evidence** that the alternative is precise. It means the
measurement has not seen enough alt-3 text yet. Before the merge the cause is a corpus with almost no
`+digit` text (baseline: 22 claims). After the merge it is too few `phone_alt3` refusals. The gate
then has three honest options:
1. Extend the window to a stated date or refusal count.
2. Lower the bar explicitly, as a recorded decision with its reason.
3. Accept the alternative on the probe-0 evidence alone, saying so.

A PASS with n ≥ 30 is evidence. A FIRE runs the F1 response.

## How to run

```
# offline, any machine
python3 .claude/scripts/pii_guard_watch.py --selftest

# read-only count scan of prod (needs MI_DB_DSN = session pooler string; PSQL_BIN if psql isn't the libpq default)
python3 .claude/scripts/pii_guard_watch.py --shadow            # writes .claude/.state/pii-shadow.json

# evaluate, locally, with this machine's telemetry
python3 .claude/scripts/pii_guard_watch.py --evaluate          # 0 quiet · 2 FIRE · 3 REVIEW only · 1 NOT EVALUATED / error

# local only, refuses under CI: masked shapes of the hits, for an F2 review
python3 .claude/scripts/pii_guard_watch.py --local-shapes
```

The Action runs `--shadow` then `--evaluate --no-telemetry` every Monday at 09:00 UTC (and on
`workflow_dispatch`). On FIRE or REVIEW it opens or updates one GitHub issue titled
`PII guard watcher: <FIRE|REVIEW> <F#…>`. The body holds counts and verdicts only: no column names,
shapes or ids. A failed or NOT EVALUATED run opens `PII guard watcher run FAILED`. It writes nothing to
Supabase, Notion or Linear, and uploads no artifacts.

## Caveats

- **Writes counted once.** `ok_sample` counts only rows that `req()` is about to send. A
  `write(dry_run=True)` pre-check or a bare `guard()` call is not a write. Refusals are recorded on
  every path, dry runs included: a refused dry run is still a producer trying to send PII.
- **Selftests.** Every `--selftest` in `.claude/scripts` was run with telemetry on: none wrote the
  real file. Their guard calls are either clean (no `ok_sample` outside `req()`) or go through
  spine_client's own redirected selftest. The explicit belt-and-braces (each script's selftest and
  `--dry-run` calling `spine_client.telemetry(False)`) lives in files outside YED-320's scope; it is
  a follow-up.
- **First live run = first ARE execution** of VARIANT_B/C, LOOSE, BARE and the classifiers. They are
  written in the constructs 0017's probe 0 already proved on PG17, but they haven't been run there.
  A compile error aborts the run fail-closed (read-only, nothing written) and opens the failure issue.
- **Scan time.** `doc_chunks.content` is the largest column scanned, and its runtime is unmeasured
  until the first live run.
- **Row-level counts.** Each column counts rows that match, not matches per row. numeric_prose
  classifies only the first alt-3 match in a row.
- **psql error text.** If a query errors, the run prints psql's stderr. The queries hold only
  patterns, and the expected failures (regex compile, syntax, connection, the read-only assert) report
  the query or the connection, not row data.

## Open questions

1. **Durable refusal store.** A spine table (`pii_refusal`: ts, table, rule, shape, booleans,
   batch_size, caller) would let CI evaluate F1(b), F3, F5 and F6. It needs DDL plus a guarded write
   from inside the guard's own refusal path. That is a later decision, not built here.
2. **Feed-only F1(b).** Once the feed lane (S-02) writes, should F1(b) filter on its `caller`?
3. *(Resolved in review)* F4 now counts non-allowlisted emails as a bypass too.
