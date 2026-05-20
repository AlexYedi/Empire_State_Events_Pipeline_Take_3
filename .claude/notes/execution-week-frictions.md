# Execution-week frictions (append-only)

Window: 2026-05-15 → ~2026-06-05. Raw capture, no structure. End-of-window batch review against published count + 2026-05-14 falsification triggers.

---

- **2026-05-20** — Linear priorities (YED-29 SessionStart hook) not project-scoped — same Yedibalian-team-wide block renders in every repo, so it's not actionable at the project level. Spec for fix folded into YED-30 (per-repo `.claude/linear-project.json` + hook patch to filter by Linear Project ID). Defer until end-of-window. Also surfaced sub-issue: SessionStart `additionalContext` is invisible to user in terminal — only renders into Claude's context. If we eventually want it visible at terminal-start, hook needs to also `>&2` echo. Captured here, not actioned.

---

## 2026-05-20 — Calendar-invite-as-structured-intake (auto-trigger event research)

### The friction
Events get booked 1+ weeks out. Alex tells himself "I'll come back to it" for research/content. Reality: events accrue, return-to-it doesn't happen, and pre-event window becomes a batch review-edit-publish crunch. The "come back to it" step is the failure point.

Possible mapping to 2026-05-14 systems-analyst diagnostic: deferred review may be the gating loop on publishing rate. Test before assuming (see falsification protocol below).

### The proposed architecture (build-better, no API integration to build)

**Step 1 — Add a structured PIPELINE block to the event invite description at acceptance time:**

```
[organizer's description, pasted verbatim]

---
PIPELINE
Speakers: Name (Title, Company), Name (Title, Company)
Host: Organizing entity
Topics: keyword, keyword, keyword
URL: https://...
Intent: attend / documentary / both
```

Friction lands at the moment of acceptance (when intent is high) rather than at content time (when intent has faded). The invite itself becomes the durable record — GCal becomes the event history, no separate intake form needed.

**Step 2 — Text expander or clipboard snippet** for the template so it pastes in 1 keystroke. Tooling: Raycast snippets, macOS Text Replacements, or Wispr Flow snippet. ~5 min setup once template is locked.

**Step 3 — Scheduled `/schedule` routine:**
- Cadence: daily, ~7am
- Query Google Calendar MCP (`mcp__claude_ai_Google_Calendar__list_events`) for events in next 14 days
- Look for `PIPELINE` block in event description
- Cross-check Notion Events DB by title + date to skip already-ingested events
- For each new event with PIPELINE block:
  1. Parse fields (Speakers, Host, Topics, URL, Intent)
  2. Run `/event-deep-research` with the structured input (skip the parsing step the command currently does — fields are already structured)
  3. Write brief to Notion Events + Content Drafts in `needs_review` status
  4. Optionally chain `pre-event-content` to draft LinkedIn post + DMs in same routine pass
- Failure modes: malformed PIPELINE block → log to scratchpad, skip event. Missing GCal MCP env → graceful fallback like the Linear hook pattern.

**Step 4 — Review cadence:** Notion Content Drafts kanban becomes the daily morning ritual instead of pre-event crunch. Reviews happen over days, in small bites, with full week of runway to event.

### What it gains
- Removes "I'll come back to it" by removing the come-back step entirely
- Distributes content review across days vs. batch crunch
- Invite is the structured intake (one source of truth, not three)
- Intent filter preserved (Alex still types the fields = still chooses what's worth content)
- No new infra — uses GCal MCP that already exists + `/schedule` harness feature

### What it costs
- Template iteration + lock (~1 hour — get the fields right so they don't churn)
- Text expander setup (~5 min once template locked)
- `/schedule` routine setup (~1-2 hours including failure-mode handling)
- One real upcoming-event end-to-end test
- **Total: ~half-day**

### Open design decisions
- **Auto-run `/event-deep-research` or stage in `intake` status for manual trigger?** Auto = less friction but loses the "approve to research" gate. Stage = preserves gate but reintroduces a manual step. Default recommendation: auto, since the PIPELINE block presence IS the approval signal.
- **Chain `pre-event-content` in the same routine or wait for separate trigger?** Chaining = content drafts ready Day 1 after acceptance. Separate = lets brief settle before content gets written against it. Default recommendation: chain — that's the whole point of the design.
- **PIPELINE block format — markdown, YAML, JSON?** Markdown headers feel most natural for a calendar invite description. YAML is more parser-friendly but uglier in GCal UI. Recommendation: markdown with regex extraction (defensible against minor formatting drift).
- **What happens when invite metadata changes after research has run?** (Speaker swapped, location moved, etc.) Detect via GCal `updated` timestamp; flag in Notion for re-research vs. silent diff vs. skip. Defer this decision until real-world test surfaces the edge case.

### Falsification protocol (BEFORE building)
Per execution-focus discipline (2026-05-15 memory): friction observation alone doesn't justify breaking the window. Confirmation requires recurrence.

**Per-event tally** — every time Alex accepts an event in the next 7-10 days, log here:
- Date of acceptance
- Event date
- Did the "come back to it" pattern fire? (y/n)
- If y: what blocked the immediate content-creation alternative

Tally log:
- (none yet — starting 2026-05-20)

**Decision rule:**
- 3+ events in next 7-10 days trigger the "come back to it" pattern → confirmed signal → re-engage early to build
- <3 events trigger it → wait until 2026-06-05 end-of-window, decide with full publishing-rate data
- 0 events trigger it (publishing rate jumps without this) → don't build; the friction wasn't the gate

### Re-engagement state (when window closes or trigger fires)
This spec is build-ready. Half-day estimate assumes:
- No new architecture decisions surface during build
- Template fields lock on first iteration (use the structure above as starting point)
- Existing `/schedule` harness works for the routine (verify before committing to estimate)
- Existing `/event-deep-research` command accepts structured input (may require a small modification to skip parsing and accept pre-parsed fields)

If any of those assumptions break, estimate could expand to 1-1.5 days.

### 2026-05-20 update — execution-focus break decision

Decision: build Option B (full chain) immediately, breaking the 21-day execution-focus window on Day 5.

**Reasoning (preserved for end-of-window review):**
- Behavioral argument advanced from "speculative friction" to "named pattern with clean architectural fit": user is *already* editing the GCal invite (moves to "going to events" calendar at registration), so PIPELINE block nests inside an existing action rather than inventing new discipline.
- Mobile context-switch cost (GCal → Notion → back) makes the Tier 0 "create Notion row at acceptance" workaround non-viable; the friction it adds is the very friction we were engineering around.
- All tooling exists inside Claude subscription: `/schedule` remote routines + connected GCal + Notion MCPs. No third-party integration to build.

**Cost accepted:** 3-5 hours during execution-focus window.

**End-of-window review should answer:**
- Did the PIPELINE block discipline sustain (i.e., did Alex actually add it to invites he accepted)?
- Did the routine fire reliably and produce drafts without manual intervention?
- Did the `needs_review` queue overflow (B's primary risk), or did the distributed-review-across-days promise hold?
- Net effect on publishing rate: up, down, or flat?
