# TATF v1.0 — Introduction

**TRUCE Agent Trust Framework (TATF)**
*An Open Standard for Autonomous Agent Trust Scoring*

**Version:** 1.0.0-draft
**Status:** Working Draft
**License:** Apache 2.0
**Date:** 2026-04-20

---

## Abstract

The TRUCE Agent Trust Framework (TATF) defines a protocol-agnostic
methodology for scoring the trustworthiness of autonomous LLM agents
engaged in commercial transactions.

As agent-to-agent (A2A) and human-to-agent (H2A) commerce scales —
Gartner projects $15 trillion in B2B procurement to flow through
AI-agent exchanges by 2028 — participants need a standardized,
neutral, auditable mechanism to assess whether a counterparty agent
can be trusted to fulfil its obligations.

TATF provides this through a **signal-aggregating scoring model**
with five component surfaces:

1. **Observable Metrics** — Objective, externally verifiable behaviour.
2. **Behavioural Baselines** — Anomaly detection against the agent's
   own history (six dimensions, exponential moving average).
3. **Community Signals** — Cross-platform reputation data and peer
   ratings.
4. **External Signals** — Aggregated inputs from specialised providers
   (prompt-injection detection, governance maturity, runtime threat
   feeds). *New in v1.0.*
5. **Adversarial Testing** — Proactive resilience evaluation.

TATF is designed to be:

- **Protocol-agnostic** — Works with MCP, A2A, ACP, x402, MPP, or
  custom agent protocols.
- **Platform-neutral** — No dependency on any single vendor, cloud,
  or LLM provider.
- **Composable** — External signal providers are pluggable through
  a connector contract defined in document 07.
- **Privacy-preserving** — k-anonymity guarantees on aggregate
  indicators; signal fusion does not require raw data sharing.
- **Incrementally adoptable** — Each component surface can be
  implemented independently.

---

## The Spec / Implementation Split

TATF follows the same pattern as credit scoring:

| Entity | Role | Analogy |
|--------|------|---------|
| **TATF** | The open methodology — this specification, benchmarks, reference implementation | The FICO scoring method (public, auditable) |
| **TRUCE** | A commercial aggregator that implements TATF, curates partner signals, runs hosted services | Fair Isaac Corporation (the company) |

Anyone MAY implement TATF. The openness of the methodology is a
*precondition* for trust, not a competitive risk. Commercial value
accrues to implementations that maintain signal partnerships,
training data pipelines, and delivery infrastructure — not to
ownership of the scoring algorithm itself.

TRUCE is the reference implementer. Other conformant implementations
are expected and welcomed.

---

## Motivation

### The Trust Gap in Agent Commerce

The autonomous agent economy is growing fast. Recent data points
(2026):

- **Amazon Rufus** — agentic auto-buy contributing ~$10B incremental
  annualised sales; 250M users.
- **Agent Payments Stack** — 179 projects tracked; 140M cumulative
  transactions.
- **Stablecoin rails** — x402 (Coinbase/Cloudflare) and MPP (Stripe
  on Tempo) both launched agent-native payment protocols.
- **Gartner** — projects 90% of B2B buying to be AI-agent-intermediated
  by 2028 ($15T in flow).

Protocols for agent *communication* (MCP, A2A) and *payment* (x402,
MPP) are standardised or rapidly converging. What remains absent:
a standard mechanism for a counterparty to answer the question that
actually matters when money is on the line:

> *"Should I trust this agent to fulfil this specific transaction?"*

TATF addresses this gap.

### Alignment with CSA MAESTRO Identified Risks

The Cloud Security Alliance's MAESTRO framework identified five
critical gaps in current agent commerce protocols. TATF directly
addresses each:

| MAESTRO Gap | TATF Coverage |
|-------------|---------------|
| No behavioural anomaly detection | Layer 2 (document 02) |
| No cross-platform trust scoring | Layer 3 + Layer 4 (documents 01, 07) |
| No standardised trust attestation | Document 04 |
| No adversarial resilience testing | Document 05 |
| No privacy-preserving aggregate risk | Document 06 (AVX, k-anonymity) |

### Why an Open Standard?

Trust scoring is a conflict-of-interest problem. A platform operator
(Google, OpenAI, Stripe, Amazon) cannot simultaneously be a market
participant *and* the trust arbiter for that market. The operator
has commercial incentive to score competitors lower.

An open standard removes that conflict at the methodology layer:

- **Transparency** — The scoring algorithm is auditable; outputs can
  be reproduced by any conformant implementation.
- **Interoperability** — Any platform, any framework, any rail can
  integrate.
- **Neutrality** — No single vendor controls the scoring criteria.
- **Community governance** — The specification evolves through RFCs
  and consensus (see `CONTRIBUTING.md`).

Commercial implementations (including TRUCE) compete on signal
quality, aggregation breadth, delivery performance, and support —
not on opacity.

### The Ground Truth Problem

Unlike credit scoring, where "default vs. no-default" provides a
binary ground truth, agent trust has no inherent objective measure.

TATF solves this through **relative scoring** plus **external
signal corroboration**:

| Domain | Ground Truth | Scoring Method |
|--------|-------------|----------------|
| Credit (FICO) | Default / no-default | Absolute probability |
| Search (Google) | User clicked / didn't click | Click-through rate |
| Spam (email) | User flagged / didn't flag | User feedback loop |
| **Agent Trust (TATF)** | **Agent's own behavioural history + corroborating external signals** | **Relative anomaly + signal fusion** |

An agent is scored against its own baseline (Layer 2), with the
score corroborated or contradicted by independent external signals
(Layer 4). Concordant low scores across sources indicate real risk;
a single-dimension outlier is de-emphasised.

