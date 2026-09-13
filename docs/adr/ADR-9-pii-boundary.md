# ADR-9 — The PII boundary: three tiers, one guard

**Status:** Accepted 2026-09-13 — Alex ratified decisions 1–3 in `.claude/proposals/yed-81-sec-pii-guardrails.md` (YED-81): email/phone never in the spine (contact detail lives in HubSpot) · hard-fail guard · code chokepoint now, Postgres constraint in Phase 2.
**Governs:** what personal data may exist where, across the base pipeline (Notion), the Market-Intelligence spine (Supabase), the public hub, and HubSpot.

## Context

Personal data enters the system from research briefs, event rosters and transcripts, inbox scanning, and document claims. Until now the only rules were prose: a Notion schema that *can* hold Email/Phone/Notes, a spine `person` table that *does* hold `email`, a denylist that described itself as the primary control but was enforced by no code, and a hub whose safety rested on fields never having been modeled. Roadmap v2 Phase 1 (post-event → MI, YED-160) and Phase 0 (whole-inbox scan, YED-161) each multiply the personal data in flight; both were gated on a real boundary.

## Decision

| Tier | Surface | May hold | Never holds | Enforced by |
|---|---|---|---|---|
| **0 — never enters** | inbox scan boundary | — | anything matching `inbox-denylist.md` | scan-side (YED-161) + write-side backstop in `spine_client.guard` |
| **1 — private review** | Notion People / Companies / Events | professional context; contact PII (Email · Phone · Notes) **only from Alex-provided input** | research- or scrape-derived contact PII | `notion-write-gotchas.md` convention (n); `notion-writer` mapping |
| **2 — the spine** | Supabase MI graph | `name · title · company_id · linkedin_url · bio/role_context` (free text scanned) | **email · phone**; any contact PII inside free text or `metadata` JSON | `spine_client.guard` — the single write chokepoint; hard-fail |
| **3 — public** | empire-state-hub | aggregates; public-figure (speaker/host) context; public post content | person rows; any contact field | `verify-public-safe.mjs` in `npm run check`; `server-only` clients |
| **CRM** | HubSpot | contact records for real relationships | — | gated post-event step only (YED-142); **one-way** — never read back into tier 2 or 3 |

**Three properties of the guard.** It is the **only** write path to the spine (every writer imports it; a repo check flags any other `rest/v1` writer). It is **hard-fail** — a refusal names the field, the tier rule, and the fix, and there is no in-run override. It **scans recursively** — allowlisting columns is not enough when a `metadata` JSON column exists.

## Consequences

- `person.email` is nulled and no longer written; `backfill_people.py` and `/post-event-content` Step 3.8 change accordingly. Nothing consumed it.
- Six existing writers migrate to `spine_client`; `trend-radar`, `/morning-refresh` and future producers write via `spine_write.py` instead of prose-instructed curl.
- YED-160 and YED-161 unblock. The hub's discipline becomes a failing check rather than a comment.
- **Deferred, deliberately:** retention/TTLs (a future ADR); a Postgres CHECK/trigger on `person` as Phase-2 hardening (needs DDL); client-bundle scanning (YED-82 launch gate).

## Relations

Refines **ADR-7** (the inbox boundary is tier 0; D5's injection guard stands). Sits on **ADR-0/1** (one graph = tier 2). Adds a finding class to **ADR-8**'s system graph (a REST writer outside the chokepoint). Numbered from `main` per the README convention (ADR-8 was the last on `main`).
