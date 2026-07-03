# TATF v0.1 — Behavioral Baselines

## 1. Overview

Layer 2 of TATF measures agent trustworthiness through **behavioral
anomaly detection** — comparing an agent's current behavior against its
own established baseline. This approach eliminates the ground truth
problem: no external "correct behavior" standard is needed.

The scoring model uses six independent dimensions, each capturing a
distinct facet of agent behavior. Dimension scores are summed into a
composite anomaly score (0–200) that drives routing decisions.

---

## 2. Baseline Establishment

### Exponential Moving Average (EMA)

Agent baselines are maintained using exponential moving average to weight
recent behavior more heavily than historical:

```
baseline_new = α * observation + (1 - α) * baseline_old
```

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| α (smoothing factor) | 0.15 | Balances responsiveness with stability; ~6.2 effective observations |
| Update frequency | Per transaction | Baselines update on every scored event |

**Effective memory:** With α = 0.15, observations older than ~40
transactions contribute less than 1% to the current baseline. This
provides approximately a 4-6 week behavioral window for active agents.

### Cold-Start Period

Agents with fewer than `COLD_START_DAYS` (default: 14) days of
observation data MUST bypass behavioral scoring:

```
if agent.observation_days < COLD_START_DAYS:
    routing = AUTO_PASS
    cold_start = true
    anomaly_score = 0  (not computed)
```

**Rationale:** Insufficient data produces unreliable z-scores. Scoring
agents during cold start would generate false positives (flagging normal
behavior as anomalous due to noisy baselines).

### Default Baseline Values

New agents MUST be initialized with the following defaults:

| Parameter | Default | Rationale |
|-----------|---------|-----------|
| time_mean | 12.0 (noon) | Neutral midpoint of business hours |
| time_std | 4.0 hours | Covers typical 8AM-4PM operating window |
| concurrent_mean | 1.0 | Single session default |
| concurrent_std | 0.5 | Conservative initial variance |
| price_mean | 0.0 | No price deviation baseline |
| price_std | 1.0 | Unit variance |
| rounds_p95 | 5.0 | Typical maximum negotiation rounds |
| known_categories | [] | Empty; first category is never penalized during cold start |
| counterparty_counts | {} | Empty concentration map |

These defaults are intentionally permissive. As the agent transacts,
EMA updates converge the baseline to its actual behavior pattern.

---

## 3. Six Scoring Dimensions

Each dimension produces a sub-score with a defined cap. The composite
anomaly score is the sum, bounded to [0, 200]:

```
composite = min(200.0, s_time + s_concurrent + s_price +
                        s_category + s_rounds + s_counterparty)
```

### Z-Score Methodology

Dimensions 1-3 and 6 use z-scores to measure standard deviations from
the baseline mean. All z-scores employ an **epsilon guard** on the
denominator:

```
z = (observed_value - baseline_mean) / (baseline_std + ε)
```

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| ε (epsilon) | 0.5 | Prevents division by zero; dampens scores when std is very small |

The epsilon guard is critical: without it, an agent with a very
consistent baseline (std ≈ 0) would produce infinite z-scores on any
deviation, however minor.

---

### Dimension 1: Time Anomaly (`s_time`)

**Cap:** 35 points
**Type:** Continuous (z-score based)

Detects when an agent operates outside its normal time-of-day pattern.

```
z_time = (hour - baseline.time_mean) / (baseline.time_std + ε)
s_time = min(35.0, floor(|z_time| * 10))
```

| Agent Profile | Normal | Anomalous |
|---------------|--------|-----------|
| 9-to-5 procurement | 10:00 trade | 03:00 trade |
| 24/7 trading bot | 03:00 trade | (nothing — low std captures this) |

**Design note:** Absolute value of z-score is used because both early
and late deviations are equally suspicious. The 10x multiplier and
cap at 35 ensure this dimension contributes meaningfully but cannot
dominate the composite score.

---

### Dimension 2: Concurrent Sessions (`s_concurrent`)

**Cap:** 45 points
**Type:** Continuous (z-score based)

Detects abnormal parallel activity, which may indicate compromised
credentials or automated amplification attacks.

```
z_concurrent = (sessions - baseline.concurrent_mean) / (baseline.concurrent_std + ε)
s_concurrent = min(45.0, max(0.0, floor(z_concurrent * 15)))
```

**Note:** Only positive z-scores contribute (more sessions than normal).
Fewer sessions than normal is not considered anomalous.

**Highest cap (45)** because concurrent session spikes are the strongest
signal of credential compromise or bot amplification.

---

### Dimension 3: Price Deviation (`s_price`)

**Cap:** 40 points
**Type:** Continuous (z-score based)

Detects when an agent's pricing deviates significantly from its own
historical pattern.

```
z_price = (price - baseline.price_mean) / (baseline.price_std + ε)
s_price = min(40.0, floor(|z_price| * 12))
```

