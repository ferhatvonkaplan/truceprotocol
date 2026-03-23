
```
  ████████╗██████╗ ██╗   ██╗ ██████╗███████╗
  ╚══██╔══╝██╔══██╗██║   ██║██╔════╝██╔════╝
     ██║   ██████╔╝██║   ██║██║     █████╗
     ██║   ██╔══██╗██║   ██║██║     ██╔══╝
     ██║   ██║  ██║╚██████╔╝╚██████╗███████╗
     ╚═╝   ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝
          AGENT  TRUST  FRAMEWORK
```

<p align="center">
  <strong>An open standard for scoring the trustworthiness of autonomous AI agents.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <a href="spec/v0.1/"><img src="https://img.shields.io/badge/spec-TATF_v0.1-8b5cf6.svg" alt="Spec Version"></a>
  <a href="https://pypi.org/project/tatf/"><img src="https://img.shields.io/pypi/v/tatf?color=8b5cf6&label=PyPI" alt="PyPI"></a>
  <a href="https://github.com/ferhatvonkaplan/truceprotocol/actions"><img src="https://github.com/ferhatvonkaplan/truceprotocol/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="benchmarks/"><img src="https://img.shields.io/badge/benchmark-97%25_accuracy-brightgreen.svg" alt="Benchmark"></a>
</p>

---

## The Problem

MCP solved agent communication. x402 solved agent payments. But neither answers the question that matters when money is on the line:

> **"Should I trust this agent to fulfill THIS specific transaction?"**

TATF answers that question — protocol-agnostically, deterministically, and without a central authority.

---

## How It Works

```
                  ┌─────────────────────────────────────────┐
                  │           TATF  SCORING  MODEL          │
                  ├─────────────────────────────────────────┤
                  │                                         │
                  │  Layer 4   ADVERSARIAL TESTING          │  Optional
                  │  ─────────────────────────────────────  │
                  │  Layer 3   COMMUNITY SIGNALS            │  Recommended
                  │  ─────────────────────────────────────  │
                  │  Layer 2   BEHAVIORAL BASELINES  ◄──────│─── EMA, 6 dimensions
                  │  ─────────────────────────────────────  │
                  │  Layer 1   OBSERVABLE METRICS    ◄──────│─── Hard numbers
                  │                                         │
                  └────────────────┬────────────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────────────┐
                  │         ALPHA  TRUST  SCORE             │
                  │                                         │
                  │   Score: 0.0 ─────────────────── 1.0    │
                  │   Confidence: Wald interval             │
                  │   Tier: LOW / MEDIUM / HIGH             │
                  └────────────────┬────────────────────────┘
                                   │
                  ┌────────────────┼────────────────────────┐
                  │                │                        │
                  ▼                ▼                        ▼
           ┌──────────┐   ┌──────────────┐         ┌────────────┐
           │AUTO_PASS │   │  SOFT_HOLD   │         │ HARD_BLOCK │
           │  < 50    │   │   50 - 119   │         │   ≥ 120    │
           └──────────┘   └──────────────┘         └────────────┘
```

**Key insight:** Agents are scored against their **own behavioral baseline** — not a global standard. A 24/7 trading bot and a 9-to-5 procurement agent have different normals. TATF respects that.

---

## Quick Start

```bash
pip install tatf
```

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()

# Ingest 30 days of transaction history
transactions = [
    Transaction(
        timestamp=datetime(2026, 1, i, 10, 0, tzinfo=timezone.utc),
        price=1000.0,
        category="electronics",
        counterparty_id=f"cp-{i % 10:03d}",
    )
    for i in range(1, 31)
]
scorer.ingest("agent-123", transactions)

# Score the agent
result = scorer.score("agent-123", market_stability=0.8)
print(result.score)        # 0.7925
print(result.routing)      # AUTO_PASS
print(result.confidence)   # (0.6795, 0.9055)
```

Detect anomalies in real time:

```python
suspicious = scorer.compute_anomaly(
    "agent-123",
    transaction=Transaction(
        timestamp=datetime(2026, 2, 1, 3, 0, tzinfo=timezone.utc),  # 3 AM
        price=50000.0,          # 50x normal
        category="agriculture", # never seen before
        counterparty_id="cp-999",
        concurrent_sessions=28,
    ),
)
print(suspicious.routing)     # HARD_BLOCK
print(suspicious.composite)   # 150+
print(suspicious.dimensions)  # Per-dimension breakdown
```

---

## Six Scoring Dimensions

```
  Dimension                  Cap    Signal
  ──────────────────────────────────────────────────────
  1. Time anomaly             35    Operating outside normal hours
  2. Concurrent sessions      45    Abnormal parallel activity
  3. Price deviation          40    Unusual pricing behavior
  4. Category anomaly         30    New product category
  5. Negotiation rounds       25    Excessive bargaining
  6. Counterparty conc.       25    Sudden relationship shift
  ──────────────────────────────────────────────────────
  Composite range: 0 - 200

  0 ━━━━━━━━━━━━━ 50 ━━━━━━━━━━━━━ 120 ━━━━━━━━━━━━━ 200
     AUTO_PASS        SOFT_HOLD          HARD_BLOCK
