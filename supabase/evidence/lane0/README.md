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
