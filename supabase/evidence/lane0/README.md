# Lane 0 topic backfill: 2026-11-04/05 (YED-307)

ID-only manifests for every `claim_entity` (entity_type='topic', role='about') row lane 0 wrote to prod.
No claim text. Each link records `claim_id`, `topic_id`, `tier`, `confidence` and `lens`.

| Tier | Rule | Calibration (368 held-out claims, Fable-blinded) |
|---|---|---|
| `T1_agree` / `T2_conf` | pilot: LLM and embedding agree on the theme, or LLM conf ≥ 0.8 | 92% / 97% Fable-endorsed |
| `llm>=0.7` | LLM tagger top-topic conf ≥ 0.7 | 95% Fable-endorsed on the hardest (disagreement) cases |
| `fable` | Fable adjudication of every claim the LLM scored below 0.7 | adjudicator of record |

Claims with no topical subject (bios, logistics, job posts, bare numbers, or funding facts whose domain the claim doesn't state) were never linked. The tagger and Fable flagged 1,371 such claims.

**Rollback a batch:** delete `claim_entity` rows matching (claim_id, 'topic', topic_id, 'about') for that manifest's `links`. Writes went through `spine_client` with `resolution=ignore-duplicates`, so re-running a batch is idempotent.

## Phase 2 (2026-11-05): legacy re-tag + company links

- **Re-tag of the 1,946 legacy topic links:**
  - The new tagger agreed with 1,163 (kept).
  - 574 additions were written at conf ≥ 0.7 (`manifest_retag_add.json`).
  - The 783 disputes went to blinded Fable: 246 legacy links upheld, 452 replaced, 65 removed (no topic), 20 removed (retired topic).
  - `manifest_retag_disputes.json` lists every `added` and `deleted` row. **Rollback** = re-insert the `deleted` rows.
- **Company links** (research claims with no company or person link), restricted to existing company rows, never creating one:
  - 893 written at conf ≥ 0.7 (`manifest_company.json`).
  - 204 low-confidence links went to Fable: 159 linked, 45 rejected, plus 3 Minerva claims moved to the correct `Minerva (minerva.io)` record (`manifest_company_fable.json`).

## Phase 3 (2026-11-05): missing companies created, claims relinked

- **Gap:** claims named 376 companies with no `company` row. Created the **39 operating companies with ≥3 claim mentions** (`manifest_company_create.json`; inputs `phase3_new_companies.json`).
  - Search-before-create: prod `lower(name)` match (no duplicates) plus akta `company_search` (free) for the website. Rilo, Mentlio and Git AI aren't covered by akta and have no website.
  - `source='lane0_company_gap'`, `company_type='operating'`.
  - Skipped on purpose: analyst firms (Gartner, Forrester), investors (a16z, Sequoia), foundations and OSS projects (Apache, Linux Foundation, Pipecat), associations and events (PMA, METR, AIMLC, Revolt).
- **Relink:** 189 claims named a new company, in the tagger's `unlisted` output or by a word-boundary text match, giving 207 claim→company decisions.
  - 163 written `about` at conf ≥ 0.7 (`manifest_company_new.json`).
  - 25 below 0.7 went to Fable: 9 `about`, and 12 `asserted_by` where the company is the survey or data publisher rather than the subject (TrustRadius ×5, Jellyfish ×3, EY, Vectara, Carta, Snyk). The rest were rejected (`manifest_company_new_fable.json`).
- **Result, research lens:** claims with a company link went 2,181 → **2,293**. Claims with a company or person link went 3,008 / 3,543 = **84.9%**, up from 81.7% after phase 2. The pre-lane-0 baseline was 54.6%.
- **Rollback:** delete the `claim_entity` rows in the two link manifests, then the `company` rows in `manifest_company_create.json`. Delete the links first, because of the FK direction.
- Scripts `lane0_create_companies.py` and `lane0_relink_new.py` read their inputs from the directory they run in (the session scratchpad). They are committed as the record of the method.

## Phase 4 (2026-11-05): roster-only person links (YED-332, decided by Alex: roster-only)

- **Scope:** only the 507 `person` rows that already exist (speakers and hosts from attended events). No person row was created.
- **Candidates:** claims whose text or quote names a person in full, matched as whole words, with no existing link to that person. That gave 127 candidates across 116 claims and 66 people. One name shared by two person rows was excluded.
- **Role:** blinded Fable adjudication against the person's title and company: 98 `about`, 26 `asserted_by`, 3 `both` (one row for each role), 0 name collisions. 6 verdicts under 0.7 confidence were skipped and are listed in `skipped`.
- **Written:** 123 rows covering 110 claims and 63 people (`manifest_person.json`; script `.claude/scripts/lane0_person_links.py`).
- **Before → after:** person `about` 715 → 811, `asserted_by` 598 → 625. Research claims with any company or person link went 3,008 → 3,016 of 3,543, because most of these claims already carried a company link. What the phase adds is speaker-level questions ("what did X claim, and did it hold up"), not coverage.
- **Rollback:** delete `claim_entity` rows matching (claim_id, 'person', person_id, role) for each entry in `links`.
