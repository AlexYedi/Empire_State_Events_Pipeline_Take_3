# Inbox allowlist — the senders `inbox-miner` reads at BODY level (Stage B)

**Status: v1 ACCEPTED — curated by Alex 2026-09-15 from the first Stage-A discovery pass (ADR-7 Decision 3).**

This is the boundary for the **expensive/risky** stage: `/scan-inbox` reads email **bodies** and extracts
company/product signals **only** from senders/domains/labels listed here. Everything else is never
body-read. This bounds PII exposure, cost, and prompt-injection surface *by construction*. See
`docs/adr/ADR-7-inbox-signal-source.md` for the two-stage rationale; the exclusion side is
`inbox-denylist.md` (a secondary safety net that also applies here).

## How this file gets populated (the two paths in)

1. **Stage-A discovery (one-time, bootstraps this list).** A metadata-only whole-inbox pass
   (sender/domain/subject/frequency — no bodies) proposes high-signal company/product-update senders.
   **Alex reviews the candidate worksheet and promotes entries here.** This is how v1 gets more coverage
   than hand-curation without a recurring whole-inbox body scan.
2. **Label-based widening (ongoing, the ONLY way to add sources after v1).** Alex applies the Gmail label
   **`Pipeline/signal-source`** to any sender/thread he wants mined; the miner treats that label as an
   allowlist extension. No recurring whole-inbox reading is ever re-enabled — new sources come in through
   the label (or a manual add here).

## Matching rules

- Match on sender **domain** (incl. subdomains), exact **sender** address, or an allowed **Gmail label**
  (`Content/Newsletters`, `Pipeline/signal-source`).
- The **denylist wins over the allowlist** on conflict (a domain on both → skip).
- **Newsletters (`label:Content/Newsletters`) ARE allowed** (corrected 2026-09-10) — the miner reads them
  for the *entity* lens (which companies launched/raised/moved); `trend-radar` reads the same mail for the
  *topic* lens. Not a conflict — different extraction. Newsletters are the allowlist anchor.
- A sender being here authorizes **body-reading + signal extraction**; it does not lower any write-gate
  or provenance requirement (ADR-7 Decision 5 still applies to every extracted signal).

## Allowed senders / domains

*(Populated by Stage-A discovery + Alex. A few obvious low-risk seeds below — confirm/prune. Prefer
`product@` / `updates@` / `changelog@` / `release@` / `news@` style senders from company domains.)*

