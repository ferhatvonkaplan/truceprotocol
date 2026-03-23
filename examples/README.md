# TATF Examples

Runnable examples for the TATF reference implementation. All examples work with:

```bash
pip install tatf
# For attestation examples:
pip install tatf[crypto]
```

---

## 1. Basic Scoring

Score an agent based on 30 days of transaction history.

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()

# Build 30 days of normal trading history
transactions = [
    Transaction(
        timestamp=datetime(2026, 1, i, 10, 0, tzinfo=timezone.utc),
        price=1000.0 + (i * 5),       # slight upward trend
        category="electronics",
        counterparty_id=f"cp-{i % 10:03d}",
    )
    for i in range(1, 31)
]

scorer.ingest("agent-alpha", transactions)

# Compute ALPHA trust score
result = scorer.score("agent-alpha", market_stability=0.8)

print(f"Trust score:  {result.score:.4f}")
print(f"Routing:      {result.routing}")
print(f"Confidence:   ({result.confidence[0]:.4f}, {result.confidence[1]:.4f})")
print(f"Tier:         {result.tier}")
print(f"Cold start:   {result.cold_start}")
```

**Expected output:**
```
Trust score:  0.7925
Routing:      AUTO_PASS
Confidence:   (0.6795, 0.9055)
Tier:         HIGH
Cold start:   False
```

---

## 2. Real-Time Anomaly Detection

Detect suspicious behavior against an agent's baseline.

```python
from truce import TATFScorer, Transaction, RoutingDecision
from datetime import datetime, timezone

scorer = TATFScorer()

# Establish baseline (normal business hours, consistent pricing)
baseline_txns = [
    Transaction(
        timestamp=datetime(2026, 1, i, 14, 0, tzinfo=timezone.utc),
        price=500.0,
        category="textiles",
        counterparty_id=f"cp-{i % 5:03d}",
    )
    for i in range(1, 31)
]
scorer.ingest("agent-bravo", baseline_txns)

# Normal transaction — should pass
normal = scorer.compute_anomaly(
    "agent-bravo",
    transaction=Transaction(
        timestamp=datetime(2026, 2, 1, 15, 0, tzinfo=timezone.utc),
        price=520.0,
        category="textiles",
        counterparty_id="cp-002",
    ),
)
print(f"Normal:     composite={normal.composite:.1f}, routing={normal.routing}")
assert normal.routing == RoutingDecision.AUTO_PASS

# Suspicious transaction — 3 AM, 100x price, new category, new counterparty
suspicious = scorer.compute_anomaly(
    "agent-bravo",
    transaction=Transaction(
        timestamp=datetime(2026, 2, 1, 3, 0, tzinfo=timezone.utc),
        price=50000.0,
        category="agriculture",
        counterparty_id="cp-999",
        concurrent_sessions=20,
    ),
)
print(f"Suspicious: composite={suspicious.composite:.1f}, routing={suspicious.routing}")
print(f"  s_time:         {suspicious.dimensions.s_time:.1f} / 35")
print(f"  s_concurrent:   {suspicious.dimensions.s_concurrent:.1f} / 45")
print(f"  s_price:        {suspicious.dimensions.s_price:.1f} / 40")
print(f"  s_category:     {suspicious.dimensions.s_category:.1f} / 30")
print(f"  s_counterparty: {suspicious.dimensions.s_counterparty:.1f} / 25")
```

---

## 3. Market Stress Monitoring (AVX)

Compute sector-level stress with k-anonymity protection.

```python
from truce import AVXCalculator, AVXEvent

avx = AVXCalculator(k_anonymity_min=5)

# Healthy market — 10 diversified firms, stable prices
healthy_events = [
    AVXEvent(firm_id=f"FIRM-{i}", price=100.0 + i, quantity=50)
    for i in range(10)
]
avx.ingest("electronics", healthy_events)

result = avx.compute("electronics")
if result:
    print(f"AVX Score:    {result.avx_score:.1f} / 100")
    print(f"  PD (panic):   {result.dimensions.pd_score:.1f}")
    print(f"  PV (price):   {result.dimensions.pv_score:.1f}")
    print(f"  DA (demand):  {result.dimensions.da_score:.1f}")
    print(f"  CR (cancel):  {result.dimensions.cr_score:.1f}")

# Stressed market — 2 firms dominate, high price variance
avx_stressed = AVXCalculator(k_anonymity_min=5)
stressed_events = []
for i in range(5):
    qty = 500 if i < 2 else 10  # 2 firms dominate volume
    price = 100.0 * (1 + i * 0.3)  # wide price spread
    stressed_events.append(AVXEvent(firm_id=f"FIRM-{i}", price=price, quantity=qty))
avx_stressed.ingest("commodities", stressed_events)

stressed = avx_stressed.compute("commodities")
if stressed:
    print(f"\nStressed AVX: {stressed.avx_score:.1f} / 100")

