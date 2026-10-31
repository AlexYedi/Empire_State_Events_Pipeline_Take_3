# Interview-Prep Dossier — Fixture (SYNTHETIC)

> **Synthetic fixture (YED-257, E-09).** "Northwind Analytics", every person, every client name and
> every number here are fictional. This file demonstrates the seven commercial-depth fields and the
> Likely Rounds and Questions section; it is the input the field-presence test parses. It contains no
> real private material — the private dossier inputs are read by path at run time only and never
> appear in fixtures.

**Axes (synthetic):** Company: Northwind Analytics · Role: Enterprise AE, AI Platform (JD pasted
verbatim in a real run) · Stage: `hiring_manager` · Interviewer: Dana Whitfield, VP Revenue.

---

## 3. Company Context (excerpt — commercial-depth fields)

### Commercial-depth fields

- **Growth stage + headcount band:** Series B, ~18 months post-raise; 140–160 employees on the company
  page, of which roughly 30 sit in GTM. The org is at the "first real sales leadership layer" point on
  the curve — big enough that process exists, small enough that the first AE hires still shape it.
- **GTM motion:** Sales-led with a partner assist. Evidence: every AE posting names a BDR pod and
  "co-sell with channel partners"; the pricing page gates everything behind "talk to sales"; two of the
  last four press items are partner announcements.
- **GTM-engineering function:** Exists in part. A two-person "Revenue Systems" team owns the
  CRM-to-product seam (posted role says "partner with Revenue Systems on attribution"); there is no
  dedicated GTM-engineering lead — the seam is owned, not engineered.
- **CRM of record + named stack:** Salesforce as CRM of record (the posting requires "deep Salesforce
  fluency"). Named stack from research: Outreach (sequences), Gong (call capture), a dbt-fed warehouse
  the RevOps team queries directly. From job postings and employee profiles, not guesswork.
- **Leadership metric:** New ARR bookings this quarter. The CEO's last public earnings-style update
  leads with it twice; the VP Revenue's LinkedIn activity ties every hire back to it.
- **Leadership AI posture:** Buying, with building signals. They purchased an AI call-review tool last
  quarter (receipt: the tool's own customer announcement) and have two open "AI workflow" roles —
  building, but around bought tools rather than in-house models.
- **Comp band:** Best-evidence range **$170K–$210K OTE**, sourced from Northwind's own Enterprise AE
  posting on its careers board (retrieved this week; the only first-party source). Evaluated against
  the comp gate (the one executable copy of the rules — not restated here):
  `comp_gate.py --text "$170K – $210K OTE" --floor 150000` →
  `{"verdict": "PASS", "figure": 190000, "rules": [...], "note": "..."}` — the floor shown is a
  synthetic placeholder; in a real run it comes from the private model file read at run time.
  - **Honest gap (format demonstrated):** *No verified range exists for this exact level at this
    company — closest evidence is the adjacent AE II posting on the same board; treat as directional
    and confirm in the recruiter screen rather than padding with a guess.*

### Client-name hygiene (E-09 addition 2)

Outcomes in this dossier are described unnamed ("a Fortune-500 logistics enterprise", "a top-5 US
healthcare carrier"). Client names appear only in the logo line:

**Key accounts:** Meridian Freight · Beacon Health · Cobalt Bank *(fictional logo line)*

## 8. Likely Rounds and Questions

Predicted rounds for a `hiring_manager` stage at a Series B sales org (derived from the decoded role
and the interviewer profile — every question below traces to one of the two; none is templated):

- **Round: hiring manager (Dana Whitfield, VP Revenue).** This stage actually tests whether the
  numbers held and whether Alex diagnoses before building.
  - Likely question 1: "Walk me through the largest deal you closed last year — what was your
    specific role vs. your team's?" *(derived from the interviewer profile: Dana is a former operator
    who publicly stresses attribution honesty)*
  - Likely question 2: "What was your quota, your attainment, and your pipeline coverage going into
    the year?" *(volume follow-up; derived from the decoded role: quota-carrying post-sales is the
    core of the job)*
  - Likely question 3: "Second follow-up — of that number, how much was expansion vs. new logo?"
    *(third-level volume follow-up; decoded role names account growth as the success metric)*
  - Likely question 4: "Salesforce adoption here is mediocre — what would you do in your first 90
    days?" *(decoded role: the AE owns pipeline hygiene; interviewer profile: Dana built RevOps)*
  - What a strong answer must establish: volumes offered unprompted, attribution owned honestly, and
    a diagnose-before-build instinct on the 90-day question.
- **Predicted next round (for orientation):** a panel with Revenue Systems + a portfolio review —
  derived from the org map: Revenue Systems co-owns the CRM-to-product seam this role feeds.

---

*Fixture only. In a real run the dossier carries the full 12 sections and writes to Notion
`needs_review` for comment review.*
