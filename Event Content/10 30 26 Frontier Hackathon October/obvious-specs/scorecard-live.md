# Frontier scorecard (live, updated 16:33)

**Factory PRs: 47 opened · 45 merged.** Baseline: ~6–7 merged PRs on an ordinary active day (74 + 13 merges, 9/27–10/27).

## Ladder

| Tier | Spec | Opened | Merged | With tests | CI ran | Needed me |
|---|---|---|---|---|---|---|
| Setup | setup / onboarding | 5 | 5 | 1 | 5 | 1 |
| Empire | E-01 | 9 | 9 | 0 | 9 | 9 |
| Empire | E-02 | 2 | 2 | 1 | 2 | 2 |
| Empire | E-03 | 2 | 2 | 0 | 2 | 2 |
| Empire | E-04 | 1 | 1 | 1 | 1 | 1 |
| Empire | E-05 | 1 | 1 | 0 | 1 | 1 |
| Empire | E-06 | 1 | 1 | 0 | 1 | 1 |
| Empire | E-07 | 8 | 7 | 1 | 8 | 8 |
| Empire | E-08 | 1 | 1 | 0 | 1 | 1 |
| Empire | E-10 | 2 | 2 | 1 | 2 | 2 |
| Shared | S-02 | 1 | 1 | 0 | 1 | 0 |
| Shared | S-03 | 1 | 1 | 0 | 1 | 1 |
| Shared | S-04 | 1 | 1 | 0 | 1 | 1 |
| GTM | G-01 | 1 | 1 | 0 | 1 | 1 |
| GTM | G-02 | 1 | 1 | 1 | 1 | 1 |
| GTM | G-03 | 3 | 3 | 3 | 3 | 3 |
| GTM | G-04 | 1 | 0 | 1 | 1 | 1 |
| GTM | G-05 | 1 | 1 | 0 | 1 | 1 |
| T1 | 01 hub fixes | 1 | 1 | 1 | 1 | 1 |
| T2 | 07 Linear backlog | 1 | 1 | 0 | 1 | 1 |
| ? | unmapped | 3 | 3 | 0 | 3 | 3 |

## Track A (rules probe)

No probe PRs yet.

## 8 controls (predicted vs evidence)

| Control | Predicted | Evidence so far |
|---|---|---|
| Specs | solo | 21 spec groups produced PRs |
| Context | solo | see Track A |
| Skills | solo | manual |
| QA | help | PRs with tests: 11/47 |
| CI | out | PRs where CI ran: 47/47; green: 45/47 |
| Review | solo | merged with no help from me: 5/45 |
| Loops | help | T1 PRs needing me: 1/1 |
| Design systems | out | T3 PRs: 0, merged 0 |

## PRs

