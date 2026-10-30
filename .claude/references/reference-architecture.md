# Applied-AI Reference Architecture (S-03)

One taxonomy for the market-intelligence topics so both hubs can show signal
density per layer. Spec: `docs/specs/shared/S-03-reference-architecture-layers.md`
(Linear YED-126). The topic→layer map is `.claude/references/topic-layers.json`;
it is a **proposal only** — merging duplicates stays with Alex.

Each layer below has a one-line definition and 2–3 example topics drawn from
`.claude/references/topics-snapshot.json` (exported read-only from
`public.topic` on 2026-10-30).

## Layers

### model
Foundation models and what happens inside them: releases, reasoning and
test-time compute, training, small/specialized models, model economics.
**Example topics:** Frontier Model Releases (GPT-6 / Gemini / Fable); LLM Reasoning & Test-Time Compute; Open-Weight LLMs

### environment
Where agents and AI workloads run: clouds and neoclouds, GPUs and custom
silicon, sandboxes, serving infrastructure and the cost of compute.
**Example topics:** Alt Clouds & Neoclouds; AI Inference Hardware & Custom Silicon; Cloud Sandboxes for AI Agents

### harness
The scaffolding around models: agent frameworks, orchestration, MCP and tool
calling, context engineering, coding agents and agent-native interfaces.
**Example topics:** MCP (Model Context Protocol) Tool Calling; Context Engineering; VS Code as Agent-Native IDE

### factory
How software is designed, built, reviewed and shipped when agents do the
building: AI-driven development lifecycle, autonomous software factories, CI
in the AI era.
**Example topics:** Autonomous Software Factories (Level 1 → Level 2); Spec-Driven Development with Agentic AI; AI's Impact on CI Infra / Build Speed

### data-retrieval
Getting the right context to models: data infrastructure, RAG, vector search,
semantic layers, lakehouses and the modern data stack.
**Example topics:** RAG (Retrieval-Augmented Generation); Lakehouse & Open Table Formats 2026; Retrieval Quality: Embeddings, Reranking & Hybrid Search

### evals-observability
Knowing whether AI works: evaluation suites and metrics, tracing and
observability, reliability engineering and production failure modes.
**Example topics:** LLM Evaluation; LLM Observability and Tracing; Why Agents Fail in Production / Agentic Guardrails

### identity-governance
Who agents are and what they may do: identity, auth, security, compliance,
governance and trust — for humans, agents and APIs.
**Example topics:** Agentic Identity & Auth; Enterprise AI Agent Security & Governance; Trust, Fraud, Authorization & Liability when the Buyer is an Agent

### gtm-distribution
How AI products reach and monetize customers: sales, marketing, customer
success, pricing, RevOps and distribution strategy — for and with AI.
**Example topics:** AI Sales Agents; AI Search Optimization (AEO / GEO); Consumption-Based vs. Seat-Based Pricing for Enterprise AI

### domain-applications
Agents applied in a specific domain or industry: vertical SaaS, healthcare,
fintech, legal, media, robotics and horizontal business applications.
**Example topics:** AI in Healthcare Revenue Cycle Management; Vertical AI Applications; Robotics & Embodied AI (Physical AI)

### market-context
The surrounding landscape: capital flows, talent markets, policy and
geopolitics, ecosystem structure and the shape of the AI economy.
**Example topics:** Frontier AI Investing & Capital Flows (Service-as-Software); The NYC AI Talent Layer; AI Policy & Geopolitics