```

No single dimension can trigger HARD_BLOCK alone.

---

## Market Stress (AVX)

The Agent Volatility Index measures sector-level stress with **k-anonymity** protection:

```python
from truce import AVXCalculator, AVXEvent

avx = AVXCalculator(k_anonymity_min=5)

events = [
    AVXEvent(firm_id=f"FIRM-{i}", price=100 + i, quantity=50)
    for i in range(10)
]
avx.ingest("electronics", events)

result = avx.compute("electronics")
print(result.avx_score)              # 0-100 stress level
print(result.dimensions.pd_score)    # Panic Diversification
print(result.dimensions.pv_score)    # Price Volatility
```

Four dimensions: **PD** (0.40) | **PV** (0.30) | **DA** (0.20) | **CR** (0.10)

AVX is only published when **≥ 5 unique firms** contribute data.

---

## Specification

| # | Document | Description |
|---|----------|-------------|
| 00 | [Introduction](spec/v0.1/00-introduction.md) | Motivation, scope, terminology |
| 01 | [Scoring Model](spec/v0.1/01-scoring-model.md) | ALPHA composite score, four-layer model |
| 02 | [Behavioral Baselines](spec/v0.1/02-behavioral-baselines.md) | EMA baselines, six scoring dimensions |
| 03 | [Anomaly Detection](spec/v0.1/03-anomaly-detection.md) | ATBF zones, routing, review queue |
| 04 | [Trust Attestation](spec/v0.1/04-trust-attestation.md) | Ed25519 signing, W3C VC mapping |
| 05 | [Adversarial Testing](spec/v0.1/05-adversarial-testing.md) | Resilience evaluation |
| 06 | [Market Stress](spec/v0.1/06-market-stress.md) | AVX indicator, k-anonymity |

---

## Benchmarks

```
  1,000 synthetic agents  ·  97,370 transactions  ·  5 archetypes  ·  97% accuracy

  Archetype        Count    Accuracy    Routing Distribution
  ─────────────────────────────────────────────────────────────
  normal            500      99.8%      AUTO_PASS
  cautious          100     100.0%      AUTO_PASS
  volatile          224      92.4%      AUTO_PASS / SOFT_HOLD
  anomalous         117      91.5%      SOFT_HOLD / HARD_BLOCK
  cold_start         59     100.0%      AUTO_PASS (cold-start fallback)
```

Generate your own:
```bash
cd benchmarks
python generate_benchmark.py --agents 1000
python evaluate.py --dataset datasets/benchmark_v0.1.jsonl --verbose
```

---

## Regulatory Alignment

| Regulation | TATF Coverage |
|-----------|---------------|
| **EU AI Act** (Aug 2026) | Trust scoring for high-risk AI agent supervision |
| **NIST AI RMF** | Maps to Govern, Map, Measure, Manage functions |
| **ISO/IEC 42001** | AI management system requirements |
| **CSA ATF** (Feb 2026) | Agentic Trust Framework maturity levels |

---

## Design Principles

- **Protocol-agnostic** — works with MCP, A2A, ACP, or any agent protocol
- **Relative scoring** — agents scored against their OWN baseline
- **Privacy-preserving** — k-anonymity on aggregate metrics
- **Incrementally adoptable** — implement layers independently
- **Deterministic** — same inputs, same output, every time
- **Apache 2.0, forever** — trust infrastructure must be a public good

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md).

Significant changes follow an [RFC process](CONTRIBUTING.md#rfc-format) with a 14-day community review period.

---

## License

- **Specification:** [Apache 2.0](LICENSE)
- **Documentation:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

---

<p align="center">
  <em>Trust is the missing layer in agent commerce. TATF is the open standard.</em>
</p>
