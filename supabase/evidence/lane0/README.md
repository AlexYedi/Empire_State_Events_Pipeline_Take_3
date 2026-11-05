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
