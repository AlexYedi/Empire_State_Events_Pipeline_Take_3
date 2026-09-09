# Target Companies — Job-Search Engine (shared reference)

> The company list the Job-Search Engine reads: **role-radar** (careers-page monitoring +
> AI-native-tier scoring), **resume/positioning tailor**, and **interview-prep**. Tiered by
> AI-nativeness (maps to rubric v2's "AI-native company tier" dimension). **Seed list 2026-09-08 —
> Alex redlines.** The `Careers / ATS` column is the monitoring source-of-truth for role-radar v2 —
> fill in each company's careers-page URL + ATS type (greenhouse / lever / ashby / custom) as it's
> confirmed (YED-148 / YED-150). Each new careers domain also needs a `.claude/settings.local.json`
> WebFetch allowlist entry.

## Company → ATS registry (role-radar v2 source — confirmed via curl spike 2026-09-08)

The authoritative mapping role-radar Step 1a curls. Endpoint patterns:
Greenhouse `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true` ·
Ashby `https://api.ashbyhq.com/posting-api/job-board/{board}` ·
Lever `https://api.lever.co/v0/postings/{company}?mode=json`.

| Company | ATS | Token / board |
|---|---|---|
| Anthropic | greenhouse | `anthropic` |
| Vercel | greenhouse | `vercel` |
| Together AI | greenhouse | `togetherai` |
| Verkada | greenhouse | `verkada` |
| Glean | greenhouse | `gleanwork` |
| Snorkel AI | greenhouse | `snorkelai` |
| OpenAI | ashby | `openai` |
| Notion | ashby | `notion` |
| Ramp | ashby | `ramp` |
| Clay | ashby | `claylabs` |
| Perplexity | ashby | `perplexity` |
| Sierra | ashby | `sierra` |
| Cursor (Anysphere) | ashby | `cursor` |
| ElevenLabs | ashby | `elevenlabs` |
| LangChain | ashby | `langchain` |
| Baseten | ashby | `baseten` |
| Cohere | ashby | `cohere` |
| Writer | ashby | `writer` |
| Harvey | ashby | `harvey` |
| Decagon | ashby | `decagon` |
| Zip | ashby | `zip` |

**Deferred — not on the big-3 by slug (Workday/custom; skip v1, no legitimate structured endpoint found):**
Hugging Face · Intercom · Rippling · Mistral (Lever board returned empty). Revisit if an API surfaces.

> This registry is what role-radar reads. The tier tables below carry the *why* + warm-path context.

## Tier 1 — Frontier / AI-native (rubric AI-native-tier = 25)

| Company | Why | Careers / ATS | Warm path? |
|---|---|---|---|
| Anthropic | Frontier lab; Claude is Alex's core stack; CSM-Top-Accounts is the ICP exemplar | _tbd_ | — |
| OpenAI | Frontier lab; Account Director archetype exemplar | _tbd_ | — |
| Clay | GTM platform; AE-Strategic + Enterprise Growth Strategist exemplars; PLG+community | _tbd_ | Everett Berry (People DB) |
| Vercel | Agentic infra; Enterprise AE exemplar; strong PLG/dev pull | _tbd_ | — |
| Notion | AI workspace; Solutions Consultant exemplar; PLG | _tbd_ | — |
| Sierra | Conversational-AI agents; enterprise CS/AE | _tbd_ | — |
| Perplexity | AI search; commercial roles | _tbd_ | — |
| Anysphere (Cursor) | AI coding; PLG dev pull | _tbd_ | — |
| ElevenLabs | Voice/generative media; this-week webinar host | _tbd_ | — |
| LangChain | Agent framework; GTM roles | _tbd_ | — |
| Baseten | Model inference infra; GLM-5.3 webinar (Philip Kiely) | _tbd_ | — |
| Together AI | Open-model infra | _tbd_ | — |
| Modal | Serverless GPU / sandboxes | _tbd_ | — |
| Hugging Face | Open-source AI hub (Nvidia acq. pending) | _tbd_ | — |
| Cohere | Enterprise LLMs | _tbd_ | — |
| Mistral | Open-weight frontier (raised €3B) | _tbd_ | — |
| Snorkel AI | Data-centric AI; sells to frontier labs; Stanford AI Lab origin; DaaS Engagement Manager = book-owning EM exemplar (consumption/rev-rec) | greenhouse `snorkelai` | — |

## Tier 2 — AI-forward high-growth (rubric AI-native-tier = 20)

| Company | Why | Careers / ATS | Warm path? |
|---|---|---|---|
| Ramp | Existing #1 target; finance-org native fit; surfaced GTM roles | _tbd_ | — |
| Intercom | AI customer service; Clay customer | _tbd_ | — |
| Verkada | AI security; Clay customer | _tbd_ | — |
| Rippling | HR/IT platform; strong GTM org | _tbd_ | — |
| Zip | AI procurement; surfaced GTM S&O role | _tbd_ | — |
| Glean | Enterprise AI search/work assistant | _tbd_ | — |
| Harvey | Legal AI | _tbd_ | — |
| Hebbia | Knowledge/finance AI | _tbd_ | — |
| Writer | Enterprise generative AI | _tbd_ | — |
| Decagon | AI customer-support agents | _tbd_ | — |

## Signals to capture per company (feed rubric v2 scoring)

- **GTM motion** — PLG / sales-led / hybrid. **PLG is a positive tailwind** (leverage dimension).
- **NYC office?** — drives the location/culture score (NYC/hybrid = 10 · remote-but-NYC-office = 5 ·
  fully-remote-no-office = 0).
- **Open commercial roles** in the four target shapes (CSM / AM-AD-book / Growth Strategist / supported AE).
- **Warm path** — existing People-DB / voice-radar relationship (e.g., Everett Berry ↔ Clay).

## Notes

- Several already sit in the pipeline's orbit: **Clay** (Everett Berry researched, this-week Clay
  livestream), **Ramp** (existing #1 target + role-radar surfaced two GTM roles), **Vercel/Notion**
  (in Alex's stack), **Anthropic** (Claude), **ElevenLabs/Baseten** (this-week events).
- Redline freely — add/cut, especially Tier 2. Companies with a genuine NYC in-person center of
  gravity + PLG motion should sort to the top of the hunt.
