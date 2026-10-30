# E-08 · Payload truncation check (Empire)

**Repo:** Empire_State_Events_Pipeline_Take_3

## Product
The 10/18 batch wrote Topic "Current Events" values cut off mid-word (for example "AI Sales Coaches", "Accelerator Ecosystem" and "AI for VC Workflows") because a length cut was applied upstream. Catch this before any Notion write.

## Technical
- In `.claude/scripts/notion_payload.py`, add a check that **flags** a text property value ending mid-word after a length cut. It exits non-zero with a message naming the page key, the property, and the last 40 characters.
- **The rule MUST be stated precisely in the code and the PR.** For example: the value's length is ≥ the known cut length, its last character is alphanumeric, and it has no terminal punctuation. Measure the false-positive rate against the existing payload fixtures and report it.
- Add selftest cases: a truncated value fails; a complete value at the same length that ends in punctuation passes.
- It MUST NOT change the output for any payload that passes today, apart from the new flag.

**Done when:** the selftest covers the rule, and the PR states the rule and its false-positive risk.
Depends on E-07 item 1 (the base selftest); build them in the same branch if they run together.
