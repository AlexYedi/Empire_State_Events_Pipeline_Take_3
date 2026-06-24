# Daytona AI Builders — Post-Event Output (Jun 23, 2026)

**Generated:** 2026-06-24 via `/post-event-content`
**Notion:**
- Post-Event Brief (data store): https://app.notion.com/p/389d3699c2db81a5913addde7c33c959
- 5 Takeaways post (2 variants + carousel): https://app.notion.com/p/389d3699c2db81cc8f84d2d116712e35
- Event row: https://app.notion.com/p/386d3699c2db81859824e7410f48812a

> ⚠️ **Quote-accuracy caveat.** Recording was low-fidelity (quiet/off-mic speakers, scrambled diarization), and the night skewed to product pitches. **Slide quotes are verbatim-safe** (recovered from photos). **Spoken quotes (Mickel, Mendez, Shah) are close paraphrases — verify against memory before posting.** Recording cut off mid-Blacksmith; Anchor Browser (Nadav Magnezi) not captured.

---

## The 5 Top Takeaways (one thesis each · speaker quote · what it means going forward)

**1 — A new compute unit for agents is forming.** *(Muhammad Annas Hashmi, Daytona)*
Slide (verbatim): "Isolated. Fast. Stateful. Disposable." VMs boot too slow, containers share a kernel, functions are stateless — none fit code an agent wrote and must keep running.
→ As agents move from suggesting code to running it, *where it executes* becomes its own infra layer, billed per agent-task.

**2 — "All tests pass" means nothing when the agent wrote the test.** *(Hashmi, Daytona — the night's thesis)*
The same agent writes the code and the test meant to catch it → the green check is theater. Fix: the agent uses the real app in a sandbox and produces a video receipt of the fix.
→ Verification shifts from self-reported pass-rates to observable proof-of-behavior.

**3 — Evals are a measurement problem; don't outsource the thinking.** *(Jennifer Mickel, Datadog — most substantive talk)*
Systematize what you're measuring, then operationalize it into a signal (Adcock & Collier 2001; Wallach et al. 2025 ICML). "Don't offload the whole eval to AI — if you've handed off all the thinking, you can't trust what it measures."
→ The moat is measurement rigor, not having an LLM-judge. Most eval scores measure something — just not the thing you care about.

**4 — A single model release is now visible in the infrastructure.** *(Aayush Shah, Blacksmith)*
CI load stepped up after Claude Opus 4.5 (Dec 2025): agent-initiated CI jobs up 11x since September. "CI is the first layer that feels the exhaust of all the code your developers are generating with AI."
→ Infra telemetry is becoming a leading indicator of agent adoption. (One vendor's self-reported data — directional.)

**5 — The pilot→production gap is an integration problem, not a model problem.** *(Jeremy Mendez, Oracle)*
"Enterprise AI breaks at the interfaces" — scale, data, trust. A "simple" 3-agent example deployment was a wall of subnets, private endpoints, and governance.
→ The demo is the easy 20%. Enterprise AI is won on data plumbing, auth, and trust — not the model.

**Through-line:** in the agent era, writing the code was never the hard part. Proving what it did is.

---

## Pre → Post gap (what the research got right/wrong)
- Predicted CTO **Vedran Jukic** would anchor Daytona → it was **DevRel Muhammad Annas Hashmi**.
- Predicted a big **security/isolation debate** (Docker vs microVM, May 2026 CVE wave) → **never came up**.
- Predicted the **GitHub-encroachment** tension would dominate → **not raised on stage**.
- Predicted Datadog = DASH product tour → it was **Jennifer Mickel on eval methodology** (the best talk).
- "All tests pass means nothing" headline → **confirmed**, the sharpest argument of the night.

(Full brief — speaker resolution table, entity glossary, slide catalog, stat bank, outreach state — lives in the Notion Post-Event Brief.)