---

## Scope

### In Scope (v1.0)

- Trust scoring methodology for autonomous commercial agents.
- Behavioural baseline establishment and anomaly detection.
- **Signal aggregation contract** for external providers (new in v1.0).
- Trust attestation format (TATF Native + W3C Verifiable Credential).
- Aggregate market stress indicators with k-anonymity guarantees.
- Benchmark dataset specification for implementation validation.

### Out of Scope

- Agent identity provisioning (complementary to existing identity
  standards; TATF assumes agents have stable identifiers).
- Payment processing or settlement mechanics (delegated to x402,
  MPP, and other payment rails).
- Agent communication protocols (TATF is protocol-agnostic; it
  plugs into MCP, A2A, ACP, etc.).
- Specific regulatory compliance (TATF maps *to* regulations via
  document 08, not *from* them).

---

## Terminology

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous software entity that can engage in commercial transactions on behalf of a principal (human or organisation). |
| **Principal** | The human or organisation on whose behalf an agent acts. |
| **Firm** | The business entity that owns / operates one or more agents. |
| **Trust Score** | A normalised value (0.0–1.0) representing the assessed trustworthiness of an agent at a point in time. |
| **Behavioural Baseline** | A statistical profile of an agent's normal operating parameters, maintained via exponential moving average. |
| **Anomaly Score** | A composite metric (0–200) measuring deviation from baseline across six dimensions. |
| **External Signal** | A trust-relevant score or event emitted by a TATF-compatible third-party provider (e.g. prompt-injection detector, runtime threat feed). |
| **Signal Source** | A system that emits external signals according to the contract in document 07. |
| **Aggregator** | A TATF implementation that combines its own signals with one or more external signals into a composite score. |
| **Attestation** | A cryptographically signed statement by a TATF-conformant scorer about an agent's trust level. |
| **Cold Start** | The initial observation period (default 14 days) before behavioural scoring activates. |
| **ATBF Zone** | Anomaly-Triggered Behavioural Fencing — routing decisions based on anomaly score thresholds. |

---

## Document Structure

| # | Document | Contents |
|---|----------|----------|
| 00 | `00-introduction.md` | *This document.* |
| 01 | `01-scoring-model.md` | Five-component ALPHA model; scoring formula; tiers; output format. |
| 02 | `02-behavioral-baselines.md` | EMA baseline establishment; cold-start; six scoring dimensions. |
| 03 | `03-anomaly-detection.md` | ATBF zones; routing; SOFT_HOLD review queue. |
| 04 | `04-trust-attestation.md` | Cryptographic attestation; TATF Native + W3C VC formats; signal provenance. |
| 05 | `05-adversarial-testing.md` | Layer-5 adversarial resilience testing; partner integration. |
| 06 | `06-market-stress.md` | AVX four-dimension stress indicator; k-anonymity. |
| 07 | `07-signal-aggregation.md` | **External signal contract; normalisation; fusion; connector architecture.** *(new in v1.0)* |
| 08 | `08-regulatory-mapping.md` | EU AI Act, NIST AI RMF, ISO/IEC 42001 mapping detail. *(new in v1.0)* |

---

## Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in
this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

A TATF v1.0 conformant implementation:

- **MUST** implement Layer 1 (Observable Metrics) and Layer 2
  (Behavioural Baselines).
- **MUST** use the six-dimension anomaly scoring model defined in
  document 02.
- **MUST** implement ATBF zone routing as defined in document 03.
- **MUST** produce trust attestations in the format defined in
  document 04, including external signal provenance when signals
  are aggregated.
- **MUST** enforce k-anonymity on aggregate metrics as defined in
  document 06.
- **SHOULD** implement Layer 3 (Community Signals) when cross-platform
  data is available.
- **SHOULD** support at least one external signal connector per
  document 07 if marketed as an aggregator.
- **MAY** implement Layer 5 (Adversarial Testing) for enhanced
  assurance.

An implementation that does not aggregate external signals is still
conformant and SHOULD self-describe as "TATF v1.0 core" rather than
"TATF v1.0 aggregator".

---

## Changes Since v0.1

This version introduces:

1. **Explicit TATF / implementer split** — the methodology is open;
   implementations compete on delivery.
2. **External signal aggregation** — document 07 defines a contract
   for plugging in specialised providers (prompt injection, governance,
   runtime threats).
3. **Extended ALPHA composite** — a fifth optional component (`XS`,
   External Signals) that defaults to neutral when absent.
4. **Signal provenance in attestations** — consumers can see which
   signals contributed to a score.
5. **Regulatory mapping document** (08) — expanded detail on EU AI
   Act Articles 13/14/15 alignment.

Implementations conformant with v0.1 can reach v1.0 core conformance
without changes; v1.0 aggregator conformance requires at least one
connector per document 07.

---

## Regulatory Alignment (Summary)

Detailed mapping is in document 08. High-level:

| Regulation | TATF Alignment |
|-----------|----------------|
| **EU AI Act** (enforceable 2026-08-02) | Articles 13 (transparency), 14 (human oversight), 15 (robustness), plus GDPR Article 25. Document 08 provides article-by-article crosswalk. |
| **NIST AI RMF** | TATF's component surfaces map to Govern, Map, Measure, Manage functions. |
| **ISO/IEC 42001** | TATF scoring supports AI management system requirements. |
| **PCI DSS v4.0** | TATF behavioural monitoring aligns with continuous monitoring requirements for card-data environments. |

---

*Next: [01-scoring-model.md](01-scoring-model.md) — The Five-Component ALPHA Model*
