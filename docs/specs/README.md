# Specs: the three tracks

One index for all four repos. Each spec lives **in the repo it builds in**, so a build agent working there can read it. Each spec has a Linear issue. To start one, point Autobuild at the spec file and expand it into a Blueprint (Product → UX → Technical) before it builds.

- **Empire**: the events pipeline and its public hub (`Empire_State_Events_Pipeline_Take_3`, `empire-state-hub`).
- **GTM**: the gtm-os signal layer and its hub (`gtm-os`, `gtm-os-hub`).
- **Shared**: what both depend on. That's the MI graph and its one write path (`spine_client.py`), the PII and public-safety boundary, the `rooms.json` data contract, and the reference architecture. **Home: this repo**, where the graph's ADRs and write path live.

Lane key: **F** = the factory can build it end to end. **F+C** = the factory builds the code; the live run or a private input stays with Claude Code plus Alex. **A** = Alex's decision.

## Empire
| ID | Spec | Repo | Linear | Lane |
|---|---|---|---|---|
| E-01 | [Hub small fixes](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-01-hub-small-fixes.md) | hub | see spec | F |
| E-02 | [Hub Long Reads + promotion](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-02-hub-long-reads.md) | hub | see spec | F (seed text: A) |
| E-03 | [/builds page + RSS feed](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-03-builds-page-and-feed.md) | hub | see spec | F |
| E-04 | [Public Rooms MCP server (B4)](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-04-rooms-mcp-server.md) | hub | see spec | F |
| E-05 | [X content contract](empire/E-05-x-content-contract.md) | pipeline | see spec | F (voice review: A) |
| E-06 | [X surfaces on the hub](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-06-x-hub-surfaces.md) | hub | see spec | F |
| E-07 | [Script selftests, index, CI](empire/E-07-script-selftests.md) | pipeline | see spec | F |
| E-08 | [Payload truncation check](empire/E-08-payload-truncation-check.md) | pipeline | see spec | F |
| E-09 | [Job-search skills batch](empire/E-09-job-search-skills.md) | pipeline | YED-257 · YED-256 · YED-258 · YED-220 | F+C |
| E-10 | [Hub themes + layer view](https://github.com/AlexYedi/empire-state-hub/blob/main/docs/specs/empire/E-10-hub-themes-and-layers.md) | hub | YED-178 · YED-126 | F |

## Shared
| ID | Spec | Repo | Linear | Lane |
|---|---|---|---|---|
| S-01 | [Graph read loop](shared/S-01-graph-read-loop.md) | pipeline | YED-260 · YED-264 · YED-265 (factory) · YED-261 · YED-262 (session) | F+C |
| S-02 | [Feed layer: code half](shared/S-02-feed-layer-code.md) | pipeline | YED-251 | F+C |
| S-03 | [Reference-architecture layers](shared/S-03-reference-architecture-layers.md) | pipeline | YED-126 | F |
| S-04 | [PII Phase 2: proposals only](shared/S-04-pii-phase-2-proposals.md) | pipeline | YED-183 | F (docs) · A (adopt) |
| S-05 | Agent guardrail layer (`AGENTS.md`, `.obvious/skills`, `.obvious/review`) in all four repos | all | see spec | Done (this PR set) |

## GTM
| ID | Spec | Repo | Linear | Lane |
|---|---|---|---|---|
| G-01 | [Next 16 upgrade](https://github.com/AlexYedi/gtm-os-hub/blob/main/docs/specs/gtm/G-01-next-16-upgrade.md) | gtm-os-hub | GTM-8 | F |
| G-02 | [V2 panels + topic-movement filter](https://github.com/AlexYedi/gtm-os-hub/blob/main/docs/specs/gtm/G-02-v2-panels.md) | gtm-os-hub | GTM-8 · YED-249 (hub part) | F |
| G-03 | [University D1/D2/D5 drafts](https://github.com/AlexYedi/gtm-os-hub/blob/main/docs/specs/gtm/G-03-university-curriculum-drafts.md) | gtm-os-hub | GTM-10 | F (voice: A) |
| G-04 | [Public-repo truth pass](https://github.com/AlexYedi/gtm-os/blob/main/docs/specs/gtm/G-04-public-repo-truth-pass.md) | gtm-os | see spec | F |

**Not in a spec, and why:** GTM-4 shipped (PR #6, 2026-08-07; close it). GTM-11 is a decision. GTM-29 needs Alex's Supercut recordings first. YED-238 (HubSpot) and YED-244 (pitch) are human-gated. YED-204 is a GitHub Support ticket. YED-263 is a decision. YED-267 and YED-268 are parked with triggers.

## How to run a spec in Obvious
1. Open the spec, then start an initiative from it ("Build docs/specs/… in this repo").
2. Expand it into a Blueprint if the spec marks phases as TODO. Approve the **plan card** only after checking its file list against the spec's "Must not touch" list.
3. One PR per executable. `requireHumanMerge` is on; Claude Code pre-reviews every PR.
