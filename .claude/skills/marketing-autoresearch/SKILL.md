---
name: marketing-autoresearch
description: Run Karpathy-style autoresearch optimization on any content. Generates 50+ variants, scores with a 5-expert simulated panel, evolves winners through multiple rounds, outputs optimized version + full experiment log. Use when optimizing landing pages, email sequences, ad copy, headlines, form pages, CTA text, or any conversion-focused content. Triggers on "optimize this page", "run autoresearch", "score these variants", "A/B test this copy". In the Empire State pipeline, used as Step 5 of pre-event-content to push LinkedIn posts from "good draft" to "best draft" before posting.
---

# Autoresearch Skill

Karpathy-style optimization loops for any conversion-focused content. No traffic needed. Simulated expert panel. Minutes, not weeks.

**When to use this:** Pre-launch content optimization. Generate 50+ variants, score with 5 simulated experts, evolve winners, output the best version + full experiment log.

**When NOT to use this:** Post-launch real-traffic A/B testing — that requires real analytics, not simulated scoring.

> The sequence: Run autoresearch FIRST to hit 80+ simulated score. Then deploy. Then validate with real engagement.

---

## Empire State pipeline usage rules

This skill is invoked as **Step 5 of `pre-event-content`**. Specific guardrails for that context:

- **Run on:** the per-event LinkedIn post (always), the Upcoming Week post (always), the synthesis post when invoked from `pattern-synthesis` (optional).
- **Do NOT run on:** speaker/host DMs, prepared questions. Over-optimized DMs read as marketing copy and break the Level 3 personalization in `outreach-templates.md`. Prepared questions are private notes — no audience scoring applies.
- **Score threshold:** default 80. Stop at 3 rounds even if below.
- **Replace persona #5** (CEO/founder voice) with **Alex's documentarian voice**: enterprise B2B GTM, NYC AI scene, "field correspondent not networker," substantive over performative. Pull tone signals from `.claude/references/content-style-guide.md` and anti-patterns from `.claude/references/content-anti-patterns.md`.

---

## What You'll Produce

Every run outputs 3 files:

| File | Purpose |
|------|---------|
| `{name}-optimized.{ext}` | The winning optimized content |
| `data/{name}-experiments.json` | Full experiment log — all variants + all scores |
| `data/{name}-optimization-report.md` | Human-readable summary with winner rationale |

For Empire State runs, write outputs to `content-drafts/<event>/autoresearch/` and reference the winner from the Notion Content Drafts page body.

---

## Expert Panel (5 Personas)

Score every variant against all 5. Batch all variants into a single API call per round.

| # | Persona | Scoring Lens |
|---|---------|--------------|
| 1 | CMO at a mid-market B2B company (50M+ revenue) | "Would this make me stop and engage?" |
| 2 | Skeptical founder | "Do I believe this? Would I trust this person?" |
| 3 | Conversion rate optimizer | "Is this clear, specific, and action-driving?" |
| 4 | Senior copywriter | "Is this compelling, differentiated, and well-crafted?" |
| 5 | Alex's documentarian voice (Empire State default) | "Substantive over performative. Specific, not generic. Would I actually post this?" |

Each judge scores 0–100. Final score = average across all 5 judges.

---

## Round Structure (Per Content Element)

**Round 1:**
- Generate 10 variants of the element
- Batch-score all 10 with the 5-expert panel (1 API call)
- Rank by average score
- Keep top 3

**Round 2 (Evolution):**
- Analyze what the top 3 did right
- Generate 10 new variants that push those winning patterns further
- Batch-score all 10 (1 API call)
- Keep top 3

**Round 3 (If score < threshold):**
- Identify weakest scoring dimension
- Generate 10 variants optimized for that dimension
- Batch-score → keep top 1

**Multi-element cross-breeding:**
- Take top 1 winner from each element
- Generate 5 combinations that mix winning elements
- Score holistically as complete units
- Output the single best combination

**Stop condition:** Top variant hits minimum score threshold (default: 80) OR 3 rounds complete.

---

## Content Types & Score Dimensions

### LinkedIn Posts (Empire State default for pre-event)
Elements to optimize: Hook (first 2 lines), Insight line, CTA
Score dimensions:
- `scroll_stop` — Does the hook earn the click on "see more"?
- `expert_pause` — Does the insight make a domain expert pause?
- `specificity` — Concrete details vs. vague claims (no "exciting," "transformative," etc.)
- `voice_fit` — Sounds like Alex (per style guide), not LinkedIn marketing-speak
- `would_engage` — Would the judge comment, share, or DM about it?

### Email Sequences / Ad Copy / Landing Pages / Form Pages
See appendix below for original generic dimensions. These are not the typical Empire State use case.

---

## Step-by-Step Execution Protocol

### Step 1: Intake & Parse

Read the source content. Identify content type automatically or confirm with user.

