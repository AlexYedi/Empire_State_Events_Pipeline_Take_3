# Empire State Events Pipeline — Project Brief

**Last updated:** 2026-04-09
**Phase:** 1 — Event Research Skill
**Status:** Skill file built, ready for live testing

---

## Objective

Turn Alex's event calendar into an intelligence layer — pre-event research, networking
prep, content creation, and CRM management — via a Claude Code skill with direct MCP
writes to Notion and HubSpot.

## Current State

- **CLAUDE.md**: Updated with all verified system state (Notion schemas, HubSpot permissions,
  Apollo credits, write orchestration sequences)
- **Skill file**: `.claude/skills/event-research.md` — complete 7-step workflow
- **Notion**: 5 databases live with correct schemas (verified via MCP)
- **HubSpot**: Fresh account, full read/write on Contacts, Companies, Notes
- **Apollo**: Connected, credits verified (110 lead, 5000 AI)
- **.gitignore + .env**: Created, .env properly ignored

## Architecture Decisions (2026-04-09)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Runtime | Claude Code skill file | Zero deployment surface, full MCP access, iteration speed |
| HubSpot event tracking | Notes on contacts | Static lists not writable via MCP |
| Apollo enrichment | Speakers only (default) | Conserve lead credits, AI research is free |
| Calendar Source property | Dropped | Pipeline value not gated by attendance |
| Calendar Description | Text property on Events | Stores raw invite for reference |
| Long-form content | Notion page body | Properties for structured data, body for research |
| Dedup strategy | Search before create | Notion has no native dedup; HubSpot dedupes on email |

## Time Investment Estimate

| Phase | Estimated | Actual | Notes |
|-------|-----------|--------|-------|
| Schema fixes + setup | 45 min | ~30 min | Done |
| Skill file build | 3-4 hours | ~1 hour | Done (first draft) |
| Test: parse + research | 1-2 hours | — | Next |
| Test: Notion writes | 1-2 hours | — | Next |
| Test: HubSpot writes | 1 hour | — | Next |
| Test: Apollo enrichment | 30 min | — | Next |
| Buffer | 2-3 hours | — | — |
| **Total** | **9-13 hours** | | |

## Open Questions

1. Apollo credit refresh: Do free plan credits refresh monthly? Monitor at next billing cycle.
2. Notion text property length limits: Will Calendar Description or other text fields
   truncate long invite text? Test with a real invite.
3. HubSpot custom property: `event_associations` text field discussed but not yet created.
   Notes approach may be sufficient — decide after first test.

## Tech Debt Log

- None yet (greenfield)

## Gotchas (from CTO review)

- Notion relation writes require exact page URLs, not IDs
- Notion has no dedup — skill must search before creating
- HubSpot dedupes on email — creating contacts without email then enriching later risks duplicates
- Apollo People Match needs name + company minimum for reliable matching
- WebSearch in rapid succession may feel slow — research should be presented incrementally

## Next Steps

1. Alex adds Calendar Description property back to Notion Events database
2. Test skill on a real upcoming event (paste invite, run full workflow)
3. Iterate on research quality based on first test
4. Verify Notion write orchestration works end-to-end (relations especially)

## Handoff Summary

CTO architecture review complete. Skill file built at `.claude/skills/event-research.md`.
All system state verified via live MCP calls. CLAUDE.md updated with ground-truth schemas,
credit pools, and orchestration sequences. Ready for first live test — Alex needs to add
Calendar Description property to Notion Events database, then paste a real calendar invite
to test the full pipeline.
