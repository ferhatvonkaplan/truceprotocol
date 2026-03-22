# truce

**TATF reference implementation — local agent trust scoring.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-TATF_v0.1-orange.svg)](https://github.com/truceprotocol/tatf)
[![Tests](https://img.shields.io/badge/tests-44_passed-green.svg)]()

Score autonomous agents locally using the [TRUCE Agent Trust Framework (TATF)](https://github.com/truceprotocol/tatf) — no server required.

## Install

```bash
pip install truce

# With Ed25519 attestation signing:
pip install truce[crypto]
```

## Quick Start

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()

# Ingest transaction history
transactions = [
    Transaction(
        timestamp=datetime(2026, 1, i, 10, 0, tzinfo=timezone.utc),
        price=1000.0,
        category="electronics",
        counterparty_id=f"cp-{i % 10:03d}",
    )
    for i in range(1, 31)  # 30 days of history
]

scorer.ingest("agent-123", transactions)

# Score the agent
result = scorer.score("agent-123", market_stability=0.8)

print(result.score)        # 0.7925
print(result.routing)      # AUTO_PASS
print(result.confidence)   # (0.6795, 0.9055)
print(result.tier)         # HIGH
print(result.cold_start)   # False
```

## Anomaly Detection

Score a new transaction against the agent's behavioral baseline:

```python
from truce import RoutingDecision

# Normal transaction
normal = scorer.compute_anomaly(
    "agent-123",
    transaction=Transaction(
        timestamp=datetime(2026, 2, 1, 11, 0, tzinfo=timezone.utc),
        price=1050.0,
        category="electronics",
        counterparty_id="cp-001",
    ),
)
assert normal.routing == RoutingDecision.AUTO_PASS

# Suspicious transaction (3 AM, new category, extreme price)
suspicious = scorer.compute_anomaly(
    "agent-123",
    transaction=Transaction(
        timestamp=datetime(2026, 2, 1, 3, 0, tzinfo=timezone.utc),
        price=50000.0,
        category="agriculture",
        counterparty_id="cp-999",
        concurrent_sessions=10,
    ),
)
print(suspicious.routing)    # SOFT_HOLD or HARD_BLOCK
print(suspicious.composite)  # Anomaly score (0-200)
print(suspicious.dimensions) # Per-dimension breakdown
```

## Market Stress (AVX)

```python
from truce import AVXCalculator, AVXEvent

avx = AVXCalculator(k_anonymity_min=5)

# Ingest market events from multiple firms
events = [
    AVXEvent(firm_id=f"FIRM-{i}", price=100 + i, quantity=50)
    for i in range(10)
]
avx.ingest("electronics", events)

result = avx.compute("electronics")
if result:  # None if k-anonymity not satisfied
    print(result.avx_score)             # 0-100 stress level
    print(result.dimensions.pd_score)   # Panic Diversification
    print(result.dimensions.pv_score)   # Price Volatility
```

## Trust Attestations

```python
from truce import TATFAttestor

attestor = TATFAttestor(issuer_id="my-scorer")

alpha = scorer.score("agent-123")
anomaly = scorer.compute_anomaly("agent-123")

attestation = attestor.attest(alpha, anomaly)
# Returns a signed TATF Native attestation (spec §04)

# Verify
assert attestor.verify(attestation)  # requires truce[crypto]
```

## Six Scoring Dimensions

TATF scores agents across six behavioral dimensions:

| # | Dimension | Cap | Signal |
|---|-----------|-----|--------|
| 1 | Time anomaly | 35 | Operating outside normal hours |
| 2 | Concurrent sessions | 45 | Abnormal parallel activity |
| 3 | Price deviation | 40 | Unusual pricing behavior |
| 4 | Category anomaly | 30 | New product category |
| 5 | Negotiation rounds | 25 | Excessive bargaining |
| 6 | Counterparty concentration | 25 | Sudden relationship shift |

**Composite range:** 0-200. **Routing:** AUTO_PASS (<50), SOFT_HOLD (50-119), HARD_BLOCK (>=120).

No single dimension can trigger HARD_BLOCK alone.

## Specification

This library implements [TATF v0.1](https://github.com/truceprotocol/tatf):

- Protocol-agnostic (works with A2A, ACP, MCP, or any agent protocol)
- Relative scoring (agents scored against their OWN baseline)
- Privacy-preserving (k-anonymity on aggregate metrics)
- Incrementally adoptable (implement layers independently)

## License

Apache 2.0
