# S-04 D1 — PII backstop twin-rehearsal runbook

**Linear:** YED-183 (D1) · **Alex approval:** 2026-11-01, YED-183 comment `dd28915c` · **Artifacts:** `docs/adr/proposals/pii-db-check.sql` (as fixed in PR #249, YED-279) + `supabase/migrations/0014_drop_legacy_person_email.sql` (PR #252) · **Instrument:** `supabase/scripts/rehearse_s04_d1.py`

**Naming** (same as `2B_REHEARSAL_RUNBOOK.md`): *Empire prod DB* = `oicikjyzmxqfomrrqkvf` (`The-Prod-Brain`). *Phantom Test Case twin* = `ytfzzsxcxxbejnowmkmk` (disposable clone).

> **Hard gate.** No statement runs against the Empire prod DB until the entire sequence — **including a PROVEN rollback** — is green on the twin. `rehearse_s04_d1.py` refuses a prod target outright (no override flag). Prod promotion is Alex's dashboard paste (CLAUDE.md invariant 2), only after this rehearsal is green.

## What is being rehearsed

| Piece | Artifact | What it does |
|---|---|---|
| PII Phase-2 DB backstop | `docs/adr/proposals/pii-db-check.sql` | `assert_no_contact_pii()` + `assert_no_pii_columns()` trigger functions; triggers on `public.person` and (catalog-guarded) `canonical_v2.person`. Refuses email/phone patterns in free-text and populated contact-PII columns with ADR-9 messages. |
| Legacy column drop (D1) | `supabase/migrations/0014_drop_legacy_person_email.sql` | Drops the legacy, empty `email` column from both person tables — the backstop's documented promotion prerequisite (the YED-81 nulling writer is retired; nothing reads the column). |

Order of application: **backstop first** (its Part-2 tolerance of the empty legacy column — YED-279 defect 1 — is a rehearsed behaviour), **then the drop**, then confirm both behave on the post-drop state.

## Prereqs

- Env: `PHANTOM_TEST_DB_PASSWORD` (twin postgres password), `PSQL_BIN` (default `psql` on PATH). Optional: `SUPABASE_API_KEY` (prod service key) — preflight currency counts only, read-only REST.
- Connection: direct `db.ytfzzsxcxxbejnowmkmk.supabase.co:5432` where IPv6 is available; otherwise the **session pooler** (IPv4):
  ```
  TWIN_DB_HOST=aws-0-<region>.pooler.supabase.com TWIN_DB_USER=postgres.ytfzzsxcxxbejnowmkmk
  ```
  (same `TWIN_DB_HOST` / `TWIN_DB_PORT` / `TWIN_DB_USER` overrides `rehearse_s1a.py` accepts;
  hostname is **dashed**, not dotted — `aws-0.<region>…` is NXDOMAIN. The pooler tenant
  must exist: a disabled pooler reports `FATAL: (ENOTFOUND) tenant/user <user> not found`
  from every region).

## The gate sequence (what the script runs)

| Gate | What happens | Pass condition |
|---|---|---|
| 0 preflight | twin reachable; `public.person` shape vs prod; `person.email` populated count **must be 0** (0014's probe — STOP if not); `canonical_v2.person` existence recorded; `check_pii_regex_parity.py` clean; prod REST counts (advisory) | all checks print OK |
| 1 snapshot A | person-column fingerprint (order-insensitive), PII trigger/function fingerprint, row counts | recorded |
| 2 apply backstop | `pii-db-check.sql` verbatim; cv2-guard NOTICE captured as evidence | psql rc=0 |
| 3 verify (pre-drop) | `staging/s04_d1_verify.sql`: clean spine write **passes**; email / US-phone / E.164 in free-text **refused** (`ADR-9 tier-2 violation…`); populating the legacy email column **refused**; nulling update **passes**; cv2 triggers exist IFF the table does; probes cleaned, counts unchanged | `S-04 D1 VERIFY: PASS (n checks)` |
| 4 re-apply backstop | second paste is a clean no-op | psql rc=0 + verify passes |
| 5 apply column drop | `0014`; catalog post-condition: no `email` column on either person table; verify re-run (post-drop leg) | post-condition + verify PASS |
| 6 rollback | `staging/s04_d1_rollback.sql` | psql rc=0 |
| 7 snapshot C | **must equal snapshot A** | rollback PROVEN only then |
| 8 (optional) `--leave-applied` | re-apply both + verify — leaves the twin in the post-D1 state for Alex's inspection | verify PASS |

## Run it

```bash
python supabase/scripts/rehearse_s04_d1.py --preflight-only     # wiring + twin-shape check first
python supabase/scripts/rehearse_s04_d1.py                      # full gate, ends rolled back
python supabase/scripts/rehearse_s04_d1.py --leave-applied      # full gate, ends in post-D1 state
python supabase/scripts/rehearse_s04_d1.py --reset-first        # after an interrupted rehearsal
```

Capture evidence by teeing the output:

```bash
python supabase/scripts/rehearse_s04_d1.py --leave-applied 2>&1 | tee supabase/evidence/s04_d1_rehearsal-$(date -u +%Y%m%dT%H%M%SZ).log
```

The evidence log contains twin hostnames and gate results only — the connection password is never printed and must never be committed. Before/after schema is captured inside the log by snapshots A and C (and diffed by gate 7).

## After the rehearsal is green

1. Attach the evidence log + `S-04 D1 VERIFY: PASS` lines to the YED-183 Linear issue as the rehearsal record.
2. Promotion is a **separate, Alex-gated step** (CLAUDE.md invariant 2): Alex pastes `pii-db-check.sql` then `0014` into the prod dashboard SQL editor, in that order, re-running the backstop's Part-3 block afterwards only if `canonical_v2.person` is created later on prod.
3. Prod rollback (if ever needed) is the same `s04_d1_rollback.sql` shape — the column comes back empty; the YED-81 gitignored export remains the only record of pre-scrub values.


## Addendum: migration 0017 twin rehearsal (YED-309 / YED-319, 2026-11-05)

Migration `0017_pii_backstop_intl_phone.sql` (PR #277) is **live on prod**:
Alex applied it via the dashboard at ~22:08 UTC on 2026-11-04, and the live
function body was verified byte-identical to the migration file (md5
`6b7dd66c…`; YED-309). It has its own executable harness:
`supabase/scripts/rehearse_0017.py`.
It follows the same gate shape as `rehearse_s04_d1.py` (preflight → snapshot A →
probes → apply → verify → idempotent re-apply → rollback → snapshot C == A →
leave applied) and refuses a prod target outright.

Corrections/notes discovered while running it (2026-11-05 run, evidence
`supabase/evidence/0017_rehearsal-20261105T000700Z.log`, ALL GATES GREEN):

- The session-pooler region index is **not always `aws-0`**: the twin answers on
  `aws-1-us-east-2.pooler.supabase.com`. Try both `aws-0-` and `aws-1-` for the
  region before concluding the pooler tenant is missing.
- `psql` must be on PATH (`PSQL_BIN` override) and `PHANTOM_TEST_DB_PASSWORD`
  must be **exported** — unlike a `.env` file read by the script; psql itself
  will hang on a password prompt if the var is unset.
- `rehearse_0017.py` has **no `--reset-first`** (its D1 counterpart does). A
  rehearsal that ends `--leave-applied` leaves the twin carrying 0017, and gate 0
  then refuses to run. To re-run: apply the rollback leg by hand first —
  Part 1 of `pii-db-check.sql` at `622a221` (the pre-0017 function body) — and
  confirm gate 0's preflight reports `has_alt3=false` before the full run.
- The twin's row counts and cv2 presence drift between rehearsals (twin refreshes
  for other work, e.g. 0016); the harness reads shape from the live catalog, so
  this is expected and not a failure.