**Design note:** Both high and low deviations are scored (absolute value).
An agent suddenly offering far below market is as suspicious as far above
— it may indicate a liquidation attack or compromised decision-making.

---

### Dimension 4: Category Anomaly (`s_category`)

**Cap:** 30 points (binary)
**Type:** Binary (0 or 30)

Detects when an agent transacts in a product category it has never
operated in before.

```
s_category = 30.0 if (category not in baseline.known_categories) else 0.0
```

**Rationale:** An electronics procurement agent suddenly trading
agricultural commodities is a strong signal that something has changed —
possibly a legitimate business expansion, but worth flagging.

Once an agent transacts in a new category and passes review, that
category is added to `known_categories` and no longer triggers.

---

### Dimension 5: Negotiation Rounds (`s_rounds`)

**Cap:** 25 points (binary)
**Type:** Binary (0 or 25)

Detects when negotiation round counts exceed the agent's historical
95th percentile.

```
s_rounds = 25.0 if (rounds > baseline.rounds_p95) else 0.0
```

**Rationale:** Excessive negotiation rounds may indicate:
- Adversarial price manipulation
- Agent stuck in negotiation loop
- Counterparty probing for information

The p95 threshold is tracked via EMA (simplified as max-tracking
with decay).

---

### Dimension 6: Counterparty Concentration (`s_counterparty`)

**Cap:** 25 points
**Type:** Continuous (HHI-based)

Detects sudden shifts in counterparty diversification using the
Herfindahl-Hirschman Index (HHI).

```
HHI = Σ(c_i / total)²
    where c_i = transaction count with counterparty i

delta_hhi = |HHI_after - HHI_before|
s_counterparty = min(25.0, floor(delta_hhi * 50))
```

| HHI Value | Interpretation |
|-----------|----------------|
| 0.0 | Perfectly diversified (infinite counterparties) |
| 1.0 | Complete concentration (single counterparty) |

**Rationale:** An agent suddenly concentrating all activity on a single
counterparty may indicate collusion, dependency, or a compromised
agent funneling value to an attacker's account.

---

## 4. Dimension Summary

| # | Dimension | Cap | Type | Signal |
|---|-----------|-----|------|--------|
| 1 | Time anomaly | 35 | z-score × 10 | Operating outside normal hours |
| 2 | Concurrent sessions | 45 | z-score × 15 | Abnormal parallel activity |
| 3 | Price deviation | 40 | z-score × 12 | Unusual pricing behavior |
| 4 | Category anomaly | 30 | Binary | New product category |
| 5 | Negotiation rounds | 25 | Binary | Excessive bargaining |
| 6 | Counterparty concentration | 25 | HHI delta × 50 | Sudden relationship shift |

**Maximum possible composite:** 200 (35 + 45 + 40 + 30 + 25 + 25)

**Design rationale for caps:**
- Concurrent sessions (45) highest because credential compromise is the most dangerous scenario
- Price deviation (40) second because financial manipulation has immediate impact
- Time anomaly (35) third because it often accompanies the above two
- Category anomaly (30) signals strategic change
- Negotiation rounds (25) and counterparty concentration (25) are supporting signals

No single dimension can push the composite into HARD_BLOCK territory
alone. Multiple concurrent anomalies are required for the highest
severity routing.

---

## 5. Baseline Data Model

Implementations MUST maintain the following baseline state per agent:

```json
{
  "agent_id": "string",
  "observation_days": 0,
  "time_mean": 12.0,
  "time_std": 4.0,
  "concurrent_mean": 1.0,
  "concurrent_std": 0.5,
  "price_mean": 0.0,
  "price_std": 1.0,
  "rounds_p95": 5.0,
  "known_categories": [],
  "counterparty_counts": {},
  "first_seen": "datetime",
  "last_updated": "datetime"
}
```

### Update Rules

After each scored transaction:

1. Increment `observation_days` if calendar day differs from `last_updated`
2. Update EMA fields: `time_mean`, `time_std`, `concurrent_mean`, `concurrent_std`, `price_mean`, `price_std`
3. Update `rounds_p95` using EMA-based max tracking
4. Add new categories to `known_categories`
5. Update `counterparty_counts` map
6. Set `last_updated` to current timestamp

---

## 6. Anomaly Score Output Format

A TATF-compliant anomaly score MUST include:

```json
{
  "agent_id": "string",
  "composite": 67.0,
  "dimensions": {
    "s_time": 0.0,
    "s_concurrent": 30.0,
    "s_price": 12.0,
    "s_category": 0.0,
    "s_rounds": 25.0,
    "s_counterparty": 0.0
  },
  "routing": "SOFT_HOLD",
  "cold_start": false,
  "computed_at": "2026-03-13T14:30:00Z",
  "spec_version": "tatf-v0.1"
}
```

---

*Next: [03-anomaly-detection.md](03-anomaly-detection.md) — Anomaly Detection & ATBF Zones*