For Empire State pre-event runs: content type is always `linkedin_post`. The source is the approved variant from Step 3 (per-event post) or Step 2 (Upcoming Week post) of `pre-event-content`.

Extract optimizable elements. List them back:

```
Found 3 elements to optimize for LinkedIn post:
1. Hook (lines 1-2): "[current hook]"
2. Insight line: "[current insight]"
3. CTA: "[current CTA]"

Optimizing: all | Variants per round: 10 | Min score: 80 | Persona #5: Alex documentarian
```

### Step 2: Get API Key

Check for Anthropic API key: `$ANTHROPIC_API_KEY` environment variable.

```
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 3: Run Optimization Rounds

For each element, run the round structure above.

**Critical API efficiency rule:** ALWAYS batch all variants into a single prompt. Never call the API once per variant. A round with 10 variants = 1 API call.

Model preference (in order):
- `claude-sonnet-4-6` (preferred — fast + smart)
- `claude-opus-4-7` (if highest quality needed)
- Any claude-4+ model if the above aren't available

### Step 4: Cross-Breed (Multi-Element)

After all elements have winners:
- Assemble the top winner from each element into a complete unit
- Generate 5 holistic variants that naturally combine the winning elements
- Score the complete units (not just individual parts)
- Pick the winner with the highest holistic score

### Step 5: Write Output Files

```bash
mkdir -p data
# Write optimized content
# Write experiments JSON
# Write optimization report
```

Experiments JSON structure:

```json
{
  "run_id": "autoresearch-{name}-{timestamp}",
  "content_type": "linkedin_post",
  "source_file": "path/to/original",
  "min_score_threshold": 80,
  "rounds": [
    {
      "round": 1,
      "element": "hook",
      "variants": [
        {
          "id": 1,
          "text": "...",
          "scores": {
            "cmo": 72,
            "skeptical_founder": 68,
            "cro": 75,
            "copywriter": 70,
            "alex_voice": 65
          },
          "avg_score": 70
        }
      ],
      "top_3": [1, 4, 7],
      "winner_score": 82
    }
  ],
  "final_winner": {
    "hook": "...",
    "insight": "...",
    "cta": "...",
    "holistic_score": 87
  }
}
```

### Step 6: Report Back

Summarize results to user:
- Final winning score
- Biggest score jump (which element improved most)
- Top 2 runner-up alternatives (in case winner doesn't feel right)
- Path to all 3 output files
- Clear next step (in Empire State pipeline: paste winner into Notion Content Drafts page body, set Status to `needs_review`)

---

## User Options

| Option | Default | Description |
|--------|---------|-------------|
| `elements` | all | Which elements to optimize |
| `variants_per_round` | 10 | How many variants to generate per round |
| `min_score` | 80 | Stop when this score is hit |
| `rounds` | 3 | Max rounds before stopping |
| `auto_apply` | false | Whether to overwrite the source file with winners |
| `content_type` | auto-detect | Force a content type if auto-detect is wrong |

---

## Quality Gates

- **< 70:** Don't ship. Something fundamental is broken (probably the source draft, not the variants — go back to Step 3 of pre-event-content).
- **70-79:** Marginal. One more round targeting the lowest-scoring dimension.
- **80-84:** Good. Shippable. Validate with real engagement.
- **85-89:** Strong. Ship with confidence.
- **90+:** Rare. Ship immediately.

---

## Anti-Patterns to Avoid

- Never call the API once per variant. Always batch. A 10-variant round = 1 call.
- Don't over-optimize for one dimension. If you're hitting 95 on `scroll_stop` but 45 on `voice_fit`, the post will sound like clickbait — final score is misleading.
- Don't run more than 5 rounds. If you're not hitting 80 after 3 rounds, the problem is strategic (wrong angle, weak insight), not tactical (wrong words). Go back to the source brief.
- Don't cross-breed until each element has its own winner. Premature cross-breeding creates incoherent combinations.
- **Empire State specific:** Never run on DMs or prepared questions. See pipeline usage rules at top.

---

## Appendix: Generic content dimensions (non-Empire-State use)

### Landing Pages
Elements: Hero headline, subheadline, CTA text, problem section, social proof
Dimensions: `first_impression`, `clarity`, `trust`, `urgency`, `would_convert`

### Email Sequences
Elements: Subject line, opening line, body copy, CTA, PS line
Dimensions: `would_open`, `would_read`, `would_click`, `would_reply`, `spam_risk` (lower = better, invert for final)

### Ad Copy
Elements: Headline, description, CTA
Dimensions: `scroll_stopping`, `clarity`, `click_worthiness`, `relevance`, `differentiation`

### Form Pages
Elements: Headline, subtext, value prop bullets, button text, field order, thank-you copy
Dimensions: `first_impression`, `trust`, `completion_likelihood`, `lead_quality`, `would_fill_out`
