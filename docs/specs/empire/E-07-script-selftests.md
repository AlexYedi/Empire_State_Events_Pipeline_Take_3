# E-07 · Script selftests, index, CI (Empire)

**Repo:** Empire_State_Events_Pipeline_Take_3

## Product
Several pipeline scripts already carry an offline `--selftest` (spine_client 30/30, lint_agent_tools 19/19, plus substrate, retrieve, comp_gate and others). The ones that gate writes and public copy don't. Give every gate a selftest and run them all in CI.

## Technical (one PR each; they're independent)
1. `notion_payload.py --selftest`: ≥1 case per rejection branch, plus one valid payload that prints VALID.
2. `output_checks.py --selftest`: one passing and one failing input per check.
3. `build_journal.py --selftest`: parse and generate from an inline fixture. Write only to a temp dir.
4. `recompute_relevance.py --selftest`: the scoring functions on inline fixtures, with no DB access. If scoring can't be separated from I/O without a behaviour change, say so in the PR and stop. (S-01 depends on this.)
5. `render_carousel.py`: tests for the pure checks only (page count, 4:5 aspect maths, overflow logic). No Chrome.
6. `.github/workflows/selftests.yml`: on a PR touching `.claude/scripts/**`, run `python3 <script> --selftest` for every script that supports the flag. Stdlib only, plus `actions/checkout@v4`. Style it after `agent-tools-lint.yml`. It MUST NOT edit existing workflows.
7. `.claude/scripts/README.md`: one row per script, with purpose (from its docstring), how to run it, and its selftest command or "none". Facts only from the code.
8. New **cases only** in the `inbox_boundary.py` selftest, each testing one boundary layer alone (CLAUDE.md: test each privacy layer on its own).
   - It MUST NOT change any line outside the case list.
   - Label the PR for human review.

## Must not
Change behaviour in any script · make network calls in tests · use real emails (`*.example` only).

**Done when:** each selftest passes locally and in the new workflow.