# k-anonymity gate — fewer than 5 firms returns None
avx_small = AVXCalculator(k_anonymity_min=5)
avx_small.ingest("niche", [AVXEvent(firm_id="FIRM-1", price=100, quantity=10)])
assert avx_small.compute("niche") is None  # suppressed
print("\nk-anonymity: sector with 1 firm correctly suppressed")
```

---

## 4. Trust Attestation

Generate and verify Ed25519 signed trust attestations.

```python
from truce import TATFScorer, TATFAttestor, Transaction
from datetime import datetime, timezone

# Score an agent
scorer = TATFScorer()
transactions = [
    Transaction(
        timestamp=datetime(2026, 1, i, 12, 0, tzinfo=timezone.utc),
        price=200.0,
        category="chemicals",
        counterparty_id=f"cp-{i % 8:03d}",
    )
    for i in range(1, 31)
]
scorer.ingest("agent-charlie", transactions)
alpha = scorer.score("agent-charlie")
anomaly = scorer.compute_anomaly("agent-charlie")

# Generate attestation (requires: pip install tatf[crypto])
attestor = TATFAttestor(issuer_id="my-scoring-node")
attestation = attestor.attest(alpha, anomaly)

print(f"Attestation format:  {attestation['format']}")
print(f"Issuer:              {attestation['issuer_id']}")
print(f"Spec version:        {attestation['spec_version']}")
print(f"Signature present:   {'signature' in attestation}")

# Verify the attestation
is_valid = attestor.verify(attestation)
print(f"Verification:        {'PASSED' if is_valid else 'FAILED'}")

# Public key for third-party verification
print(f"Public key (hex):    {attestor.public_key_hex[:32]}...")
```

---

## 5. MCP Integration Pattern (Conceptual)

How TATF scoring fits into an MCP tool server architecture.

```python
"""
Conceptual example — shows the pattern for integrating TATF
scoring into an MCP-based agent communication workflow.

This is NOT a runnable MCP server. It demonstrates where
TATF fits in the request processing pipeline.
"""

from truce import TATFScorer, Transaction, RoutingDecision
from datetime import datetime, timezone

# Initialize scorer (once, at server startup)
scorer = TATFScorer()

def handle_agent_request(agent_id: str, request: dict) -> dict:
    """
    MCP tool handler pattern:
    1. Extract transaction parameters from MCP request
    2. Score the agent against its behavioral baseline
    3. Route based on ATBF zone
    """

    # Step 1: Build transaction from MCP request
    transaction = Transaction(
        timestamp=datetime.now(timezone.utc),
        price=request.get("price", 0.0),
        category=request.get("category", "unknown"),
        counterparty_id=request.get("counterparty", "unknown"),
        concurrent_sessions=request.get("active_sessions", 1),
    )

    # Step 2: Score
    anomaly = scorer.compute_anomaly(agent_id, transaction=transaction)

    # Step 3: Route
    if anomaly.routing == RoutingDecision.AUTO_PASS:
        return {"status": "approved", "score": anomaly.composite}

    elif anomaly.routing == RoutingDecision.SOFT_HOLD:
        # Queue for human review (15-min timeout per TATF spec)
        return {"status": "pending_review", "score": anomaly.composite}

    else:  # HARD_BLOCK
        return {"status": "rejected", "score": anomaly.composite}
```

---

## 6. Multi-Agent Portfolio

Score multiple agents and identify the riskiest one.

```python
from truce import TATFScorer, Transaction
from datetime import datetime, timezone

scorer = TATFScorer()

# Three agents with different behavioral profiles
agents = {
    "agent-reliable": {
        "hour": 10, "price": 500, "category": "electronics",
        "counterparties": 8, "description": "Steady trader"
    },
    "agent-volatile": {
        "hour": 16, "price": 2000, "category": "commodities",
        "counterparties": 3, "description": "Concentrated exposure"
    },
    "agent-new": {
        "hour": 12, "price": 100, "category": "textiles",
        "counterparties": 5, "description": "New agent (cold start)"
    },
}

# Ingest history for each agent
for agent_id, profile in agents.items():
    days = 30 if agent_id != "agent-new" else 5  # new agent has limited history
    transactions = [
        Transaction(
            timestamp=datetime(2026, 1, i, profile["hour"], 0, tzinfo=timezone.utc),
            price=profile["price"] + (i * 2),
            category=profile["category"],
            counterparty_id=f"cp-{i % profile['counterparties']:03d}",
        )
        for i in range(1, days + 1)
    ]
    scorer.ingest(agent_id, transactions)

# Score all agents
print(f"{'Agent':<20} {'Score':>6} {'Routing':<12} {'Tier':<8} {'Cold Start'}")
print("─" * 65)

scores = {}
for agent_id, profile in agents.items():
    result = scorer.score(agent_id, market_stability=0.7)
    scores[agent_id] = result
    print(
        f"{agent_id:<20} {result.score:>6.4f} {str(result.routing):<12} "
        f"{str(result.tier):<8} {result.cold_start}"
    )

# Identify riskiest agent (lowest score, excluding cold-start)
active_agents = {k: v for k, v in scores.items() if not v.cold_start}
if active_agents:
    riskiest = min(active_agents, key=lambda k: active_agents[k].score)
    print(f"\nRiskiest active agent: {riskiest} (score: {scores[riskiest].score:.4f})")
```
