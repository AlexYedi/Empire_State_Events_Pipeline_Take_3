# YED-304 W2 — fixed-taxonomy baseline validation (leave-one-out)

Generated 2026-11-03T21:10:18Z by `supabase/scripts/topic_cluster_assign.py --validate` (offline, fixture-backed; no database writes).

## What this measures — read first

- **This is the fixed-taxonomy BASELINE study.** Production clustering is on hold pending the dynamic-taxonomy design review (PR #264); any new design must beat these numbers.
- **Agreement, not accuracy:** all 170 curated assignments are `cluster_assigned_by='llm'` (the original bootstrap). This study measures agreement with the LLM bootstrap taxonomy, **not** hand-labelled ground truth.
- **Name-only embeddings:** the fixture is name-only by design (most backlog topics have no description); name+description results would overstate backlog performance.
- **attended_linked is a snapshot** that changes after the W4 data fixes; the fixture is regenerated before any backfill dry-run. Not treated as stable here.
- **Backlog:** the fixture's 102 unassigned rows include 8 merge tombstones (`metadata ? 'merged_into'`) that are not identifiable in the name-only fixture; the real backlog is **94**. Twin-backed runs exclude them explicitly.

## Method

- Embeddings: `BAAI/bge-small-en-v1.5` (384-d, the pin from `.claude/scripts/dockb_common.py`), local ONNX inference via fastembed, cosine similarity, deterministic.
- **Leave-one-out over all 170 curated assignments:** each topic is assigned blind with kNN over the other 169; vote per cluster weighted by similarity; confidence = winning cluster's vote share × top-1 similarity.
- k swept over [1, 3, 5, 7] (clusters are small — 2–10 topics, 8 of 30 with ≤3 members — so k=7 alone would be biased toward large clusters) and the confidence threshold over [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9].
- Ship rule (PR #264 review): the lowest threshold where precision ≥ 0.90 AND the Wilson 95% lower bound beats both baselines; across k, highest coverage wins.
- Baselines over the same trial set: (a) always-largest-cluster (LOO form); (b) size-weighted-random, mean over 1000 seeded repetitions.

## Data

- Fixture: `supabase/fixtures/yed304_topic_clusters.json` (generated 2026-11-03 20:48:31.89821+00; source: The-Prod-Brain public.topic + topic_intelligence.topic_cluster, read-only export (YED-304). Name-only by design: no descriptions.)
- Topics: **272** · assigned (LLM bootstrap): **170** · clusters: **30** · unassigned: **102** (8 tombstones → real backlog 94)

## Sweep results — precision / Wilson 95% lower bound / coverage

| k | threshold | auto-n | precision | wilson95_lo | coverage | qualifies |
|---|---|---|---|---|---|---|
| 1 | 0.50 | 170 | 0.482 | 0.408 | 1.000 |  |
| 1 | 0.55 | 170 | 0.482 | 0.408 | 1.000 |  |
| 1 | 0.60 | 170 | 0.482 | 0.408 | 1.000 |  |
| 1 | 0.65 | 168 | 0.482 | 0.408 | 0.988 |  |
| 1 | 0.70 | 165 | 0.485 | 0.410 | 0.971 |  |
| 1 | 0.75 | 155 | 0.497 | 0.419 | 0.912 |  |
| 1 | 0.80 | 118 | 0.517 | 0.428 | 0.694 |  |
| 1 | 0.85 | 53 | 0.585 | 0.451 | 0.312 |  |
| 1 | 0.90 | 21 | 0.762 | 0.549 | 0.124 |  |
| 3 | 0.50 | 88 | 0.682 | 0.579 | 0.518 |  |
| 3 | 0.55 | 61 | 0.738 | 0.616 | 0.359 |  |
| 3 | 0.60 | 40 | 0.800 | 0.652 | 0.235 |  |
| 3 | 0.65 | 29 | 0.793 | 0.616 | 0.171 |  |
| 3 | 0.70 | 26 | 0.769 | 0.579 | 0.153 |  |
| 3 | 0.75 | 24 | 0.792 | 0.595 | 0.141 |  |
| 3 | 0.80 | 22 | 0.773 | 0.566 | 0.129 |  |
| 3 | 0.85 | 10 | 0.900 | 0.596 | 0.059 | ✅ |
| 3 | 0.90 | 5 | 1.000 | 0.566 | 0.029 | ✅ |
| 5 | 0.50 | 36 | 0.833 | 0.681 | 0.212 |  |
| 5 | 0.55 | 24 | 0.875 | 0.690 | 0.141 |  |
| 5 | 0.60 | 20 | 0.850 | 0.640 | 0.118 |  |
| 5 | 0.65 | 19 | 0.842 | 0.624 | 0.112 |  |
| 5 | 0.70 | 16 | 0.812 | 0.570 | 0.094 |  |
| 5 | 0.75 | 11 | 0.818 | 0.523 | 0.065 |  |
| 5 | 0.80 | 8 | 0.750 | 0.409 | 0.047 |  |
| 5 | 0.85 | 1 | 1.000 | 0.207 | 0.006 | ✅ |
| 5 | 0.90 | 1 | 1.000 | 0.207 | 0.006 | ✅ |
| 7 | 0.50 | 22 | 0.864 | 0.667 | 0.129 |  |
| 7 | 0.55 | 16 | 0.875 | 0.640 | 0.094 |  |
| 7 | 0.60 | 12 | 0.833 | 0.552 | 0.071 |  |
| 7 | 0.65 | 10 | 0.900 | 0.596 | 0.059 | ✅ |
| 7 | 0.70 | 8 | 0.875 | 0.529 | 0.047 |  |
| 7 | 0.75 | 4 | 1.000 | 0.510 | 0.024 | ✅ |
| 7 | 0.80 | 2 | 1.000 | 0.342 | 0.012 | ✅ |
| 7 | 0.85 | 0 | n/a | 0.000 | 0.000 |  |
| 7 | 0.90 | 0 | n/a | 0.000 | 0.000 |  |

## Baselines (same trial set, coverage 1.0)

- (a) Always-largest-cluster (LOO form): **0.059**
- (b) Size-weighted-random (LOO form): mean **0.033** over 1000 seeded reps
- Baseline floor for the ship rule: **0.059**

## Verdict

**PASS** — ship point: **k=3, threshold=0.85** · precision 0.900 (9/10) · Wilson 95% lower bound 0.596 > baseline floor 0.059 · coverage 0.059 (10/170 auto-assigned, 160 to review).

The gate clears for the fixed taxonomy. This number is the bar any dynamic-taxonomy design must beat. The backfill dry-run remains a separate task and the nightly write stays behind the W1 allowlist + design review.

## Twin read-path probe (live, 2026-11-03T21:12Z)

`topic_cluster_assign.py --check-twin` over the session pooler (`aws-1-us-east-2.pooler.supabase.com`, user `postgres.ytfzzsxcxxbejnowmkmk`), read-only:

- `public.topic`: 188 rows; columns id, name, description, created_at, metadata — **no cluster columns** (the pre-W1 table the LLM bootstrap wrote around; tombstone metadata lives here).
- `canonical_v2.topic`: 185 rows; columns include id, name, description, cluster_id, cluster_assigned_by, cluster_assignment_confidence, metadata, created_at — **the live cluster-state table**; assigned rows: 170 (matches the fixture); merge tombstones in canonical_v2: 0 (tombstones are a public.topic artifact).
- `topic_event_links`: 243 rows; 170 attended-linked topic ids.
- Prod (`oicikjyzmxqfomrrqkvf`) is unreachable by construction: the connection guard refuses any non-twin host; no prod credential is configured.

## Per-topic results (leave-one-out)

Auto column uses the ship-point threshold 0.85

| topic | true cluster | predicted cluster | top-1 sim | confidence | auto | correct |
|---|---|---|---|---|---|---|
| AI Coding Agent Infrastructure | Coding Agents | Coding Agents | 0.959 | 0.959 | yes | ✅ |
| AI Coding Agents | Coding Agents | Coding Agents | 0.959 | 0.959 | yes | ✅ |
| Enterprise Deployment of AI Coding Agents (Claude Code at org scale) | Coding Agents | Coding Agents | 0.922 | 0.922 | yes | ✅ |
| Real-Time Voice AI Infrastructure | Voice AI Infrastructure | Voice AI Infrastructure | 0.900 | 0.900 | yes | ✅ |
| Voice AI Infrastructure & Ultra-Low-Latency RTC | Voice AI Infrastructure | Voice AI Infrastructure | 0.900 | 0.900 | yes | ✅ |
| AI Harnesses & Agent Hooks for Codebases | Coding Agents | Coding Agents | 0.899 | 0.899 | yes | ✅ |
| Voice as the Default Human-AI Interface | Voice AI Infrastructure | Voice AI Infrastructure | 0.882 | 0.882 | yes | ✅ |
| Real-Time Voice Agent Orchestration | Voice AI Infrastructure | Voice AI Infrastructure | 0.882 | 0.882 | yes | ✅ |
| AI-Ready Data | Data Foundations for AI | Data Foundations for AI | 0.865 | 0.865 | yes | ✅ |
| AI-Era API Security | AI & Agent Security & Governance | AI & Agent Security & Governance | 0.830 | 0.830 | no | ✅ |
| Trust, Fraud, Authorization & Liability when the Buyer is an Agent | Agentic Commerce & Payments | Agentic Commerce & Payments | 0.825 | 0.825 | no | ✅ |
| Open-Source Infrastructure for Quantum Networking | Quantum Computing & HPC | Quantum Computing & HPC | 0.823 | 0.823 | no | ✅ |
| Quantum Networking Protocol Stack | Quantum Computing & HPC | Quantum Computing & HPC | 0.823 | 0.823 | no | ✅ |
| Quantum Key Distribution (QKD) & Post-Quantum Cryptography (PQC) | Quantum Computing & HPC | Quantum Computing & HPC | 0.821 | 0.821 | no | ✅ |
| Quantum Random Number Generation (QRNG) & Entropy Management | Quantum Computing & HPC | Quantum Computing & HPC | 0.821 | 0.821 | no | ✅ |
| Quantum-Accelerated Supercomputing | Quantum Computing & HPC | Quantum Computing & HPC | 0.815 | 0.815 | no | ✅ |
| Quantum-Classical Hybrid Workflows | Quantum Computing & HPC | Quantum Computing & HPC | 0.815 | 0.815 | no | ✅ |
| Near-Term Quantum Applications (chemistry, materials, optimization) | Quantum Computing & HPC | Quantum Computing & HPC | 0.787 | 0.787 | no | ✅ |
| Distributed Training with Ray + PyTorch | Distributed Compute (Ray/Python) | Distributed Compute (Ray/Python) | 0.786 | 0.786 | no | ✅ |
| Quantum: Hype vs. Reality & the Commercial Timeline | Quantum Computing & HPC | Quantum Computing & HPC | 0.739 | 0.739 | no | ✅ |
| Agent Observability & Monitoring | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.975 | 0.682 | no | ✅ |
| Agent Observability & Management | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.975 | 0.679 | no | ✅ |
| GTM Engineering | GTM & Marketing Engineering | GTM & Marketing Engineering | 0.953 | 0.652 | no | ✅ |
| GTM Engineering (the emerging role) | GTM & Marketing Engineering | GTM & Marketing Engineering | 0.953 | 0.644 | no | ✅ |
| The Data Cloud as AI/Agent Foundation | Data Foundations for AI | Data Foundations for AI | 0.945 | 0.635 | no | ✅ |
| AI Agent Observability | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.924 | 0.629 | no | ✅ |
| Open-source AI Infrastructure | AI Compute Infrastructure | AI Compute Infrastructure | 0.912 | 0.612 | no | ✅ |
| Data Foundations for AI Agents | Data Foundations for AI | Data Foundations for AI | 0.908 | 0.611 | no | ✅ |
| Agent Evaluation & Reliability in Production | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.894 | 0.609 | no | ✅ |
| AI Agent Reliability & Evaluation | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.915 | 0.608 | no | ✅ |
| Scaling AI Agents to Production / Reliability | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.915 | 0.607 | no | ✅ |
| Enterprise AI Agent Security & Governance | AI & Agent Security & Governance | AI & Agent Security & Governance | 0.894 | 0.601 | no | ✅ |
| Production Voice Agent Architecture (Deployment, Scaling, Observability) | Voice AI Infrastructure | Voice AI Infrastructure | 0.882 | 0.595 | no | ✅ |
| Coding Agents for GTM | Coding Agents | Coding Agents | 0.882 | 0.591 | no | ✅ |
| Personal & Local AI Infrastructure | AI Compute Infrastructure | AI Compute Infrastructure | 0.879 | 0.586 | no | ✅ |
| Hiring in AI-Era Engineering Orgs | AI Talent, Hiring & Leadership | AI Talent, Hiring & Leadership | 0.865 | 0.582 | no | ✅ |
| OpenClaw & the Future of Software | The Software Development Shift | The Software Development Shift | 0.833 | 0.571 | no | ✅ |
| Successful AI Deployment Requirements | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.850 | 0.565 | no | ✅ |
| Local-First / Sovereign AI | AI Compute Infrastructure | AI Compute Infrastructure | 0.837 | 0.563 | no | ✅ |
| AI Startup Hiring Trends | AI Talent, Hiring & Leadership | AI Talent, Hiring & Leadership | 0.822 | 0.561 | no | ✅ |
| Multichannel Conversational AI & CPaaS | Voice AI Infrastructure | Voice AI Infrastructure | 0.835 | 0.558 | no | ✅ |
| AI Content Engineering / Editorial Pipelines | Agentic Marketing | Agentic Marketing | 0.827 | 0.558 | no | ✅ |
| Content & Brand AI | Agentic Marketing | Agentic Marketing | 0.827 | 0.558 | no | ✅ |
| Apache Spark | Distributed Compute (Ray/Python) | Distributed Compute (Ray/Python) | 0.808 | 0.557 | no | ✅ |
| CS as Business Transformation (Outcomes Over Admin) | Customer Success Transformation | Customer Success Transformation | 0.812 | 0.551 | no | ✅ |
| Why Agents Fail in Production / Agentic Guardrails | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.821 | 0.550 | no | ✅ |
| Agent Memory & Human Handoff Design | Agent Architecture & Memory | Agent Architecture & Memory | 0.823 | 0.549 | no | ✅ |
| Computer-Use / Production Browser Agents | Agent Architecture & Memory | Agent Architecture & Memory | 0.814 | 0.547 | no | ✅ |
| CS Owning Revenue Outcomes (Expansion + Retention as Commercial Accountability) | Customer Success Transformation | Customer Success Transformation | 0.812 | 0.546 | no | ✅ |
| Contextual SLMs & Prompt/Context Compression | Context & Prompt Engineering | Context & Prompt Engineering | 0.800 | 0.541 | no | ✅ |
| Content Engineering | Agentic Marketing | Agentic Marketing | 0.819 | 0.540 | no | ✅ |
| The NYC AI Talent Layer | AI Talent, Hiring & Leadership | AI Talent, Hiring & Leadership | 0.806 | 0.540 | no | ✅ |
| AI App Infrastructure & Deployment (serverless GPU) | AI Compute Infrastructure | AI Compute Infrastructure | 0.815 | 0.539 | no | ✅ |
| Executive Relationships & The Modern CS Career Path | Customer Success Transformation | Customer Success Transformation | 0.787 | 0.537 | no | ✅ |
| LLM Observability and Tracing | Agent Reliability & Evaluation | Agent Reliability & Evaluation | 0.790 | 0.530 | no | ✅ |
| Independent Media Economics in the AI Era | AI Capital, Business Models & Media | AI Capital, Business Models & Media | 0.783 | 0.522 | no | ✅ |
| Microsoft Fabric | Microsoft AI Stack | Microsoft AI Stack | 0.749 | 0.518 | no | ✅ |
| Legal & Compliance AI | AI & Agent Security & Governance | AI & Agent Security & Governance | 0.759 | 0.504 | no | ✅ |
| Agentic Payment Rails & Protocols (x402, AP2, card networks, stablecoins) | Agentic Commerce & Payments | Agentic Commerce & Payments | 0.750 | 0.503 | no | ✅ |
| Marketing & Revenue Attribution Evolution | Agentic Marketing | Agentic Marketing | 0.757 | 0.502 | no | ✅ |
| CRM as System of Action | GTM Operating Model | GTM Operating Model | 0.753 | 0.492 | no | ✅ |
| Data Cloud × Agentic AI | Data Foundations for AI | Data Foundations for AI | 0.945 | 0.327 | no | ✅ |
| AI Infrastructure for Large-Scale Systems | AI Compute Infrastructure | AI Compute Infrastructure | 0.912 | 0.310 | no | ✅ |
| Engineering Leadership in the AI Era | AI Talent, Hiring & Leadership | AI Talent, Hiring & Leadership | 0.865 | 0.309 | no | ✅ |
| Agentic Marketing Workflows | Agentic Marketing | Agentic Marketing | 0.883 | 0.309 | no | ✅ |
| Agentic Commerce (thesis: real vs. narrative + who owns the relationship) | Agentic Commerce & Payments | Agentic Commerce & Payments | 0.867 | 0.305 | no | ✅ |
| Spark Resource Optimization & Auto-Rightsizing | Distributed Compute (Ray/Python) | Distributed Compute (Ray/Python) | 0.808 | 0.295 | no | ✅ |
| Copilot in Fabric | Microsoft AI Stack | Microsoft AI Stack | 0.749 | 0.294 | no | ✅ |
| Production Agentic Infrastructure | MCP & Agent-Ready APIs | MCP & Agent-Ready APIs | 0.863 | 0.292 | no | ✅ |
| Ray for AI Workloads | Distributed Compute (Ray/Python) | Distributed Compute (Ray/Python) | 0.839 | 0.285 | no | ✅ |
| Adaptive Software & Agent-Driven UIs | Agent Architecture & Memory | Agent Architecture & Memory | 0.834 | 0.285 | no | ✅ |
| Azure AI Foundry as Agentic Runtime | Microsoft AI Stack | Microsoft AI Stack | 0.846 | 0.284 | no | ✅ |
| Programmatic Prompt Optimization (DSPy) | Context & Prompt Engineering | Context & Prompt Engineering | 0.800 | 0.283 | no | ✅ |
| Conversational AI Design Patterns (Turn-Taking, Interruption, Latency) | Voice AI Infrastructure | Voice AI Infrastructure | 0.835 | 0.283 | no | ✅ |
| Agent-Ready APIs (OpenAPI for Agents) | MCP & Agent-Ready APIs | MCP & Agent-Ready APIs | 0.841 | 0.282 | no | ✅ |
| The Future of Software Development Shift | The Software Development Shift | The Software Development Shift | 0.810 | 0.279 | no | ✅ |
| Postgres as the Agent Data Layer | Agentic Data Access | Agentic Data Access | 0.827 | 0.278 | no | ✅ |
| The SDR Role Reshape | Outbound & the SDR Reshape | Outbound & the SDR Reshape | 0.770 | 0.273 | no | ✅ |
| Future of Data Infrastructure | Data Foundations for AI | Data Foundations for AI | 0.793 | 0.269 | no | ✅ |
| Agent Skills & Specialization | Agent Architecture & Memory | Agent Architecture & Memory | 0.789 | 0.268 | no | ✅ |
| AI x Media Convergence | AI Capital, Business Models & Media | AI Capital, Business Models & Media | 0.783 | 0.266 | no | ✅ |
| Right-Time Data & The Modern Data Stack Inversion | Data Foundations for AI | Data Foundations for AI | 0.759 | 0.253 | no | ✅ |
| Microsoft Purview | Microsoft AI Stack | Microsoft AI Stack | 0.675 | 0.234 | no | ✅ |
| Freedom Tech Movement | AI Compute Infrastructure | AI Compute Infrastructure | 0.645 | 0.220 | no | ✅ |
| Custom AI Infrastructure in Regulated Environments | AI & Agent Security & Governance | AI Compute Infrastructure | 0.881 | 0.881 | yes | ❌ |
| Voice AI for B2B Outbound | Outbound & the SDR Reshape | Voice AI Infrastructure | 0.839 | 0.839 | no | ❌ |
| Cassandra / Astra DB Data Modeling for AI | Agentic Data Access | Data Foundations for AI | 0.836 | 0.836 | no | ❌ |
| AI Sales Coaches & Conversation Intelligence | Outbound & the SDR Reshape | Voice AI Infrastructure | 0.825 | 0.825 | no | ❌ |
| GTM Operating Systems vs. Point Tools | GTM Operating Model | GTM & Marketing Engineering | 0.802 | 0.802 | no | ❌ |
| Marketing Engineering (the role) | GTM & Marketing Engineering | Agentic Marketing | 0.741 | 0.741 | no | ❌ |
| Durable Execution for AI Agents | MCP & Agent-Ready APIs | Agent Reliability & Evaluation | 0.915 | 0.621 | no | ❌ |
| Cloud Sandboxes for AI Agents | Coding Agents | Data Foundations for AI | 0.905 | 0.614 | no | ❌ |
| Data Infrastructure & Observability for AI | Data Foundations for AI | AI Compute Infrastructure | 0.886 | 0.595 | no | ❌ |
| MCP for Databases / Agentic Data Access (beyond RAG) | Agentic Data Access | MCP & Agent-Ready APIs | 0.866 | 0.579 | no | ❌ |
| API Governance for Agentic Systems | AI & Agent Security & Governance | MCP & Agent-Ready APIs | 0.870 | 0.578 | no | ❌ |
| AI-Powered GTM (incl. embedded / MCP GTM) | AI-Native GTM & Revenue Agents | GTM & Marketing Engineering | 0.858 | 0.578 | no | ❌ |
| Real-World AI Use Cases & Deployment | Forward-Deployed & Enterprise Adoption | Agent Reliability & Evaluation | 0.850 | 0.570 | no | ❌ |
| AI Developer Tooling Ecosystem | AI Dev Tooling & IDEs | AI Compute Infrastructure | 0.840 | 0.561 | no | ❌ |
| Agents as Users / The New Application Layer | Agent Architecture & Memory | MCP & Agent-Ready APIs | 0.836 | 0.556 | no | ❌ |
| Agentic Analytics & The Semantic Layer | Semantic Layer & Lineage | Data Foundations for AI | 0.831 | 0.552 | no | ❌ |
| From Chatbots to Structured Intelligence | Knowledge & Retrieval | Voice AI Infrastructure | 0.820 | 0.550 | no | ❌ |
| AI Engineering (building & shipping AI apps) | AI Engineering Practice | The Software Development Shift | 0.824 | 0.545 | no | ❌ |
| TAM Mapping & Audience-Building with AI | Outbound & the SDR Reshape | AI Talent, Hiring & Leadership | 0.810 | 0.542 | no | ❌ |
| AI-Generated Code Governance & Risk Tolerance | AI & Agent Security & Governance | Coding Agents | 0.812 | 0.542 | no | ❌ |
| Agent-to-Agent (A2A) Transactions & Agent Identity/Trust | Agentic Commerce & Payments | AI & Agent Security & Governance | 0.825 | 0.539 | no | ❌ |
| Consumption-Based vs. Seat-Based Pricing for Enterprise AI | AI Capital, Business Models & Media | AI-Native GTM & Revenue Agents | 0.798 | 0.534 | no | ❌ |
| Frontier AI Investing & Capital Flows (Service-as-Software) | AI Capital, Business Models & Media | AI Compute Infrastructure | 0.791 | 0.528 | no | ❌ |
| AI for HR & Performance Management | Vertical & Applied AI | AI Talent, Hiring & Leadership | 0.792 | 0.525 | no | ❌ |
| Distributed Python Ecosystem | Distributed Compute (Ray/Python) | AI Dev Tooling & IDEs | 0.780 | 0.521 | no | ❌ |
| Personal Cloud Infrastructure & Democratized Computing | AI Compute Infrastructure | Data Foundations for AI | 0.773 | 0.512 | no | ❌ |
| Distributed DataFusion | Distributed Compute (Ray/Python) | Data Foundations for AI | 0.768 | 0.511 | no | ❌ |
| AI SDR Hits & Misses | Outbound & the SDR Reshape | Agent Reliability & Evaluation | 0.770 | 0.510 | no | ❌ |
| Rust in Production / Core Services | Distributed Compute (Ray/Python) | MCP & Agent-Ready APIs | 0.666 | 0.440 | no | ❌ |
| Agentic AI | AI Engineering Practice | AI & Agent Security & Governance | 0.928 | 0.321 | no | ❌ |
| Agentic AI Security | AI & Agent Security & Governance | AI Engineering Practice | 0.928 | 0.321 | no | ❌ |
| Agentic Marketing | Agentic Marketing | Agentic Commerce & Payments | 0.890 | 0.305 | no | ❌ |
| Agentic Commerce | Agentic Commerce & Payments | Agentic Marketing | 0.890 | 0.304 | no | ❌ |
| MCP for Marketing | Agentic Marketing | MCP & Agent-Ready APIs | 0.827 | 0.301 | no | ❌ |
| Agentic Systems (FDE Lens) | Forward-Deployed & Enterprise Adoption | Distributed Compute (Ray/Python) | 0.863 | 0.299 | no | ❌ |
| Agents & APIs (how agents consume/orchestrate APIs) | MCP & Agent-Ready APIs | AI & Agent Security & Governance | 0.870 | 0.297 | no | ❌ |
| AI Revenue Agents & Agentic GTM | AI-Native GTM & Revenue Agents | Coding Agents | 0.864 | 0.295 | no | ❌ |
| Agentic Systems on Ray | Distributed Compute (Ray/Python) | Forward-Deployed & Enterprise Adoption | 0.863 | 0.294 | no | ❌ |
| Agentic Infrastructure & MCP | MCP & Agent-Ready APIs | Agentic Data Access | 0.866 | 0.294 | no | ❌ |
| AI Agent Memory Layer | Agent Architecture & Memory | MCP & Agent-Ready APIs | 0.866 | 0.290 | no | ❌ |
| Spec-Driven Development with Agentic AI | The Software Development Shift | AI Engineering Practice | 0.861 | 0.289 | no | ❌ |
| OCI for AI Workloads | AI Compute Infrastructure | Distributed Compute (Ray/Python) | 0.839 | 0.286 | no | ❌ |
| Reliable GTM Systems with Code | GTM & Marketing Engineering | AI-Native GTM & Revenue Agents | 0.851 | 0.286 | no | ❌ |
| Microsoft's AI Agent Factory Thesis | Microsoft AI Stack | Agent Reliability & Evaluation | 0.853 | 0.286 | no | ❌ |
| Context Engineering | Context & Prompt Engineering | Agentic Marketing | 0.819 | 0.285 | no | ❌ |
| Enterprise Sales & GTM Intelligence | GTM Operating Model | AI-Native GTM & Revenue Agents | 0.824 | 0.283 | no | ❌ |
| Autonomous Agent Frameworks (OpenClaw) | The Software Development Shift | MCP & Agent-Ready APIs | 0.839 | 0.282 | no | ❌ |
| MCP at Enterprise Scale | MCP & Agent-Ready APIs | Agentic Marketing | 0.827 | 0.280 | no | ❌ |
| Production AI Demos and Shipping Patterns | Forward-Deployed & Enterprise Adoption | AI Engineering Practice | 0.824 | 0.280 | no | ❌ |
| Non-Engineers Building With AI / The New Builder | The Software Development Shift | AI Engineering Practice | 0.816 | 0.279 | no | ❌ |
| AI Agents for Customer Experience (CX) | Voice AI Infrastructure | Agent Reliability & Evaluation | 0.831 | 0.279 | no | ❌ |
| Enterprise AI Adoption (FDE-led) | Forward-Deployed & Enterprise Adoption | Coding Agents | 0.826 | 0.278 | no | ❌ |
| Commerce & Supply Chain Intelligence | Agentic Commerce & Payments | GTM Operating Model | 0.789 | 0.278 | no | ❌ |
| Self-Hosted AI Inference | AI Compute Infrastructure | Data Foundations for AI | 0.828 | 0.278 | no | ❌ |
| AI-DLC (AI-Driven Development Lifecycle) | The Software Development Shift | AI Dev Tooling & IDEs | 0.827 | 0.277 | no | ❌ |
| Agent Architecture Patterns | Agent Architecture & Memory | AI & Agent Security & Governance | 0.827 | 0.277 | no | ❌ |
| AI's Impact on CI Infra / Build Speed | AI Dev Tooling & IDEs | AI Compute Infrastructure | 0.812 | 0.276 | no | ❌ |
| RevOps in the AI Era | GTM Operating Model | MCP & Agent-Ready APIs | 0.821 | 0.276 | no | ❌ |
| Agentic CI / Independent Proof-of-Behavior | Agent Reliability & Evaluation | AI Engineering Practice | 0.820 | 0.275 | no | ❌ |
| Bedrock as an Enterprise AI Control Plane | Enterprise AI Control Planes | Coding Agents | 0.817 | 0.275 | no | ❌ |
| AI in Healthcare Revenue Cycle Management | Vertical & Applied AI | AI-Native GTM & Revenue Agents | 0.806 | 0.273 | no | ❌ |
| Building Agentic Products (Designing for a Shifting Frontier) | Agent Architecture & Memory | Agentic Commerce & Payments | 0.815 | 0.273 | no | ❌ |
| AI-Native Go-To-Market | AI-Native GTM & Revenue Agents | Outbound & the SDR Reshape | 0.806 | 0.272 | no | ❌ |
| The NYC AI/Data Scene Gatekeeper Structure | AI Talent, Hiring & Leadership | Outbound & the SDR Reshape | 0.810 | 0.271 | no | ❌ |
| Multi-Agent Coordination Without Orchestrators | Agent Architecture & Memory | The Software Development Shift | 0.807 | 0.271 | no | ❌ |
| ML/AI Lineage, Provenance & MLOps Source of Truth | Semantic Layer & Lineage | GTM Operating Model | 0.796 | 0.270 | no | ❌ |
| GitHub as Agentic Developer Platform | AI Dev Tooling & IDEs | Coding Agents | 0.797 | 0.266 | no | ❌ |
| Robotics & Embodied AI (Physical AI) | Vertical & Applied AI | Forward-Deployed & Enterprise Adoption | 0.795 | 0.266 | no | ❌ |
| VS Code as Agent-Native IDE | AI Dev Tooling & IDEs | Coding Agents | 0.781 | 0.264 | no | ❌ |
| Workflow Collapse — The 2026 GTM Pattern | GTM Operating Model | GTM & Marketing Engineering | 0.769 | 0.262 | no | ❌ |
| AI-Native Vertical SaaS | Vertical & Applied AI | AI Capital, Business Models & Media | 0.782 | 0.262 | no | ❌ |
| AI-Driven Outbound & Personalized Sequencing at Scale | Outbound & the SDR Reshape | Agent Reliability & Evaluation | 0.774 | 0.260 | no | ❌ |
| AI Media Compression for eCommerce | Vertical & Applied AI | AI Capital, Business Models & Media | 0.776 | 0.260 | no | ❌ |
| AI Search Optimization (AEO / GEO) | Agentic Marketing | Data Foundations for AI | 0.767 | 0.258 | no | ❌ |
| Ruby + AI Resurgence / Vibe Coding / Ship-Things Culture | The Software Development Shift | GTM Operating Model | 0.769 | 0.257 | no | ❌ |
| Personalization at the Signal Layer | Agentic Marketing | Outbound & the SDR Reshape | 0.763 | 0.257 | no | ❌ |
| Single-Player to Multiplayer GTM | GTM Operating Model | GTM & Marketing Engineering | 0.751 | 0.253 | no | ❌ |
| Accelerator Ecosystem Dynamics | AI Capital, Business Models & Media | Distributed Compute (Ray/Python) | 0.741 | 0.253 | no | ❌ |
| RAG (Retrieval-Augmented Generation) | Knowledge & Retrieval | Outbound & the SDR Reshape | 0.750 | 0.251 | no | ❌ |
| Forward Deployed Engineering | Forward-Deployed & Enterprise Adoption | GTM & Marketing Engineering | 0.744 | 0.249 | no | ❌ |
| Cortex Code / Snowflake CoCo | Data Foundations for AI | The Software Development Shift | 0.702 | 0.247 | no | ❌ |
| LLM Knowledge Bases | Knowledge & Retrieval | Agent Reliability & Evaluation | 0.701 | 0.241 | no | ❌ |
| Claude CoWork / Desktop for Knowledge Workers | Enterprise AI Control Planes | Agent Architecture & Memory | 0.715 | 0.239 | no | ❌ |
| Claude Managed Agents | Enterprise AI Control Planes | Agent Reliability & Evaluation | 0.708 | 0.238 | no | ❌ |
| Vercel Workflows | MCP & Agent-Ready APIs | GTM Operating Model | 0.691 | 0.233 | no | ❌ |
| OneLake | Microsoft AI Stack | Distributed Compute (Ray/Python) | 0.609 | 0.205 | no | ❌ |
