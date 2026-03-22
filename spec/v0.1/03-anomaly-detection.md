# TATF v0.1 — Anomaly Detection & ATBF Zones

## 1. Anomaly-Triggered Behavioral Fencing (ATBF)

ATBF is the routing mechanism that translates behavioral anomaly scores
into concrete actions. When an agent's composite anomaly score exceeds
defined thresholds, ATBF "fences" the agent's transactions into
appropriate review paths.

### Zone Definitions

The composite anomaly score (0–200) maps to three zones:

```
                 0                50               120              200
                 ├────────────────┼─────────────────┼────────────────┤
                   AUTO_PASS          SOFT_HOLD         HARD_BLOCK
                  (proceed)         (review queue)     (reject)
```

| Zone | Score Range | Action | Rationale |
|------|-------------|--------|-----------|
| **AUTO_PASS** | composite < 50 | Transaction proceeds to order book | Agent behavior within normal parameters |
| **SOFT_HOLD** | 50 ≤ composite < 120 | Transaction held for human review | Anomalies detected but not severe enough for automatic rejection |
| **HARD_BLOCK** | composite ≥ 120 | Transaction rejected immediately | Multiple severe anomalies indicate high-risk behavior |

### Threshold Design Rationale

**AUTO_PASS ceiling (50):** Allows up to ~1.5 standard deviations of
combined anomaly before triggering review. A single moderate anomaly
(e.g., slightly unusual time + minor price deviation) passes through.

**SOFT_HOLD ceiling (120):** Requires multiple significant anomalies
to reach HARD_BLOCK. Since the maximum composite is 200, a score of
120 requires substantial deviation across multiple dimensions — not a
single outlier event.

**Key property:** No single dimension can push an agent into HARD_BLOCK
(max single dimension = 45). At least three concurrent anomalies are
needed. This prevents false positives from isolated events.

### Threshold Customization

Implementations MAY adjust zone thresholds based on risk appetite:

| Profile | AUTO_PASS | SOFT_HOLD | HARD_BLOCK |
|---------|-----------|-----------|------------|
| Conservative | < 30 | 30–90 | ≥ 90 |
| **Standard (default)** | **< 50** | **50–119** | **≥ 120** |
| Permissive | < 80 | 80–150 | ≥ 150 |

When customizing thresholds:
- AUTO_PASS ceiling MUST be > 0
- HARD_BLOCK floor MUST be > AUTO_PASS ceiling
- The gap (SOFT_HOLD range) SHOULD be at least 40 points wide

---

## 2. SOFT_HOLD Review Queue

Transactions routed to SOFT_HOLD enter a time-bounded review queue.

### Queue Lifecycle

```
Transaction submitted
        │
        ▼
  ┌─────────────┐
  │  SOFT_HOLD   │◄── anomaly score 50-119
  │   PENDING    │
  └──────┬───────┘
         │
    ┌────┼────┐
    │    │    │
    ▼    ▼    ▼
APPROVED REJECTED TIMED_OUT
    │         │       │
    ▼         ▼       ▼
 Order    Cancelled  Depends on
  Book              timeout_behavior
```

### Timeout Behavior

Review items MUST have a configurable timeout (default: 15 minutes).
When a review item times out, the behavior depends on configuration:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **fail_open** (default) | Auto-release to order book | High-throughput environments where false holds are costly |
| **fail_closed** | Auto-HARD_BLOCK | High-security environments where unreviewed transactions are unacceptable |

### Review Item Data Model

```json
{
  "review_id": "REV-{12-hex}",
  "offer_id": "string",
  "agent_id": "string",
  "firm_id": "string",
  "anomaly_score": 67.0,
  "anomaly_dimensions": {
    "s_time": 0.0,
    "s_concurrent": 30.0,
    "s_price": 12.0,
    "s_category": 0.0,
    "s_rounds": 25.0,
    "s_counterparty": 0.0
  },
  "routing": "SOFT_HOLD",
  "status": "PENDING",
  "queued_at": "2026-03-13T14:30:00Z",
  "expires_at": "2026-03-13T14:45:00Z",
  "reviewed_at": null,
  "reviewer_note": null
}
```

### Review Queue Requirements

