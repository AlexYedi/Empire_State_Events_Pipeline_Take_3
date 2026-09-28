# Cross-provider judge quorum — RETIRED 2026-09-28 (YED-231)

The two-then-three-seat quorum this file specified (Claude Sonnet + Gemini + an OpenAI shadow, scoped weighting,
per-seat trust ladder, quorum merge) was removed by YED-231. The judge is now one Sonnet reviewer that raises flags.

**Current design: `.claude/references/judge.md`.** How to run it: `.claude/skills/judge-build/SKILL.md`.

This stub stays so older records that cite this path (ADR-8, run logs, notes) still resolve. The full retired text
is in git history (`git log -- .claude/references/cross-provider-judge.md`).
