# Frontier Build NYC 2: Obvious spec pack (Fri 10/30)

Paste each spec into its repo's Obvious project as a document, then start one initiative per spec.
Sources: Notion Specs & Ideas (35 open rows), the To-dos DB (~50 open), and a read of both codebases on 10/30.

## The complexity ladder (what the day measures)

The question isn't only "how many PRs." It's how complex a build the factory can take before it needs you.
Each tier is a harder test. Start them in this order, so the easy volume lands while the hard ones run.

| # | Spec | Repo | Tier | Items | What it tests |
|---|---|---|---|---|---|
| 0 | `00-track-a-rules-test.md` | pipeline | Probe | 2 runs | Does it read CLAUDE.md without AGENTS.md? |
| 1 | `01-hub-small-fixes.md` | hub | T1 Volume | 9 | Parallel throughput on independent, small, verifiable PRs |
| 2 | `02-pipeline-tests-and-docs.md` | pipeline | T1 Volume | 8 | Python test-writing against real code, with no behaviour change |
| 3 | `03-mid-builds.md` | both | T2 Backlog | 3 | Real roadmap items: multi-file, judgment inside a contract |
| 4 | `04-hub-long-reads.md` | hub | T3 Feature | 4–5 | A full Product/UX/Technical spec decomposed into a UI feature (design systems) |
| 5 | `05-rooms-mcp-server.md` | hub | T4 Stretch | 3–4 | Roadmap build B4: a new protocol surface, an external SDK, plus tests |

About 30 executables in total. Your baseline is ~6–7 merged PRs on an ordinary active day.

## Kickoff order (first hour)
1. Install gate: selected repos only, `requireHumanMerge` ON, screenshot the permission screen.
2. Start 01 and 02 (volume) immediately.
3. Run 00 (Track A, both runs), with a hard stop at 11:30.
4. Start 03 and 04 at about 11:30, and 05 once 04's plan card is approved.

## Rules for every spec (paste the block below at the top of each one)

```
Constraints for this initiative:
- One PR per item. Small diffs. Each PR states what it changed and how it was verified.
- Do not touch: .env*, .claude/hooks/, .claude/settings*.json, the guard logic in spine_client.py,
  inbox_boundary.py or verify-public-safe.mjs (tests that call them are fine), git history.
- Never add secrets, tokens or API keys. Nothing here needs one.
- Run the repo's checks before opening a PR (hub: `pnpm check && pnpm lint && pnpm build`;
  pipeline: the script's `--selftest`).
- If a requirement is ambiguous, stop and ask on the plan card. Don't guess.
```

## Deliberately excluded (and why)
- **spine_client fails closed when the denylist is missing** (open to-do): a guard-logic change on the PII boundary. CLAUDE.md invariant 1 requires human review. Do it with Claude Code next week, not with an unfamiliar agent.
- **Keychain secret loading** (open to-do): secrets-adjacent. It also needs the Mac mini.
- **B1/B2/B3/B5 builds**: these need API keys (Clay, AI Gateway, OpenAI, ElevenLabs). No keys go into the Obvious workspace.
- Anything that writes to Notion, HubSpot or Supabase.
