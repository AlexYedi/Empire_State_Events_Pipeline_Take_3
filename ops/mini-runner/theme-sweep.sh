#!/bin/zsh
# Daily theme sweep (YED-384 discovery loop, ADR-14 §2.1-2.3): the first scheduled job that runs a model.
# Called by run-job.sh `sweep` on the mini; also runnable by hand from any checkout for a dry run.
#
# Read-only by design. The only model step is the `theme-sweeper` agent with WebSearch + WebFetch and nothing else
# (invariant 5: it reads hostile web text, so it holds no write tools). This shell does every step that touches disk:
#   1. sweep_seed.py ranks today's themes (deterministic, GET-only spine reads)
#   2. the top N themes each get one `claude -p --agent theme-sweeper` run, inputs passed as JSON
#   3. sweep_manifest.py validates each raw manifest (schema, window, cap, https, PII) before anything reads it
# Output: .claude/.state/sweeps/<date>/ (gitignored). No database, Notion or HubSpot writes: the stage-market writer
# comes after migration 0022 and needs its own approval. The raw manifest is page-derived text and is never echoed
# into this log; only the validator's counts are.
set -u
PY="${PY:-.venv/bin/python}"
N="${SWEEP_THEMES:-3}"             # themes per run
CAP="${SWEEP_CAP:-15}"             # items per theme
BUDGET="${SWEEP_BUDGET_USD:-4}"    # per-theme ceiling on the list-price estimate (a guardrail, not a bill)
TODAY="${SWEEP_TODAY:-$(date +%F)}"
OUT=".claude/.state/sweeps/$TODAY"
mkdir -p "$OUT"

SEED_ARGS=(--today "$TODAY" --out "$OUT/seeds.json")
# On the mini, event inventories live in the laptop mirror (run-job.sh sets INPUTS_ROOT).
if [[ -n "${INPUTS_ROOT:-}" && -d "$INPUTS_ROOT/Event Content" ]]; then
  SEED_ARGS+=(--events-dir "$INPUTS_ROOT/Event Content" --state-dir "$INPUTS_ROOT/.claude/.state")
fi
"$PY" .claude/scripts/sweep_seed.py "${SEED_ARGS[@]}" || { echo "FAIL: sweep_seed"; exit 5; }

# One input file per theme: the top N themes in seed order (velocity, then event, then gap), all their seed rows.
"$PY" - "$OUT" "$N" "$CAP" <<'PYEOF' > "$OUT/plan.tsv" || { echo "FAIL: plan"; exit 6; }
import json, re, sys
out, n, cap = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
seeds = json.load(open(f"{out}/seeds.json"))
themes = {}
for r in seeds:
    themes.setdefault(r["theme"], []).append(r)
for theme, rows in list(themes.items())[:n]:
    slug = re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")[:60]
    w = rows[0]["window"]
    inp = {"theme": theme, "theme_id": rows[0]["theme_id"], "query_id": None, "window": w,
           "seed_queries": [{k: r[k] for k in ("kind", "query", "seed_ref")} for r in rows],
           "known_entities": [], "cap": cap}
    json.dump(inp, open(f"{out}/{slug}.input.json", "w"), indent=1)
    print("\t".join([slug, rows[0]["theme_id"] or "null", w["from"], w["to"], theme]))
PYEOF

FAILS=0; TOTAL=0
while IFS=$'\t' read -r SLUG TID FROM TO THEME; do
  echo "-- $THEME ($FROM..$TO)"
  claude -p --agent theme-sweeper --model sonnet --permission-mode dontAsk --strict-mcp-config \
    --no-session-persistence --allowedTools WebSearch WebFetch --max-budget-usd "$BUDGET" --output-format json -- \
    "Sweep this theme. Inputs as JSON; return only the manifest JSON per your contract:
$(cat "$OUT/$SLUG.input.json")" > "$OUT/$SLUG.envelope.json" 2> "$OUT/$SLUG.stderr"
  RC=$?
  # The envelope carries run metadata (subtype, turns, list-price estimate) and the final message in `result`.
  # Log only the metadata; the result is page-derived and goes to the validator, never to this log.
  "$PY" - "$OUT/$SLUG.envelope.json" "$OUT/$SLUG.raw.json" <<'PYEOF'
import json, sys
try:
    e = json.load(open(sys.argv[1]))
except Exception as x:
    print(f"   envelope unreadable ({type(x).__name__})"); open(sys.argv[2], "w").close(); sys.exit(0)
r = (e.get("result") or "").strip()
if r.startswith("```"):
    r = r.split("\n", 1)[-1].rsplit("```", 1)[0]
# The sweeper sometimes opens with a line of prose before the manifest (2026-11-13, YED-414). Hand the validator the
# first top-level JSON object that has an "items" key; if none decodes, pass the text through and let it reject.
if not r.startswith("{"):
    dec, i = json.JSONDecoder(), r.find("{")
    while i != -1:
        try:
            obj, _ = dec.raw_decode(r[i:])
            if isinstance(obj, dict) and "items" in obj:
                r = json.dumps(obj, ensure_ascii=False); print("   note: prose before the manifest was stripped"); break
        except ValueError:
            pass
        i = r.find("{", i + 1)
open(sys.argv[2], "w").write(r)
print(f"   sweeper: {e.get('subtype')} · turns {e.get('num_turns')} · est ${e.get('total_cost_usd', 0):.2f} (list price) · result {len(r)} chars")
PYEOF
  if [[ $RC -ne 0 ]]; then echo "   sweeper exit $RC (stderr kept in $OUT/$SLUG.stderr)"; FAILS=$((FAILS+1)); continue; fi
  "$PY" .claude/scripts/sweep_manifest.py validate "$OUT/$SLUG.raw.json" --window "$FROM" "$TO" \
    --theme-id "$TID" --cap "$CAP" --out "$OUT/$SLUG.valid.json" > "$OUT/$SLUG.validate.txt" 2>&1
  VRC=$?
  if [[ $VRC -eq 0 ]]; then
    K=$("$PY" -c "import json,sys; print(len(json.load(open(sys.argv[1]))['items']))" "$OUT/$SLUG.valid.json")
    TOTAL=$((TOTAL+K)); echo "   valid: $K items"; tail -3 "$OUT/$SLUG.validate.txt" | sed 's/^/   /'
  else
    echo "   validator exit $VRC (manifest rejected; see $OUT/$SLUG.validate.txt)"; FAILS=$((FAILS+1))
  fi
done < "$OUT/plan.tsv"

echo "SWEEP: $(wc -l < "$OUT/plan.tsv" | tr -d ' ') themes, $TOTAL valid items, $FAILS failed -> $OUT"
[[ $FAILS -eq 0 ]]
