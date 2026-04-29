# MOVED — Signal Pipeline → gtm-os

**This work has moved to its own repo: [AlexYedi/gtm-os](https://github.com/AlexYedi/gtm-os).**

The Signal Pipeline began as a subdirectory of `Empire_State_Events_Pipeline_Take_3` because it was scoped as an extension of the events pipeline. As the scope expanded into a full GTM operating system (always-on signal layer, parallel Hub site, broader stack integration than just events), it warranted its own repo.

## Where things now live

| Was here (Empire) | Now here (gtm-os) |
|---|---|
| `Signal_Pipeline/PROJECT_BRIEF.md` | `gtm-os/PROJECT_BRIEF.md` |
| `Signal_Pipeline/SESSION_BOOTSTRAP.md` | `gtm-os/SESSION_BOOTSTRAP.md` |
| `Signal_Pipeline/Phase_0/` | `gtm-os/Phase_0/` |
| `Signal_Pipeline/MCP_SETUP.md` | `gtm-os/MCP_SETUP.md` (expanded to 11 servers) |
| `Signal_Pipeline/gtm-os-bootstrap/` | consumed during migration; deleted post-migration |

## What stays in Empire

- The events pipeline itself (skills, CLAUDE.md, predecessor architecture notes) remains canonical here.
- HubSpot + Notion MCP wiring (`.mcp.json`, `.env.example`, `MCP_SETUP.md` at root) stays — Empire still uses the same data systems for the events pipeline work.
- This `MOVED.md` stays as a breadcrumb for anyone who lands on the old path.

## Why two repos, not one

Empire is the **events pipeline** — a finished, shipped module with a defined scope (calendar invite → research → Notion + HubSpot writes). It's stable.

gtm-os is the **always-on GTM operating system** — actively under construction, broader stack, different cadence. Mixing the two slowed both down. Splitting them lets each evolve at its own pace and keeps the gtm-os repo's commit history clean from day one.

## Cross-references

- The events pipeline is gtm-os's first completed module, NOT a thing being restarted.
- gtm-os reads from / writes to many of the same Notion DBs and HubSpot records as the events pipeline. They share the data plane; the codebases are separate.
- Phase 0 of gtm-os explicitly inventories what the events pipeline produced as the foundation layer.

---

*If you're a fresh agent landing here looking for Signal Pipeline context: go to gtm-os and read `SESSION_BOOTSTRAP.md`.*