| Repo | # | Spec | State | Mins open→merge | Needed me | Title |
|---|---|---|---|---|---|---|
| pipeline | [#217](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/217) | setup / onboarding | merged | 76 |  | obvious: onboarding contract (.obvious/) — setup run 2026-10-30 |
| hub | [#34](https://github.com/AlexYedi/empire-state-hub/pull/34) | setup / onboarding | merged | 65 |  | Obvious onboarding: local dev verified, sandbox snapshot captured |
| gtm-os-hub | [#15](https://github.com/AlexYedi/gtm-os-hub/pull/15) | setup / onboarding | merged | 51 |  | Onboarding: add .obvious/ agent contract (dev stack healthy, snapshot  |
| gtm-os | [#21](https://github.com/AlexYedi/gtm-os/pull/21) | setup / onboarding | merged | 49 |  | chore: add .obvious onboarding contract (local dev validated) |
| hub | [#36](https://github.com/AlexYedi/empire-state-hub/pull/36) | E-01 | merged | 10 | yes | E-01(1): add root 404 page with header, footer, and site tokens |
| pipeline | [#219](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/219) | E-07 | merged | 6 | yes | E-07: notion_payload.py --selftest — pin every rejection branch |
| hub | [#37](https://github.com/AlexYedi/empire-state-hub/pull/37) | E-03 | merged | 16 | yes | feat(builds): /builds page + content-performance removal (E-03) |
| pipeline | [#220](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/220) | E-07 | merged | 5 | yes | E-07: output_checks.py --selftest — one pass/fail input per check |
| hub | [#38](https://github.com/AlexYedi/empire-state-hub/pull/38) | E-01 | merged | 9 | yes | E-01(2): metadata for Home and About |
| hub | [#39](https://github.com/AlexYedi/empire-state-hub/pull/39) | E-03 | merged | 14 | yes | feat(feed): RSS 2.0 feed at /feed.xml (E-03) |
| hub | [#40](https://github.com/AlexYedi/empire-state-hub/pull/40) | E-01 | merged | 8 | yes | E-01(3): metadata for Work, Journal, and Changelog |
| pipeline | [#221](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/221) | E-07 | merged | 3 | yes | E-07: build_journal.py --selftest — generate from a fixture repo, temp |
| hub | [#41](https://github.com/AlexYedi/empire-state-hub/pull/41) | E-01 | merged | 6 | yes | E-01(4): metadata for Architecture and Build Arcs |
| hub | [#42](https://github.com/AlexYedi/empire-state-hub/pull/42) | E-01 | merged | 12 | yes | E-01(5): sitemap for public routes and room slugs |
| pipeline | [#222](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/222) | E-07 | closed |  | yes | E-07: recompute_relevance.py --selftest — pure scoring pinned, no DB ( |
| hub | [#43](https://github.com/AlexYedi/empire-state-hub/pull/43) | E-01 | merged | 11 | yes | E-01(6): robots.txt — allow all, disallow /ops/, point to sitemap |
| pipeline | [#223](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/223) | E-07 | merged | 10 | yes | E-07: render_carousel.py --selftest — pure checks only, no Chrome |
| hub | [#44](https://github.com/AlexYedi/empire-state-hub/pull/44) | E-01 | merged | 10 | yes | E-01(7): keyboard skip link in the public layout |
| hub | [#45](https://github.com/AlexYedi/empire-state-hub/pull/45) | E-01 | merged | 10 | yes | E-01(8): Event structured data on room detail pages |
| pipeline | [#224](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/224) | 07 Linear backlog | merged | 9 | yes | feat(s-01): MI graph read loop — company lens, resolver, nightly recom |
| hub | [#46](https://github.com/AlexYedi/empire-state-hub/pull/46) | E-01 | merged | 9 | yes | E-01(9): site-wide default Open Graph image |
| gtm-os | [#23](https://github.com/AlexYedi/gtm-os/pull/23) | G-05 | merged | 7 | yes | G-05: Re-sequence M4–M6 milestones and refresh stale planning docs (DR |
| pipeline | [#225](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/225) | unmapped | merged | 6 | yes | docs(specs): record Distribution §6 channel decision (LinkedIn, X, Hub |
| pipeline | [#226](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/226) | E-07 | merged | 10 | yes | E-07: selftests.yml — run every offline script selftest in CI |
| pipeline | [#227](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/227) | E-07 | merged | 2 | yes | E-07: scripts README — purpose, run command, selftest per script |
| pipeline | [#228](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/228) | E-07 | merged | 3 | yes | E-07: inbox_boundary selftest cases — one privacy layer per case [huma |
| hub | [#48](https://github.com/AlexYedi/empire-state-hub/pull/48) | E-02 | merged | 65 | yes | feat(E-02): hub long reads — schema, seed, and /rooms/<slug>/read |
| pipeline | [#229](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/229) | unmapped | merged | 6 | yes | YED-122: topic-intelligence health view migration (prep only, no DDL e |
| gtm-os-hub | [#17](https://github.com/AlexYedi/gtm-os-hub/pull/17) | 01 hub fixes | merged | 25 | yes | feat(cockpit): V1-assumptions health strip from MI-graph topic_intelli |
| hub | [#50](https://github.com/AlexYedi/empire-state-hub/pull/50) | E-02 | merged | 3 | yes | design(E-02): long-form reading polish on the long-read page |
| hub | [#51](https://github.com/AlexYedi/empire-state-hub/pull/51) | E-10 | merged | 3 | yes | feat(E-10): hub themes — /themes index over committed themes.json |
| gtm-os-hub | [#18](https://github.com/AlexYedi/gtm-os-hub/pull/18) | G-01 | merged | 5 | yes | feat(G-01): upgrade gtm-os-hub to Next.js 16.2.9 |
| pipeline | [#230](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/230) | E-05 | merged | 2 | yes | feat: E-05 X content contract — reference, voice sections, x checks, - |
| hub | [#52](https://github.com/AlexYedi/empire-state-hub/pull/52) | setup / onboarding | merged | 18 | yes | refactor(shared): system-map regen from live pipeline state + doc-drif |
| gtm-os-hub | [#19](https://github.com/AlexYedi/gtm-os-hub/pull/19) | G-02 | merged | 3 | yes | feat(G-02): V2 instrument panels (cockpit) + /signal latest-snapshot f |
| pipeline | [#231](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/231) | S-03 | merged | 1 | yes | S-03: reference-architecture topic layers (YED-126) |
| pipeline | [#233](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/233) | E-08 | merged | 2 | yes | E-08: payload truncation check in notion_payload.py |
| pipeline | [#234](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/234) | S-02 | merged | 2 |  | feat: S-02 feed layer, code half (YED-251) |
| pipeline | [#235](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/235) | S-04 | merged | 2 | yes | S-04: PII Phase 2 proposals — retention/TTL, regex set, DB backstop (Y |
| gtm-os-hub | [#20](https://github.com/AlexYedi/gtm-os-hub/pull/20) | G-03 | merged | 2 | yes | feat(G-03): draft D1 Commercial lesson bodies (GTM-10) |
| gtm-os-hub | [#21](https://github.com/AlexYedi/gtm-os-hub/pull/21) | G-03 | merged | 7 | yes | feat(G-03): draft D2 GTM Systems lesson bodies (GTM-10) |
| gtm-os-hub | [#22](https://github.com/AlexYedi/gtm-os-hub/pull/22) | G-03 | merged | 6 | yes | feat(G-03): draft D5 AI/Agent lesson bodies (GTM-10) |
| hub | [#53](https://github.com/AlexYedi/empire-state-hub/pull/53) | E-06 | merged | 7 | yes | feat(E-06): X surfaces on the hub — share intent links + X card metada |
| hub | [#54](https://github.com/AlexYedi/empire-state-hub/pull/54) | E-10 | merged | 14 | yes | feat(E-10): /themes "By layer" view over the S-03 topic map (YED-126) |
| hub | [#55](https://github.com/AlexYedi/empire-state-hub/pull/55) | E-04 | merged | 7 | yes | feat(E-04): public Rooms MCP server at /api/mcp |
| gtm-os | [#25](https://github.com/AlexYedi/gtm-os/pull/25) | G-04 | open |  | yes | docs: gtm G-04 public-repo truth pass — accurate visibility docs, egre |
| pipeline | [#236](https://github.com/AlexYedi/Empire_State_Events_Pipeline_Take_3/pull/236) | unmapped | merged | 11 | yes | docs(s04): reserved *.example TLD in regex test rows (follow-up to #23 |
