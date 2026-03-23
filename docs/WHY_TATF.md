# Why TATF?

**Positioning in the Agent Trust Landscape**

---

## The Trust Gap

The agent infrastructure stack is maturing fast:

```
  ┌─────────────────────────────────────────────────────┐
  │                  Agent Commerce                      │
  ├─────────────────────────────────────────────────────┤
  │                                                     │
  │  Communication    MCP, A2A          ✅ Solved       │
  │  Payments         x402, ACP         ✅ Solved       │
  │  Identity         OAuth, OIDC       ✅ Solved       │
  │  Permissions      RBAC, ABAC        ✅ Solved       │
  │                                                     │
  │  Trust scoring    ???               ⬚ Missing       │
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

Every layer above assumes the counterparty is trustworthy. None of them verify it. TATF fills this gap.

When your procurement agent encounters a supplier agent for the first time, MCP tells you **how** to talk to it. OAuth tells you **who** it claims to be. RBAC tells you **what** it is allowed to do.

None of them tell you **whether you should trust it with your money**.

---

## TATF vs. Traditional Approaches

| Approach | What It Does | What It Misses |
|----------|-------------|----------------|
| **OAuth / OIDC** | Verifies identity ("who are you?") | No behavioral assessment. A compromised agent with valid tokens passes. |
| **RBAC / ABAC** | Enforces permissions ("what can you do?") | No continuous trust signal. Permissions are static; behavior is dynamic. |
| **FICO-style scoring** | Credit risk from binary outcomes | Requires ground truth (default / no default). No such binary exists for agent transactions. |
| **Star ratings** | Subjective reputation aggregation | Gameable. No anomaly detection. No statistical rigor. |
| **TATF** | Behavioral trust scoring against own baseline | Protocol-agnostic. Deterministic. Relative. Auditable. |

The fundamental problem with applying traditional approaches to agent commerce: **they were designed for humans operating at human speed**. Agent commerce operates at machine speed, with machine-scale Sybil attack surfaces, and without the social context that makes human reputation systems work.

---

## The Relative Scoring Advantage

Most trust systems use **absolute thresholds**. TATF uses **relative baselines**.

Consider two agents:

```
  Agent A: High-frequency trader
  ─────────────────────────────────
  Normal hours:    24/7
  Concurrent:      50-200 sessions
  Price range:     $10K - $500K
  Categories:      12 product types
  Counterparties:  300+ unique firms

  Agent B: Boutique procurement
  ─────────────────────────────────
  Normal hours:    09:00 - 17:00
  Concurrent:      1-3 sessions
  Price range:     $500 - $2,000
  Categories:      1 product type
  Counterparties:  5 regular firms
```

Under an absolute scoring model, Agent A's normal behavior would trigger every alarm. Under TATF, both agents are scored against their own history:

- Agent A running 150 concurrent sessions at 3 AM? **Normal.** Score: 0.
- Agent B running 150 concurrent sessions at 3 AM? **Extreme anomaly.** Score: 45 + 35 + ...

This is not a design preference — it is a mathematical necessity. Without relative scoring, any global threshold will either be too permissive for conservative agents or too restrictive for aggressive ones.

---

## Protocol-Agnostic by Design

TATF sits **below** the protocol layer:

```
  ┌──────────────────────────────────────────┐
  │     Agent Protocol Layer                  │
  │     (MCP, A2A, ACP, HTTP, gRPC, ...)    │
  └──────────────────┬───────────────────────┘
                     │
  ┌──────────────────▼───────────────────────┐
  │     TATF Trust Scoring Layer              │
  │                                           │
  │  Input:  Transaction metadata             │
  │  Output: Trust score + routing decision   │
  │                                           │
  │  Does NOT care how agents communicate.    │
  │  Does NOT require network access.         │
  │  Does NOT depend on any specific protocol.│
  └───────────────────────────────────────────┘
```

This is intentional. Protocol wars come and go. Trust scoring is a permanent need. TATF integrates with whatever protocol your agents use today and whatever protocol replaces it tomorrow.

---

## Regulatory Readiness

Three regulatory frameworks are converging on agent governance:

| Framework | Timeline | TATF Alignment |
|-----------|----------|----------------|
| **EU AI Act** | August 2026 | Articles 9 (risk management), 13 (transparency), 14 (human oversight via SOFT_HOLD), 15 (accuracy) |
| **NIST AI RMF** | Active | Maps to Govern, Map, Measure, Manage functions |
| **CSA ATF** | February 2026 | ALPHA tiers map to CSA maturity levels |

The EU AI Act in particular creates a regulatory requirement for:
- **Transparent scoring** — TATF scores are deterministic and explainable
- **Human oversight** — SOFT_HOLD review queue with configurable timeout
- **Risk management** — 4-layer model with adversarial testing
- **Auditability** — Ed25519 attestations are independently verifiable

Organizations deploying autonomous agents in the EU after August 2026 will need this infrastructure. TATF provides it as an open standard rather than a vendor-locked compliance product.

---

## Summary

TATF exists because:

1. **Trust scoring is a distinct infrastructure layer** — separate from identity, authorization, and communication
2. **Relative scoring is the only model that survives adversarial manipulation at scale** — absolute thresholds are gameable
3. **The regulatory window is closing** — EU AI Act, NIST, CSA all require what TATF provides
4. **Agent commerce needs a neutral, open standard** — not a proprietary score owned by a platform

Trust infrastructure must be a public good. That is why TATF is Apache 2.0 — and will stay that way.
