---
description: "Channel-ready copy variations (email/ads/social/landing) with A/B variants + QA checklist. Use when you have a messaging brief and need the actual drafts per channel. Fans out copywriting + voice specialists from this thread."
argument-hint: "[channels + persona + offer, e.g. 'email,linkedin, CIO, data platform']"
---

# /generate-channel-copy

Turn a **messaging brief** into channel-ready copy with A/B variants + a QA checklist. Multi-agent fan-out
runs **from this parent thread** (subagents cannot spawn subagents — SDK constraint); this file is the
orchestration shape. Conforms to `.claude/references/command-orchestration-convention.md`.

## Step 1 — Intake & validate (this thread, not a subagent)
Collect and confirm:
1. **channels** (required) — comma-separated from `email | ads | social | landing | sms | in-app`. Parse the
   list; validate each against that set (reject/ask on an unknown channel). If missing, ask.
2. **persona** (required) — audience/persona. If missing, ask.
3. **offer** (required) — product/feature/value prop. If missing, ask.
4. **messaging brief** (strongly preferred) — the `/create-messaging-brief` output (pillars + hook bank +
   CTAs). Keep it as a `VERBATIM SOURCE` block. **If absent, offer to run `/create-messaging-brief` first**
   — copy without a brief drifts off-positioning.
5. **tone** / **length** (optional) — tone descriptor; length constraint (short/medium/long or char count).

## Step 2 — Fan-out (this thread, parallel `Agent` calls in one message — one dispatch per channel)
For **each** requested channel, dispatch **conversion-copywriter** in parallel, leading with the verbatim
brief + persona + offer + channel-specific constraints (e.g. email subject+preview+body; ads = headline+
primary text; landing = hero+subhead+CTA). Each returns: hook, body, primary/secondary CTA, and **2 A/B
variants** anchored to *different* angles (not reworded). Compose `alex:copy-frameworks`.
Wait for all channels. If one is thin, re-invoke just that channel.

## Step 3 — Voice + QA pass (serial, this thread)
Dispatch **voice-editor** (synthesis-only) over all drafts for tone/compliance (`alex:voice-guidelines`).
Then build the **QA checklist** with **concrete, checkable pass/fail items per channel** (an unchecked item
is a blocker to "ready", not decoration):
- **email** — subject ≤ 60 chars; preview ≤ 100 chars; every personalization token (`{first_name}`, etc.)
  defined + has a fallback; one primary CTA present; unsubscribe/compliance line present.
- **ads** — headline ≤ 30 chars; primary text ≤ 90 chars (platform limit); no unsupported claim; CTA verb present.
- **social** — within platform char cap (LinkedIn ~3000, X 280); hook in first line; no more than the platform's
  link/hashtag norms; alt-text noted for any image.
- **landing** — hero + subhead + single primary CTA present; reading level ≤ grade 8; all links resolve.
- **sms / in-app** — ≤ 160 chars (SMS) / fits the component; one CTA; opt-out (SMS) present.
Cross-channel: A/B variants are angle-distinct (not reworded); no fabricated proof/metric ships.

## Step 4 — Output destination (NAME IT)
- **`conversation`** (default) — a copy table: `channel | hook | body | CTA | A/B variant | notes`, plus the
  QA checklist.
- Offer a Notion write (Content Drafts) as an explicit follow-up — parent-thread MCP only. This command does
  not publish to any channel (publishing is a judgment-gated, outward-facing step Alex owns).

## Failure modes
- **No messaging brief** — offer `/create-messaging-brief` first; if Alex proceeds anyway, derive a minimal
  inline brief from persona+offer and flag that positioning is unverified.
- **Unknown channel** — reject it and ask; don't silently drop or guess.
- **A channel returns thin** — re-invoke just that channel; note the gap.

## Ground-truth references
- `.claude/references/command-orchestration-convention.md` — the required skeleton
- Upstream: `/create-messaging-brief`. Downstream: `/test-and-report` (experiment plan for the variants)
- Agents: `conversion-copywriter`, `voice-editor`
- Skills: `alex:copy-frameworks`, `alex:voice-guidelines`
