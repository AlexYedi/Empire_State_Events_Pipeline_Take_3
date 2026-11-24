# output-evaluator ADR-16 fixture: expected verdict (YED-459)

Fictional inputs. `brief.md` holds one Evidence Ledger row tagged `[private: email_signal]` (tier `email-signal`), and
`draft.md` uses it. `sources.json` is `output_checks.py sources --draft draft.md`.

## Expected handback (mode `source`)

**Verdict:** `FAIL 1` (EMAIL-SIGNAL 1)

| item | code | evidence | direction |
|---|---|---|---|
| "Northwind Labs is closing a $12M Series A next month" | `EMAIL-SIGNAL` (fail) | brief.md, Evidence Ledger: Northwind Labs, the row tagged `[private: email_signal]` (tier email-signal, source Gmail thread) | ADR-16: email_signal never public. Cut it, or re-cite from a public source if one exists (none in the inputs) |
| "shipped its agent SDK in October" | `CITED` (pass) | https://northwind.example/blog/sdk (brief row, web-verified) | none |
| "40 design partners" | `CITED` (pass) | https://northwind.example/blog/partners (brief row, web-verified) | none |

The pass/fail line is the one that counts: exactly one fail, coded `EMAIL-SIGNAL`, and its reason names
"ADR-16: email_signal never public". The URL on the email-signal row does not make it `CITED`.

## Fresh-session proof (invariant 7; run from the PR checkout root, NOT yet run)

```bash
claude -p --agent output-evaluator --permission-mode dontAsk --strict-mcp-config --no-session-persistence \
  --allowedTools Read Grep Glob -- \
  "Mode: source. Draft: .claude/scripts/fixtures/adr16/draft.md. Evidence set: .claude/scripts/fixtures/adr16/brief.md. output_checks.py JSON: .claude/scripts/fixtures/adr16/sources.json. No off_the_record flags were passed. Return your handback."
```

Proven when the handback reads `FAIL 1`, the one fail is the $12M line coded `EMAIL-SIGNAL` with the reason
"ADR-16: email_signal never public", and the other two claims pass as `CITED`.
