---
name: transcript-conditioning
description: "Condition a raw single-event ASR/diarized transcript into reliable content inputs — resolve diarized 'Speaker N' labels to a known roster, normalize ASR-mangled entity names against a pre-event brief, and extract a confidence-scored verbatim quote bank. Upstream of content-correspondent Mode B. Use when post-event content is built from a manually-pasted or low-quality transcript (Otter/Zoom/phone-recording exports, walk-in events Granola didn't record) where speaker labels are unreliable and proper nouns are garbled. Triggers: 'condition this transcript', 'clean up the transcript', 'who said what', 'fix the speaker labels', or any post-event flow where transcript quality gates quote accuracy."
---

# Transcript Conditioning

## Purpose

Raw event transcripts (phone recordings, Otter/Zoom exports, walk-in audio Granola didn't capture) arrive with two defects that poison downstream content:

1. **Diarized "Speaker 1/2/N" labels split on pauses, not identity** — so the same person becomes several speakers and several people collapse into one.
2. **ASR-mangled proper nouns** — Vercel → "Purcell/Versailles", Mahan Salehi → "vahan", agentic → "genetic", MCP → "FCP", Claude Code → "quad code".

If content-correspondent consumes this raw, it misattributes quotes and prints garbled company/product names in public posts. Conditioning is the grounding step that turns a noisy transcript into trustworthy inputs BEFORE any drafting.

This is NOT the sales-call mining skill. `transcript-analysis` works N≥10 call corpora for pains/triggers/objections/battlecards. This skill is single-event, content-facing, and runs against a known roster.

## When to use

- Post-event content from a manually-pasted or low-quality transcript (content-correspondent **Mode B**).
- Granola **Mode A** where diarization is unreliable or speakers weren't enrolled.
- Any time you're about to quote a named person publicly from a transcript and the labels/proper nouns can't be trusted at face value.

Skip it when Granola's diarized transcript is already clean and the roster is small and obvious.

## Inputs

- **Raw transcript** (diarized or not).
- **The pre-event research brief** for the event (roster + known entities) — this is the ground truth the conditioning anchors to. If no brief exists, build a minimal roster from the calendar invite / attendee list first.

## Method — 4 parts

### 1. Speaker resolution (resolve by content, not by label)
Ignore the "Speaker N" numbering. For each distinct voice, resolve to a person on the roster using role/content tells: company self-references ("I work at…", "we built…"), domain vocabulary, the moderator's question-asking cadence, named products. Output a table: `raw labels seen | resolved person | tell | confidence`. Flag any voice you can't resolve rather than guessing it onto a person.

### 2. Entity normalization glossary
Build a `mangled → canonical` map anchored to the brief's known entities (companies, people, products, acronyms). Anchor every correction to a brief entity where possible — don't invent canonical forms. Maintain a separate ⚠️ **low-confidence list** for garbles too damaged to resolve safely (e.g., "Mythos in the news") — these are EXCLUDED from any quote, never guessed into one.

### 3. Quote bank (the load-bearing output)
Extract the high-value verbatim quotes per resolved speaker — the lines content will actually use. Lightly de-noise ASR artifacts (filler, doubled words) WITHOUT changing wording or meaning. Attribute each to the resolved speaker. Tag confidence:
- **HIGH** — clearly recorded, unambiguous → safe to quote verbatim.
- **MED** — substance certain, phrasing approximate → soften/paraphrase downstream, do NOT quote verbatim.
Quotes drawn from low-SNR sections (mic dropouts, crosstalk) are flagged and not promoted to verbatim.

### 4. Conditioning confidence score
State an overall confidence (%) and name the sections you down-weighted (e.g., "~88%; audience Q&A tail excluded for mic dropouts"). This is the honesty gate that tells the drafting step how hard it can lean on the material.

## Output contract (hand to content-correspondent)

A compact artifact, NOT a re-typed transcript:
1. Speaker resolution table (with confidence + tells)
2. Entity normalization glossary (+ ⚠️ excluded-garble list)
3. Quote bank (attributed, confidence-tagged, de-noised verbatim)
4. Conditioning confidence score + down-weighted sections

content-correspondent (Mode B) consumes this in place of the raw transcript: the quote bank is the verbatim-quote source, the glossary guarantees proper nouns are spelled right in public copy, the confidence score gates how aggressively to quote.

## Discipline

- **Rule 12 (CLAUDE.md):** a transcript is a PRIMARY source for what a person *said in the room* — quote freely. It is NOT a source for external firm/person *thesis* claims; those still need independent citation before public use.
- **Never guess a proper noun into a public post.** If the glossary can't resolve it confidently, cut it.
- **Never promote a MED/low-confidence line to a verbatim quote.** Paraphrase and soften, or drop.

## Status

**v1 scaffold** — method codified 2026-05-27 from the first live full-pipeline run (Scaling Enterprise AI Agents, NYC; 5-speaker panel, inline conditioning produced a 12-quote bank at ~88% confidence that fed two parallel post drafts). NOT yet wired as an automatic upstream step in `/post-event-content` or the content-correspondent Mode B entry.

**Validation rule:** skill discovery is session-frozen (see CLAUDE.md SDK constraints) — test invocation in a FRESH conversation.

**Wire-up TODO:** add a one-line "run transcript-conditioning first if labels/proper-nouns are unreliable" pointer to content-correspondent SKILL.md Mode B, and reference this skill from any `/post-event-content-manual` wrapper if that command gets built.
