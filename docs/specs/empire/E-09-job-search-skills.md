# E-09 · Job-search skills batch (Empire)

**Linear:** YED-257 · YED-256 · YED-258 (YED-151 is its duplicate) · YED-220 · **Repo:** Empire_State_Events_Pipeline_Take_3

**Private-input rule for this whole spec:** `me-model.md` and `target-companies.md` are gitignored and are **not in the sandbox**.
- Every skill here MUST read them by path at run time and MUST be built and tested against **synthetic fixtures** in `.claude/skills/<skill>/fixtures/`.
- Fixture people and companies are fictional.

## Executables
1. **YED-257 · Interview-prep dossier fields.**
   - Add these fields to `.claude/skills/interview-prep-dossier/`:
     - growth stage and headcount band;
     - GTM motion (PLG / sales-led / partner);
     - whether a GTM-engineering function exists;
     - CRM of record and named stack;
     - the metric leadership cares about;
     - leadership's AI posture;
     - comp band.
   - Also add a "Likely rounds and questions" section.
   - Exit: a fixture dossier renders every new field.
2. **YED-256 · Mock-interviewer skill.**
   - A new skill, `.claude/skills/mock-interviewer/`.
   - Round types: frustrated rep (discovery), hiring manager (behavioural, with second and third follow-ups that ask for volumes), portfolio skeptic, take-home panel, commercial rounds (discovery call, book review, QBR, renewal save).
   - It probes the failure path harder than the happy path, and it scores against 7 dimensions: commercial bias, diagnose before build, failure paths, adoption and handoff, experimentation, honest AI scoping, communication across levels.
   - Output: a debrief described as a Notion `needs_review` draft. The skill MUST NOT call Notion write tools itself.
   - Exit: 3 fixture rounds documented end to end.
3. **YED-258 · /tailor-resume.**
   - A skill + command producing one page: HTML → headless Chrome → text-based, ATS-safe PDF. It has a general mode and a posting-tailored mode.
   - Rules from Alex:
     - quota-carrying post-sales is always the lead;
     - client names appear only as a "Key accounts" logo line;
     - proof links (repos, hub) are verified live;
     - nothing is invented beyond me-model.
   - Build against a synthetic me-model fixture.
   - Exit: the fixture renders to one page, and `pdftotext` output keeps reading order.
4. **YED-220 · Five patterns from the Eric harvest.**
   - The source note is `docs/archive/notes/eric-coldoutboundskills-harvest-2026-09-24.md`.
   - Implement:
     1. fact-before-prose with abstain-empty, in `outreach-templates.md` and `pre-event-content`;
     2. the phrase gate plus a posting-liveness check (URL, posted date, live) in `.claude/skills/role-radar/` Step 3, with tests in its scripts;
     3. a positive-reply taxonomy with its null baseline;
     4. single-variable tagging across the 3 post variants;
     5. approval-loop tuning (a sample of 1 → 10 → lock).
   - One PR per pattern.

## Must not
Read or commit real private files · weaken any role-radar comp-gate rule (`comp_gate.py` is the one executable copy of the comp rules).

## Session-side
YED-152 (the dossier reads the real Target-Role ICP) runs in the Claude Code session against the local me-model.
