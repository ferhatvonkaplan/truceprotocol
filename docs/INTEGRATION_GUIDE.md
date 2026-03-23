# TATF Integration Guide

A practical guide for integrating TATF trust scoring into your agent infrastructure.

---

## Architecture Overview

```
  Your Agent System
  ─────────────────────────────────────────────────────
  ┌──────────┐     ┌──────────┐     ┌──────────────┐
  │  Agent   │────>│  TATF    │────>│  Your Logic  │
  │  Request │     │  Scorer  │     │              │
  └──────────┘     └─────┬────┘     │  AUTO_PASS → │
                         │          │    proceed    │
                   ┌─────▼────┐     │  SOFT_HOLD → │
                   │ Baseline │     │    review     │
                   │  Store   │     │  HARD_BLOCK →│
                   │ (in-mem) │     │    reject     │
                   └──────────┘     └──────────────┘
```

TATF runs **in-process**. No server, no network call, no external dependency.

---

## Step 1: Install

```bash
pip install tatf

# With attestation support:
pip install tatf[crypto]
```

Requirements: Python 3.9+, Pydantic v2.

---

## Step 2: Ingest Historical Data

Before scoring, TATF needs behavioral history to establish baselines.

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()

# Load from your database, logs, or event stream
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
```

**Important:** TATF requires 14 calendar days of history before anomaly scoring activates. During cold start, agents receive safe default scores and the `cold_start` flag is set to `True`.

**Transaction fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `timestamp` | Yes | When the transaction occurred (timezone-aware) |
| `price` | Yes | Transaction value |
| `category` | Yes | Product/service category |
| `counterparty_id` | Yes | Identifier of the other party |
| `concurrent_sessions` | No | Number of active sessions (default: 1) |
| `negotiation_rounds` | No | Number of negotiation rounds (default: 0) |

---

## Step 3: Score in Real Time

For each incoming transaction, compute an anomaly score:

```python
anomaly = scorer.compute_anomaly(
    "agent-123",
    transaction=Transaction(
        timestamp=datetime.now(timezone.utc),
        price=request.price,
        category=request.category,
        counterparty_id=request.counterparty,
        concurrent_sessions=active_session_count,
    ),
)

print(anomaly.composite)     # 0-200
print(anomaly.routing)       # AUTO_PASS, SOFT_HOLD, or HARD_BLOCK
print(anomaly.dimensions)    # Per-dimension breakdown
```

For aggregate trust assessment (not per-transaction):

```python
alpha = scorer.score("agent-123", market_stability=0.8)
print(alpha.score)           # 0.0 - 1.0
print(alpha.confidence)      # (lower, upper) Wald interval
print(alpha.tier)            # LOW, MEDIUM, or HIGH
```

---

## Step 4: Implement Routing

Map ATBF zones to your business logic:

```python
from truce import RoutingDecision

def process_transaction(agent_id: str, transaction: Transaction):
    anomaly = scorer.compute_anomaly(agent_id, transaction=transaction)

    if anomaly.routing == RoutingDecision.AUTO_PASS:
        # Score < 50: proceed normally
        execute_transaction(transaction)

    elif anomaly.routing == RoutingDecision.SOFT_HOLD:
        # Score 50-119: queue for review
        queue_for_review(
            transaction,
            anomaly_score=anomaly.composite,
            dimensions=anomaly.dimensions,
            timeout_minutes=15,  # per TATF spec
        )

    else:  # HARD_BLOCK
        # Score >= 120: reject immediately
        reject_transaction(
            transaction,
            reason="ATBF hard block",
            score=anomaly.composite,
        )
```

---

## Step 5: Market Context (Optional)

Use AVX to factor in sector-level stress:

```python
from truce import AVXCalculator, AVXEvent

avx = AVXCalculator(k_anonymity_min=5)

# Ingest events from your market data feed
for event in market_feed:
    avx.ingest(
        event.sector,
        [AVXEvent(
            firm_id=event.firm_id,
            price=event.price,
            quantity=event.quantity,
        )],
    )

# Compute sector stress
result = avx.compute("electronics")
if result:
    market_stability = 1.0 - (result.avx_score / 100.0)
else:
    market_stability = 0.5  # neutral fallback (k-anonymity not met)

# Feed into ALPHA scoring
alpha = scorer.score("agent-123", market_stability=market_stability)
```

---

## Step 6: Attestation (Optional)

Generate verifiable proof of trust scores:

```python
from truce import TATFAttestor

attestor = TATFAttestor(issuer_id="my-scoring-node")

alpha = scorer.score("agent-123")
anomaly = scorer.compute_anomaly("agent-123")

# Generate Ed25519-signed attestation
attestation = attestor.attest(alpha, anomaly)

# Verify (any party with the public key can do this)
assert attestor.verify(attestation)

# Share public key for third-party verification
print(attestor.public_key_hex)
```

---

## Common Integration Patterns

### Gateway Pattern

Score **before** routing to the order book. Blocking. Simplest to implement.

```
  Request → TATF Score → Route → Order Book
```

Best for: systems where latency is acceptable and every transaction must be scored.

### Sidecar Pattern

Score **in parallel** with transaction processing. Non-blocking. Score is logged and available for audit, but does not gate the transaction in real time.

```
  Request → Order Book
      └───→ TATF Score → Log + Alert
```

Best for: high-throughput systems where you want observability without latency impact. Use alerting to catch anomalies after the fact.

### Batch Scoring Pattern

Recalculate trust scores **periodically** (e.g., nightly). No per-transaction overhead.

```
  Nightly Job → Load History → Score All Agents → Update Trust Table
```

Best for: portfolio-level risk assessment, regulatory reporting, periodic review.

---

## Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| `ingest()` | O(n) | One-time per agent; processes n transactions |
| `compute_anomaly()` | O(1) | Constant time per transaction |
| `score()` | O(1) | Constant time per agent |
| `avx.compute()` | O(k) | k = number of unique firms in sector |

- No external dependencies at scoring time
- No network calls
- No disk I/O
- Thread-safe for concurrent scoring of different agents
- Memory: ~1KB per agent baseline

---

## Next Steps

- Read the [TATF v0.1 specification](../spec/v0.1/) for full technical details
- Run the [examples](../examples/) to see scoring in action
- Try the [benchmarks](../benchmarks/) to evaluate accuracy on synthetic data
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to get involved
