# inbox-miner — company alias map (v1)

One entity is named many ways across newsletters. This map resolves variants → one canonical company
slug BEFORE the `GET /company` dedup (SKILL.md B3 Step 1), so the same company doesn't fragment into
several rows. Read at the start of B3; **append new aliases in the same run** (grows like
`signal-taxonomy.md`). Matching: case-insensitive, after slug-normalization (strip legal suffix/punct).

## Canonical map

| canonical slug | company (display) | aliases / variants (→ this) |
|---|---|---|
| `openai` | OpenAI | OpenAI, OpenAI Inc, ChatGPT, GPT-6, **Astra** (GPT-6 Astra), Codex |
| `anthropic` | Anthropic | Anthropic, Claude, **Fable 5.1** (Claude model), Claude Code |
| `xai` | xAI | xAI, Grok, **GrokBot**, **SpaceXAI** (newsletter renaming seen in The Code) |
| `google` | Google | Google, Google DeepMind, DeepMind, Alphabet, Google AI Studio, Gemini |
| `meta` | Meta | Meta, Meta AI, **Muse** (Meta's agent), Facebook |
| `clay` | Clay | Clay, Clay.com, Clay Sequencer |
| `microsoft` | Microsoft | Microsoft, MSFT, Azure, GitHub (parent; note: GitHub *notifications* are self-exhaust, excluded per allowlist) |

## Notes / cautions
- **Product ≠ company.** "Astra" is an OpenAI *product*; the company row is `openai`, product named in `description`. Same for Muse→meta, Fable 5.1→anthropic.
- A newsletter's *renaming* (GrokBot/SpaceXAI) is an alias, not a new entity — do not create a separate row.
- When unsure whether two names are the same entity, DON'T alias-merge (under-merging is recoverable; a false merge corrupts). Flag for review instead.

## Growth log
- 2026-09-10 — seeded from cohort v1 (the parallel product-naming in this timeline: Astra=GPT-6, Fable 5.1=Claude; the xAI/GrokBot/SpaceXAI cluster in The Code).
