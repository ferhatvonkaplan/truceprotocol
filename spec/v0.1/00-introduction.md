# TATF v0.1 — Introduction

**TRUCE Agent Trust Framework (TATF)**
*An Open Standard for Autonomous Agent Trust Scoring*

**Version:** 0.1.0-draft
**Status:** Working Draft
**License:** Apache 2.0
**Date:** 2026-03-13

---

## Abstract

The TRUCE Agent Trust Framework (TATF) defines a protocol-agnostic
methodology for scoring the trustworthiness of autonomous LLM agents
engaged in commercial transactions. As agent-to-agent (A2A) and
human-to-agent (H2A) commerce scales, participants need a standardized,
neutral mechanism to assess whether a counterparty agent can be trusted
to fulfill its obligations.

TATF provides this mechanism through a four-layer scoring model:

1. **Observable Metrics** — Objective, measurable agent behavior
2. **Behavioral Baselines** — Anomaly detection relative to an agent's own history
3. **Community Signals** — Cross-platform reputation aggregation
4. **Adversarial Testing** — Proactive resilience evaluation

TATF is designed to be:
- **Protocol-agnostic** — Works with any agent communication protocol (A2A, ACP, MCP, custom)
- **Platform-neutral** — No dependency on any single vendor or cloud provider
- **Privacy-preserving** — k-anonymity guarantees on aggregate metrics
- **Incrementally adoptable** — Each layer can be implemented independently

## Motivation

### The Trust Gap in Agent Commerce

The autonomous agent economy is projected to reach $52B by 2030
(Gartner). Google's Agent-to-Agent Protocol (A2A), OpenAI's Agentic
Commerce Protocol (ACP), and Coinbase's x402 all address agent
*communication* and *payment* — but none define how to assess whether
an agent is **trustworthy**.

The Cloud Security Alliance's MAESTRO framework identified five
critical gaps in current agent commerce protocols:

1. No behavioral anomaly detection
2. No cross-platform trust scoring
3. No standardized trust attestation format
4. No adversarial resilience testing
5. No privacy-preserving aggregate risk metrics

TATF addresses all five gaps.

### Why an Open Standard?

Trust scoring must be performed by a **neutral third party**. A platform
operator (Google, OpenAI, Stripe) cannot simultaneously be a market
participant and a trust arbiter — the conflict of interest is inherent.

An open standard ensures:
- **Transparency** — Scoring methodology is auditable
- **Interoperability** — Any platform can integrate
- **Neutrality** — No single vendor controls the scoring criteria
- **Community governance** — The standard evolves through consensus

### The Ground Truth Problem

Unlike credit scoring (FICO), where "default vs. no-default" provides
a binary ground truth, agent trust has no inherent objective measure.

TATF solves this through **relative scoring**: an agent is measured
against its *own behavioral baseline*, not against an absolute standard.
This eliminates the "scored against what?" problem:

| Domain | Ground Truth | Scoring Method |
|--------|-------------|----------------|
| Credit (FICO) | Default / no-default | Absolute probability |
| Search (Google) | User clicked / didn't click | Click-through rate |
| Spam (email) | User flagged / didn't flag | User feedback loop |
| **Agent Trust (TATF)** | **Agent's own behavioral history** | **Relative anomaly score** |

An agent with a consistent 18-month transaction history behaving
normally scores high. The same agent suddenly trading in a new category
at 3 AM with 10x concurrent sessions scores low — relative to itself.

## Scope

### In Scope

- Trust scoring methodology for autonomous commercial agents
- Behavioral baseline establishment and anomaly detection
- Trust attestation format (W3C Verifiable Credential compatible)
- Aggregate market stress indicators with privacy guarantees
- Benchmark dataset specification for implementation validation

### Out of Scope

- Agent identity provisioning (complementary to existing identity standards)
- Payment processing or settlement mechanics
- Agent communication protocols (TATF is protocol-agnostic)
- Specific regulatory compliance (TATF maps TO regulations, not FROM them)

## Terminology

| Term | Definition |
|------|-----------|
| **Agent** | An autonomous software entity that can engage in commercial transactions on behalf of a principal (human or organization) |
| **Principal** | The human or organization on whose behalf an agent acts |
| **Firm** | The business entity that owns/operates one or more agents |
| **Trust Score** | A normalized value (0.0–1.0) representing the assessed trustworthiness of an agent at a given point in time |
| **Behavioral Baseline** | A statistical profile of an agent's normal operating parameters, maintained via exponential moving average |
| **Anomaly Score** | A composite metric (0–200) measuring deviation from behavioral baseline across six dimensions |
| **Attestation** | A cryptographically signed statement by a TATF-compliant scorer about an agent's trust level |
| **Cold Start** | The initial observation period (default 14 days) before behavioral scoring activates |
| **ATBF Zone** | Anomaly-Triggered Behavioral Fencing — routing decisions based on anomaly score thresholds |

## Document Structure

| Document | Contents |
|----------|----------|
| [01-scoring-model.md](01-scoring-model.md) | Four-layer trust model, composite scoring, ALPHA formula |
| [02-behavioral-baselines.md](02-behavioral-baselines.md) | EMA baseline establishment, cold-start handling, six scoring dimensions |
| [03-anomaly-detection.md](03-anomaly-detection.md) | ATBF zones, z-score methodology, routing decisions, review queue |
| [04-trust-attestation.md](04-trust-attestation.md) | Cryptographic attestation format, W3C VC mapping, notarization |
| [05-adversarial-testing.md](05-adversarial-testing.md) | Layer 4 adversarial resilience testing methodology |
| [06-market-stress.md](06-market-stress.md) | AVX aggregate market stress indicator, k-anonymity |

## Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

A TATF-conformant implementation:
- **MUST** implement Layer 1 (Observable Metrics) and Layer 2 (Behavioral Baselines)
- **MUST** use the six-dimension anomaly scoring model defined in [02-behavioral-baselines.md](02-behavioral-baselines.md)
- **MUST** implement ATBF zone routing as defined in [03-anomaly-detection.md](03-anomaly-detection.md)
- **SHOULD** implement Layer 3 (Community Signals) when cross-platform data is available
- **MAY** implement Layer 4 (Adversarial Testing) for enhanced assurance
- **MUST** produce trust attestations in the format defined in [04-trust-attestation.md](04-trust-attestation.md)
- **MUST** enforce k-anonymity on aggregate metrics as defined in [06-market-stress.md](06-market-stress.md)

## Regulatory Alignment

TATF is designed to map to existing and forthcoming regulations:

| Regulation | TATF Alignment |
|-----------|----------------|
| **EU AI Act** (Aug 2026) | TATF provides the trust scoring required for high-risk AI agent supervision |
| **NIST AI RMF** | TATF's four layers map to NIST's Govern, Map, Measure, Manage functions |
| **ISO/IEC 42001** | TATF scoring supports AI management system requirements |
| **PCI DSS v4.0** | TATF behavioral monitoring aligns with continuous monitoring requirements |

---

*Next: [01-scoring-model.md](01-scoring-model.md) — The Four-Layer Trust Model*
