# 02 · Pipeline tests + docs (Empire_State_Events_Pipeline_Take_3) · Tier 1, volume

Stdlib Python scripts under `.claude/scripts/`. Several already have an offline `--selftest`
(spine_client 30/30, lint_agent_tools 19/19, substrate, retrieve, comp_gate…). Copy their pattern.
**No behaviour change in any script.** Selftests only exercise existing functions. Each must run offline
with no `.env`, no network and no Notion/Supabase calls. One PR per item.

## P1 · `notion_payload.py --selftest`
This is the schema check that gates every Notion write, and it has no selftest. Read the script and add cases
covering each rejection branch it already has, plus one valid payload that prints VALID.
**Done when:** `python3 .claude/scripts/notion_payload.py --selftest` passes, with ≥1 case per rejection branch.

## P2 · `output_checks.py --selftest`
The pre-check that runs before output-evaluator. Cover each check it emits, with one passing and one failing input per check.

## P3 · `build_journal.py --selftest`
Cover parsing and generation from a small inline fixture. Must not write to the real journal files (use a temp dir).

## P4 · `recompute_relevance.py --selftest`
Cover the scoring function(s) on inline fixtures with no DB access. If scoring can't be separated from I/O without
changing behaviour, stop and say so on the plan card.

## P5 · `render_carousel.py` pure-function tests
Test only the pure checks (page-count and 4:5 aspect maths, overflow detection logic) on inline fixtures. No headless Chrome.

## P6 · CI: run every selftest on PRs
New `.github/workflows/selftests.yml`: on `pull_request` touching `.claude/scripts/**`, run
`python3 <script> --selftest` for every script that supports the flag. Stdlib only, no third-party actions beyond `actions/checkout@v4`.
Match the style of `agent-tools-lint.yml`. **Do not edit the existing workflows.**

## P7 · Scripts index
New `.claude/scripts/README.md`: one row per script with purpose (from its docstring), how to run it, and its selftest
command (or "none"). Facts only from the code.

## P8 · Guard selftest cases (tests only; human review)
Add **new test cases only** to `inbox_boundary.py`'s existing selftest. Each case tests one layer of the boundary
on its own (for example: a denylisted sender alone, a denylisted domain alone, a missing denylist file alone).
**Do not change any line outside the selftest case list.** Alex reviews this PR line by line (CLAUDE.md invariant 1).