- `ship@info.vercel.com` — Vercel (product/release) — approved 2026-09-09
- `no-reply@contact.elevenlabs.io` — ElevenLabs (product launches) — approved 2026-09-09
- `chanchan@lancedb.com` — LanceDB (company/product digest) — approved 2026-09-09
- `social@cognee.ai` — Cognee (product memo) — approved 2026-09-09
- `claire@naolabs.io` — Nao Labs (product update) — approved 2026-09-09
- `noreply@apollographql.com` — Apollo GraphQL (product/technical POV) — approved 2026-09-09
- `changelog@updates.linear.app` — Linear (changelog/releases) — approved 2026-09-10
- `updates@braintrustdata.com` — Braintrust (evals product) — approved 2026-09-10
- `philip.kiely@hello.baseten.co` — Baseten (model serving) — approved 2026-09-10
- `updates@email.grok.com` — Grok/xAI — approved 2026-09-10
- `team@mail.lmstudio.ai` — LM Studio — approved 2026-09-10
- `team@mail.vapi.ai` — Vapi (voice AI) — approved 2026-09-10
- `mongodbteam@messages.mongodb.com` — MongoDB — approved 2026-09-10
- `googleaistudio-noreply@google.com` — Google AI Studio — approved 2026-09-10
- `teams@intercom.com` — Intercom — approved 2026-09-10
- `newsletter@mobbin.com` — Mobbin (design/product) — approved 2026-09-10
- `a16z@substack.com` — a16z (market theses, company/infra analysis) — approved 2026-09-15 (Stage-A discovery)
- `semianalysis@substack.com` — SemiAnalysis (chips / inference economics) — approved 2026-09-15
- `techpresso@dupple.com` — Techpresso (daily AI/company news) — approved 2026-09-15
- `superhumancode@news.codenewsletter.ai` — The Code (AI/dev news) — approved 2026-09-15
- `newsletter@ittnewsletter.com` — AI Business (enterprise AI + funding) — approved 2026-09-15
- `newsletter@aicollective.com` — AI Collective (AI lab/industry news) — approved 2026-09-15
- `postround@substack.com` — Postround (weekly Series A activity — funding signal) — approved 2026-09-15
- `info@technyc.org` — Tech:NYC Digest (NYC ecosystem) — approved 2026-09-15
- `please-reply@langflow.org` — Langflow AI++ (open stack / RAG) — approved 2026-09-15
- `neweconomies@substack.com` — New Economies (single-company deep dives) — approved 2026-09-15
- `update@digital.metamail.com` — Meta (product launches) — approved 2026-09-15
- `news@news.openhands.dev` — OpenHands (product changes) — approved 2026-09-15
- `team@send.intercom.com` — Intercom (product launches) — approved 2026-09-15
- `jai@deepline.com` — Deepline (release notes) — approved 2026-09-15
- `hello@mail.apollo.io` — Apollo.io (product + GTM; mixed with marketing) — approved 2026-09-15
- `hello@mail.attio.com` — Attio (product; mixed with marketing) — approved 2026-09-15
- `community@mail.attio.com` — Attio community (workshops) — approved 2026-09-15
- `success@mail.attio.com` — Attio success (workshops) — approved 2026-09-15
- `will-leatherman@courses.maven.com` — Will Leatherman / Maven (GTM + agent builds) — approved 2026-09-15
- `demand@mail.datacamp.com` — DataCamp (data/AI stack content) — approved 2026-09-15
- `hello@email.cohley.com` — Cohley (UGC/creator market) — approved 2026-09-15
- `lenny@substack.com` — Lenny's Newsletter (product/growth essays) — approved 2026-09-15
- `elenaverna@substack.com` — Elena Verna (PLG/growth essays) — approved 2026-09-15
- `notboring@substack.com` — Not Boring (company strategy essays) — approved 2026-09-15
- `chinatalk@substack.com` — ChinaTalk (AI/tech policy; expect many off-domain tags) — approved 2026-09-15
- `newsletter@garysguide.com` — Gary's Guide (NYC tech events + ecosystem) — approved 2026-09-15
- `foundersbay@newsletter.foundersbay.com` — Founders Bay (NYC AI/tech roundups) — approved 2026-09-15
- `matthewyglesias@substack.com` — Matt Yglesias (policy/politics; expect off-domain tags) — approved 2026-09-15
- `withallduerespectpodcast@substack.com` — With All Due Respect (politics; expect off-domain tags) — approved 2026-09-15
- `# GitHub OMITTED 2026-09-10 — verified 100% own-repo CI/PR-bot + account-security + marketing (self-exhaust, not market signal). See "NOT allowed" below.`
- `# --- widen from Companies/* labels as needed; add via Pipeline/signal-source label ---`

## NOT allowed — self-generated / operational notifications (not market signal)

Excluded by principle (verified against samples, 2026-09-10): **your own-repo CI/PR/build notifications and your own tools' routine notifications are operational exhaust, not market intelligence.** Do not allowlist:
- `notifications@github.com` / `noreply@github.com` / `no-reply@email.github.com` — own-repo PR-bot comments (`vercel[bot]`, `linear-code[bot]`, `github-actions[bot]`), CI failures, account-security codes, GitHub marketing. (Exception to revisit only if Alex *watches external orgs'* repos for release signal — not the case today.)
- `notifications@clarify.ai`, `noreply@notifications.hubspot.com`, `no-reply@zoom.us`, Vercel/Railway deploy notifications, and similar own-tool routine mail.
> These are also a large share of the inbox's unread volume — a Gmail filter to skip-inbox + label them is a separate hygiene win (Alex's workflow call, not the miner's allowlist).

## Allowed labels

- `Content/Newsletters` — **the allowlist anchor** (~1,039 threads). Read for the *entity* lens (companies/funding/launches/exec-moves named in the body), distinct from `trend-radar`'s *topic* lens on the same mail.
- `Pipeline/signal-source` — the hand-applied widening lever (tag any sender/thread to mine it).

## Review log

- 2026-09-08 — v1 scaffold created. **Awaiting Stage-A discovery output + Alex curation** before Stage B runs.
- 2026-09-15 — **v1 ACCEPTED.** First Stage-A discovery (metadata only; 824 boundary-filtered threads, 311 senders; Forums full year, Promotions ~4 weeks and Updates ~9 days — page-capped). Alex approved all 13 candidate rows (14 senders) plus every sender marked unclear (15). Relevance stays tagged, not filtered: the policy/politics newsletters will mostly tag off-domain. Spam batch and unsubscribe worksheet reviewed separately.