Implementations MUST:
- Persist review items durably (survive process restart)
- Track timeout expiration per item
- Support `approve`, `reject`, and `list` operations
- Include full anomaly score breakdown to assist reviewer decision

Implementations SHOULD:
- Alert reviewers when queue depth exceeds thresholds
- Track review latency metrics
- Provide anomaly dimension visualization to reviewers

---

## 3. Cold-Start Bypass

During the cold-start period, agents MUST bypass ATBF scoring entirely:

```
if observation_days < COLD_START_DAYS:
    routing = AUTO_PASS
    cold_start = true
    # No anomaly score computed
```

**Rationale:** Scoring with insufficient baseline data produces
unreliable z-scores. Better to let agents transact freely during
cold start (with other controls) than to generate false anomalies.

**Post-cold-start transition:** After cold start ends, the agent's
first scored transaction uses the accumulated baseline data from the
cold-start period. There is no discontinuity — the EMA baseline has
been updating during cold start, it simply wasn't used for scoring.

### Cold-Start Configuration

| Parameter | Default | Range |
|-----------|---------|-------|
| COLD_START_DAYS | 14 | 7–30 |

Shorter cold-start periods increase false positive risk.
Longer periods delay anomaly detection capability.

---

## 4. Scoring Edge Cases

### New Category During Cold Start

When an agent transacts in a new category during cold start:
- The category is added to `known_categories`
- No penalty is applied (cold start bypass)
- Post-cold-start, the category is already "known"

### Agent with Zero Standard Deviation

An agent that always transacts at exactly the same time would have
`time_std ≈ 0`. The epsilon guard (ε = 0.5) prevents division by zero:

```
z = (hour - mean) / (0.0 + 0.5) = (hour - mean) / 0.5
```

Any deviation from the mean produces a z-score, but the 0.5 floor
dampens it to a reasonable range. A 2-hour deviation yields z = 4,
producing `s_time = min(35, floor(4 * 10)) = 35`.

### Counterparty Concentration with Single Trade

On an agent's first trade, HHI = 1.0 (complete concentration on one
counterparty). After the second trade:
- Same counterparty: HHI = 1.0, delta = 0.0 → no score
- Different counterparty: HHI = 0.5, delta = 0.5 → `s_counterparty = min(25, floor(0.5 * 50)) = 25`

This is expected. The first few trades will naturally produce HHI
swings. The cold-start bypass prevents these from triggering ATBF.

---

## 5. Multi-Transaction Anomaly Patterns

ATBF is designed to detect these common attack patterns:

### Credential Compromise
```
s_time: 35 (3 AM transaction)
s_concurrent: 45 (20 parallel sessions)
s_price: 0 (normal pricing)
s_category: 30 (new category)
Total: 110 → SOFT_HOLD
```

### Price Manipulation
```
s_time: 0 (normal hours)
s_concurrent: 0 (normal sessions)
s_price: 40 (extreme price deviation)
s_rounds: 25 (excessive negotiation)
s_counterparty: 25 (single counterparty)
Total: 90 → SOFT_HOLD
```

### Full Account Takeover
```
s_time: 35 (abnormal time)
s_concurrent: 45 (session flood)
s_price: 40 (wild pricing)
s_category: 30 (new categories)
s_rounds: 25 (unusual negotiation)
s_counterparty: 25 (funneling to single party)
Total: 200 → HARD_BLOCK
```

---

## 6. Implementation Checklist

A TATF-conformant ATBF implementation MUST:

- [ ] Compute all six dimensions per the formulas in [02-behavioral-baselines.md](02-behavioral-baselines.md)
- [ ] Apply epsilon guard (ε = 0.5) on all z-score denominators
- [ ] Cap each dimension at its defined maximum
- [ ] Sum dimensions into composite, bounded to [0, 200]
- [ ] Route to correct ATBF zone based on composite score
- [ ] Implement SOFT_HOLD review queue with configurable timeout
- [ ] Bypass scoring during cold-start period
- [ ] Update baselines via EMA after each scored transaction
- [ ] Include full dimension breakdown in output

---

*Next: [04-trust-attestation.md](04-trust-attestation.md) — Trust Attestation Format*
