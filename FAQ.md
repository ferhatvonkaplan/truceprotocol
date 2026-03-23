# Frequently Asked Questions

---

## General

### What is TATF?

TATF (TRUCE Agent Trust Framework) is an open standard for scoring the trustworthiness of autonomous AI agents in commercial transactions. It defines a protocol-agnostic, four-layer model for behavioral trust assessment.

### Is TATF free to use?

Yes. The specification and reference implementation are Apache 2.0 licensed. No fees, no registration, no API keys.

### What is the relationship between TATF and TRUCE?

TATF is the **open standard** — the specification that anyone can implement. TRUCE Protocol is the organization that maintains TATF and builds commercial infrastructure (TRUCE CORE) on top of it. The standard remains open regardless of what TRUCE Protocol builds commercially.

### Does TATF require a server?

No. The reference implementation (`pip install tatf`) runs entirely locally. No network calls, no external dependencies at scoring time, no data leaves your machine.

---

## Technical

### How does scoring work?

TATF monitors six behavioral dimensions in real time, comparing each observation against the agent's own historical baseline using exponential moving averages (EMA). Each dimension produces a sub-score with a defined cap. The six sub-scores sum to a composite (0-200) that maps to three routing zones:

```
0 ━━━━━━━━━━━━━ 50 ━━━━━━━━━━━━━ 120 ━━━━━━━━━━━━━ 200
   AUTO_PASS        SOFT_HOLD          HARD_BLOCK
```

On top of this, the ALPHA score (0.0-1.0) provides a composite trust signal with Wald confidence intervals.

### What is relative scoring?

Agents are scored against their **own behavioral baseline**, not a global standard. A high-frequency trading bot running 500 transactions per day has a different "normal" than a procurement agent running 3. TATF respects this — anomalies are defined relative to each agent's history.

### What is the cold-start problem?

New agents have no behavioral history. TATF handles this with two mechanisms:
- **KYA-B cold start:** 14 calendar days of data required before anomaly scoring activates. During cold start, agents receive safe default scores.
- **ALPHA cold start:** 5 observations minimum before ALPHA trust scores are computed. Until then, ALPHA returns a cold-start flag with neutral defaults.

### Can TATF be gamed?

TATF includes several anti-gaming measures:
- **Relative baselines** prevent manipulation of absolute thresholds
- **No single dimension** can trigger HARD_BLOCK alone (max single dimension: 45 out of 120 threshold)
- **Layer 4 (Adversarial Testing)** probes agents for resilience against known attack patterns
- **EMA decay** means historical manipulation has diminishing returns
- **k-anonymity** in AVX prevents gaming aggregate market metrics

No scoring system is immune to all adversarial strategies. TATF is designed to raise the cost of manipulation, not eliminate it.

### What cryptographic algorithms does TATF use?

- **Signing:** Ed25519 (EdDSA over Curve25519)
- **Hashing:** SHA-256
- **Attestation format:** TATF Native (with W3C Verifiable Credentials v2 mapping)
- **Key management:** Signing keys are generated locally; no CA or PKI required

### Does TATF work with MCP, A2A, or ACP?

Yes. TATF is protocol-agnostic by design. It scores agent **behavior**, not agent **communication**. The same scoring engine works whether agents communicate via MCP, Google A2A, OpenAI ACP, raw HTTP, or any other protocol.

### What is k-anonymity in AVX?

The Agent Volatility Index (AVX) aggregates market data from multiple firms. To prevent any single firm's behavior from being reverse-engineered from aggregate statistics, AVX is only published when at least **5 unique firms** (configurable) contribute data. If fewer firms are present, AVX returns null and ALPHA falls back to a neutral market stability assumption.

---

## Adoption

### How do I get started?

```bash
pip install tatf
```

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()
scorer.ingest("agent-123", transactions)
result = scorer.score("agent-123")
print(result.score, result.routing)
```

Five lines from install to trust score.

### What Python versions are supported?

Python 3.9 and above. The only runtime dependency is Pydantic v2. Ed25519 attestation requires the optional `PyNaCl` package (`pip install tatf[crypto]`).

### Can I contribute?

Yes. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Spec changes follow an RFC process with a 14-day community review period. Code contributions are welcome via pull request.

### Is there a commercial version?

TRUCE CORE is a commercial product that provides full clearing infrastructure for agent commerce — matching engine, escrow, webhooks, real-time dashboard, SDKs. TATF (the scoring standard) remains open and Apache 2.0 licensed regardless of commercial offerings.

---

## Regulatory

### Does TATF comply with the EU AI Act?

TATF is designed with the EU AI Act (effective August 2026) in mind. Its deterministic scoring, explainable routing decisions, and human-in-the-loop review queue (SOFT_HOLD) address requirements in Articles 9 (risk management), 13 (transparency), 14 (human oversight), and 15 (accuracy and robustness).

### What about NIST AI RMF?

TATF's four layers map to the NIST AI Risk Management Framework functions:
- **Layer 1 (Observable Metrics)** → Measure
- **Layer 2 (Behavioral Baselines)** → Measure, Manage
- **Layer 3 (Community Signals)** → Govern, Map
- **Layer 4 (Adversarial Testing)** → Manage

### Is TATF auditable?

Yes. TATF is deterministic — identical inputs produce identical outputs on every run, on every platform. There is no randomness and no external state dependency. Ed25519 attestations provide cryptographic proof that a specific score was computed for a specific input at a specific time. Any third party can independently verify both the score and the attestation.
