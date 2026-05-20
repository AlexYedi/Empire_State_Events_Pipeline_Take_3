# PIPELINE Block Template — Calendar-Invite-as-Structured-Intake

**Purpose:** A small structured block you paste into the description of GCal event invites you intend to write about. The `/check-new-events` slash command detects events with this block and runs the full research + content chain on them.

**Locked:** 2026-05-20.

---

## Template (paste this as the starting point — edit freely)

```
[organizer's description, pasted verbatim from Lu.ma / Partiful / Meetup / email]

---
PIPELINE
Speakers: Jane Smith (CTO, Acme Corp), John Doe (Founder, Beta Co)
Host: AI NYC Meetup
Topics: agentic systems, enterprise AI adoption, evals
URL: https://lu.ma/event-slug
Intent: attend
```

---

## Field-by-field

| Field | Required? | Format guide | Example |
|---|---|---|---|
| `Speakers` | Yes | List of `Name (Title, Company)` entries. Comma / dash / semicolon / `@` all OK. Bulleted lists OK. Just names OK if no title/company known. | `Jane Smith (CTO, Acme), John Doe — Founder at Beta` |
| `Host` | Yes | Free text — organizing entity or person | `AI NYC Meetup`, `Cohere + LangChain`, `Some Investor Group` |
| `Topics` | Yes | Comma-separated keywords, 3-5 recommended | `agentic systems, enterprise AI adoption, evals` |
| `URL` | Optional | First http(s) URL in the block | `https://lu.ma/event-slug` |
| `Intent` | Optional | `attend` / `documentary` / `both` — drives content POV. Defaults to `attend` if absent. | `attend` |

## Format is loose, not rigid

The slash command parses the block with an LLM, not regex. All of these work:

```
Speakers: Jane Smith (CTO, Acme), John Doe (Founder, Beta)        ← canonical
Speakers: Jane Smith - CTO at Acme; John Doe - founder, Beta       ← different separators
Speakers: Jane Smith @ Acme, John Doe @ Beta                        ← LinkedIn-style
Speakers:
  - Jane Smith (CTO, Acme)
  - John Doe (Founder, Beta)                                        ← bulleted
Speakers: Jane (Acme CTO), independent consultant John              ← messy but readable
Speakers: Jane Smith                                                ← just a name
```

Edit on mobile freely — the parser handles the variations.

## Block delimiter rule

The block is detected by a `---` line followed by `PIPELINE` on the next line. The block continues to the end of the description (no terminator needed). Organizers' own `---` separators elsewhere in the description are ignored (the parser specifically looks for `---` + `PIPELINE` together).

## What happens if you forget a required field?

The slash command surfaces the event as a "parse warning" at the end of the run, with the missing field named. It does NOT process the event (because research can't proceed without speakers/host/topics). Fix the PIPELINE block in the invite and re-run `/check-new-events`.

## What happens if the same event already exists in Notion?

The slash command pre-dedups against the Notion Events DB by title + date. Existing events are listed as "skipped" — no duplicate writes, no wasted research.

## Why this lives in the invite (not a form or Notion intake)

- You're already in the invite when you accept an event (you move it to "Going to Events" calendar). Friction lands at moment of high intent.
- No tool switch on mobile — GCal app stays open, you paste the block, done.
- The invite itself becomes the durable record. GCal becomes your event history.
- Distributes content review across days — `/check-new-events` processes one event at a time with continue-or-quit control.

See `.claude/notes/execution-week-frictions.md` for the full design decision record (2026-05-20).
