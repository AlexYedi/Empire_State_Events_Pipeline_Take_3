# NYC AI Demos #10 → VC-portfolio **job map** (employment pivot) + event ingest + prediction framework

## Context
Alex got a late (Jun 23) approval for **NYC AI Demos #10: VENTURE SPOTLIGHT** — curated, tonight Wed Jun 24, 6–8 PM, The Refinery at Domino, Brooklyn. Curating firms: **Thrive Capital, First Round Capital, Index Ventures, Inspired Capital, Able Partners (+ "and more")**, >$60B AUM combined. Hosts: **Kyle Bhiro (Pensar)** + **TechNYC**.

The bigger picture, in Alex's words: he is **transitioning out of the family business — employment is the ultimate goal** for this next chapter. So the confirmed VC list is more than trivia: it's a **job-target map**. The primary new deliverable is a screened board of **open, relevant NYC roles at these firms' AI portfolio companies**. The event-prediction exercise stays, but secondary.

This plan = three deliverables. **#3 (the job map) is the priority.**

---

## DELIVERABLE 3 (priority) — Relevant open roles at the VCs' NYC AI portfolio companies

### Target-role filter (locked with Alex)
- **In scope (post-sale / expansion / relationship GTM):** Account Manager, Account Director, Strategic/Enterprise Account Manager, Customer Success Manager / CSM Lead, Customer Success/Account-management leadership, **Expansion**, Renewals, **Growth**, **Founding GTM** (when expansion/relationship-oriented), Partnerships/Alliances (post-sale flavor).
- **Explicitly EXCLUDE:** pure new-business / net-new-logo sales, AE, SDR/BDR, quota-hunting closer roles.
- **Seniority:** Mid-senior IC **and** Lead. (Exclude junior; include Head/Director only where it's a player-coach lead role.)
- **Location:** **NYC onsite or hybrid.** Exclude fully-remote/other-metro.

### Sourcing approach (read-only research, runs after approval)
For each curating firm — **Thrive, First Round, Index Ventures, Inspired Capital, Able Partners** (and any "and more" firms we can identify, e.g. from the event thumbnail / luma page):
1. **Enumerate the AI portfolio** — firm portfolio pages + WebSearch/WebFetch; keep only **AI-native** companies with a **NYC HQ or office**.
2. **Pull live openings per company** — careers pages + ATS (Greenhouse / Lever / Ashby), plus job tools available in-session: **Apollo `apollo_organizations_job_postings`**, **Dice `search_jobs`**, WebSearch. Prefer the company's own ATS as source of truth.
3. **Apply the target-role filter** above; dedupe; flag companies backed by **≥2 of the named VCs** (stronger signal + warmer intro path).
4. Parallelize with one research agent per VC (general-purpose / research-analyst) to stay within tonight's window.

### Output schema (one row per open role)
`Company · Curating VC(s) · AI focus · Stage · Role title · Level (IC/Lead) · Team (CS / AM / Expansion / Growth / Founding GTM) · Location (onsite|hybrid) · Apply link · Source + date pulled · Fit note (why it suits Alex's GTM/enablement + family-business operator background)`
Grouped by VC → company. A short "warm-intro map" note: which companies overlap firms Alex could reach via the event tonight.

### Storage
Job listings go stale fast, so:
- **Live board** → `nyc-ai-portfolio-jobs.md` (this event folder; full table, regenerable). *(moved here from ~/.claude/plans/ on 2026-06-24 consolidation.)*
- **Memory** → one concise `project` note `…/memory/nyc-ai-vc-portfolio-job-search.md` capturing the **strategy + the locked target-role filter + pointer to the live board**, so the criteria persist across sessions. + MEMORY.md index line.

---

## DELIVERABLE 1 — Event-facts memory
`…/memory/nyc-ai-demos-10-venture-spotlight.md` (+ index line). Confirmed facts:
- **When:** Wed Jun 24 2026, 6:00–8:00 PM EDT. **Where:** The Refinery at Domino Offices, 300 Kent Ave, Brooklyn, NY 11249 ("Going to Events" calendar).
- **What:** 10th installment, last before summer. Startups hand-picked by **Thrive, First Round, Index Ventures, Inspired Capital, Able Partners, and more** (>$60B AUM). **Index Ventures** corroborated by the event thumbnail logo lockup. Live demos; room of founders, investors, engineers, operators.
- **Hosts:** Kyle Bhiro (Co-founder, Pensar) + TechNYC. Approval from `pensar@calendar.luma-mail.com`, Gmail thread `19ef671c90176f90`. Links: https://luma.com/nyc10 · Luma "My Ticket".

## DELIVERABLE 2 — Locked prediction framework (secondary)
Sibling file `…/memory/nyc-ai-demos-10-predictions.md` (+ index line). Vectors captured now; **predictions TBD** (research deferred per Alex — run before 6 PM if pursued, to keep pre-commitment honest). Condensed:
- **Priors (gates/weights):** AI-native · live-demoable · in a named firm's portfolio · NYC-tied · fast-growing (90-day momentum) · seed–B · founder available.
- **Layer A — VC vectors:** AI thesis · recent NYC AI investments · stage mix · portfolio momentum · organizer ties · NYC-based partners · public showcase behavior · demo-friendliness.
- **Layer B — company score:** AI-native(gate) · NYC(gate) · stage · investment recency · momentum · demo-ability · founder availability · prior showcase · multi-VC backing · host-orbit fit → **ranked top ~12–18, tiered High/Med/Long-shot**.
- **Layer C — people:** likely founders/CEOs · NYC-based partners · hosts (Kyle Bhiro/Pensar, TechNYC) · repeat scene figures · Alex's networking targets.
- **Calibration (post-event):** precision@K · recall · confidence calibration · surprises → vector tuning. Ground truth: transcript, photos, Alex's notes.

Note the two efforts reinforce each other: the **same VC-portfolio research** feeds both the job map (Deliverable 3) and the demo predictions (Deliverable 2).

---

## Decisions locked
- Lock prediction vectors now; predictive research deferred (Deliverable 2).
- Predicted-company shortlist depth: top ~12–18, tiered.
- Predictions stored in a sibling file.
- Job-target filter: post-sale/expansion GTM (AM, CSM, Founding GTM, Growth, Expansion); **exclude AE/new-business/SDR**; Lead + mid-senior IC; **NYC onsite/hybrid**.

## Verification
- Memory files + index lines exist (`grep -i "nyc ai" MEMORY.md`).
- Live job board lists only in-scope roles (spot-check: no AE/SDR titles; every role NYC onsite/hybrid; each row has a working apply link + source date + attributed VC).
- ≥2-VC-backed companies flagged; warm-intro overlaps with tonight's event noted.
