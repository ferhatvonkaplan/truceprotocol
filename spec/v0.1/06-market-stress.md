# TATF v0.1 — Market Stress Indicator (AVX)

## 1. Overview

The Agent Volatility Index (AVX) is a sector-level aggregate stress
indicator that measures market conditions in the agent economy. AVX
feeds into the ALPHA composite score as the Market Stability (MS)
component.

Unlike agent-level scoring, AVX operates at the **market level** —
it answers "how stressed is this sector right now?" rather than
"how trustworthy is this agent?"

---

## 2. Design Principles

### Why Sector-Level?

Individual agent anomalies are captured by KYA-B scoring (Layer 2).
But some conditions affect all agents in a sector simultaneously:

- A supply chain disruption triggers mass renegotiations
- A regulatory announcement causes sudden demand shifts
- A platform outage forces agents to alternate channels

AVX detects these systemic conditions. When AVX is high, even
well-behaved agents may exhibit anomalous patterns — so the ALPHA
score accounts for market context.

### Privacy by Design

AVX aggregates data from multiple firms. To prevent reverse-engineering
individual firm behavior from aggregate statistics, AVX enforces
**k-anonymity**: the index is only published when enough unique firms
contribute events to prevent identification.

---

## 3. Four-Dimension Stress Model

```
AVX = min(100.0, w_PD * PD + w_PV * PV + w_DA * DA + w_CR * CR)
```

| Dimension | Weight | Range | Signal |
|-----------|--------|-------|--------|
| **PD** (Panic Diversification) | 0.40 | [0, 100] | Event source concentration |
| **PV** (Price Volatility) | 0.30 | [0, 100] | Price instability |
| **DA** (Demand Acceleration) | 0.20 | [0, 100] | Demand surge/cliff |
| **CR** (Cancellation Rate) | 0.10 | [0, 100] | Transaction abandonment |

Weights MUST sum to 1.0. The final score is bounded to [0, 100].

### Weight Rationale

- **PD (0.40):** Highest weight because source concentration is the most
  reliable early indicator of market stress. When few firms dominate event
  flow, it signals either market dominance or mass exit by other participants.

- **PV (0.30):** Price instability directly impacts transaction success.
  High volatility increases the risk that mid-transaction price shifts
  invalidate negotiated terms.

- **DA (0.20):** Demand acceleration captures momentum shifts. A 2x demand
  spike may indicate legitimate growth or speculative activity.

- **CR (0.10):** Lowest weight because cancellations have many benign
  explanations. But sustained elevated cancellation rates are a meaningful
  secondary signal.

---

## 4. Dimension Formulas

### PD — Panic Diversification

Measures event source concentration using the Herfindahl-Hirschman Index:

```
firm_counts = {firm_id: count_of_events}
N = number of unique firms
total = sum of all counts

HHI = Σ(count_i / total)²

// Normalize to [0, 1]
HHI_min = 1 / N
HHI_normalized = (HHI - HHI_min) / (1 - HHI_min)

PD = min(100, max(0, HHI_normalized * 100))
```

**Edge case:** N ≤ 1 → PD = 100.0 (maximum concentration)

| HHI_normalized | PD Score | Interpretation |
|----------------|----------|----------------|
| 0.0 | 0 | Perfectly diversified |
| 0.5 | 50 | Moderate concentration |
| 1.0 | 100 | Complete monopoly |

### PV — Price Volatility

Measures price instability using the coefficient of variation:

```
CV = stdev(prices) / mean(prices)
PV = min(100, CV * 200)
```

**Edge case:** < 2 prices or mean = 0 → PV = 0.0

| CV | PV Score | Interpretation |
|----|----------|----------------|
| 0.0 | 0 | No price variation |
| 0.25 | 50 | Moderate volatility |
| 0.50+ | 100 | Extreme volatility |

**Scaling factor (200):** A CV of 0.5 (standard deviation is half the mean)
is considered extreme in most commercial contexts, hence maps to PV = 100.

### DA — Demand Acceleration

Measures the ratio of current-window demand to prior-window demand:

```
current_demand = Σ quantity (current window)
prior_demand = Σ quantity (prior window)

if prior_demand ≤ 0:
    DA = 100 if current_demand > 0 else 0
else:
    ratio = current_demand / prior_demand
    acceleration = max(0, (ratio - 1) * 100)
    DA = min(100, acceleration)
```

| Ratio | DA Score | Interpretation |
|-------|----------|----------------|
| 1.0 | 0 | Stable demand |
| 1.5 | 50 | 50% demand increase |
| 2.0+ | 100 | Demand doubled or more |

**Window size:** Default lookback is 2 hours (current window) vs.
the preceding 2 hours (prior window). Implementations MAY adjust
window size for sector-specific dynamics.

### CR — Cancellation Rate

Measures current cancellation rate relative to the sector baseline:

```
current_rate = cancellations / total_events
safe_baseline = max(baseline_rate, 0.01)    // floor to prevent div/0
ratio = current_rate / safe_baseline
CR = min(100, max(0, (ratio - 1) * 100))
```

| Ratio | CR Score | Interpretation |
|-------|----------|----------------|
| 1.0 | 0 | Normal cancellation rate |
| 1.5 | 50 | 50% above baseline |
| 2.0+ | 100 | Doubled or worse |

**Default baseline cancellation rate:** 0.05 (5%)

---

## 5. K-Anonymity Enforcement

### Requirement

AVX MUST NOT be published for a sector unless at least `K` unique
firms have contributed events to the calculation window.

```
if unique_firms < K_ANONYMITY_MIN:
    return null    // AVX suppressed
```

| Parameter | Default | Minimum |
|-----------|---------|---------|
| K_ANONYMITY_MIN | 5 | 3 |

### Rationale

With K < 5, a sophisticated attacker could potentially:
- Infer individual firm trading volumes from PD changes
- Estimate a competitor's price range from PV shifts
- Detect a specific firm's demand patterns from DA movements

K = 5 provides a practical privacy floor while allowing AVX to
be useful in moderately active sectors.

### When K-Anonymity Fails

If a sector has fewer than K unique firms in the observation window:
- AVX is NOT published
- ALPHA falls back to MS = 0.5 (neutral market stability)
- No error is raised — this is expected behavior for low-activity sectors

---

## 6. AVX Output Format

```json
{
  "sector": "electronics",
  "timestamp": "2026-03-13T14:30:00Z",
  "avx_score": 42.5,
  "dimensions": {
    "pd_score": 35.0,
    "pv_score": 55.0,
    "da_score": 40.0,
    "cr_score": 20.0
  },
  "metadata": {
    "unique_firms": 12,
    "event_count": 847,
    "lookback_hours": 2,
    "k_anonymity_satisfied": true
  },
  "spec_version": "tatf-v0.1"
}
```

### Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| sector | MUST | Sector identifier |
| timestamp | MUST | Computation time |
| avx_score | MUST | Composite AVX (0-100) |
| dimensions.* | MUST | All four sub-scores |
| metadata.unique_firms | MUST | Firm count for k-anonymity verification |
| metadata.event_count | SHOULD | Total events in window |
| metadata.k_anonymity_satisfied | MUST | Boolean confirmation |
| spec_version | MUST | TATF version |

---

## 7. Historical AVX and Time Series

Implementations SHOULD maintain historical AVX scores to enable:

- Trend analysis (sector stress increasing/decreasing)
- Baseline establishment for CR dimension
- Regulatory reporting

### Retention

| Purpose | Retention Period |
|---------|-----------------|
| Real-time scoring | 24 hours |
| Trend analysis | 90 days |
| Compliance | Per applicable regulation |

---

## 8. Sector Taxonomy

TATF does not prescribe a fixed sector taxonomy. Implementations
MUST document their sector classification scheme and SHOULD use
industry-standard classifications where possible (ISIC, NAICS, GICS).

Recommended minimum sector granularity:
- Sector must map to a coherent set of agents with similar behavior
- Too broad (e.g., "commerce") → AVX is meaningless noise
- Too narrow (e.g., "blue widget procurement in Q2") → k-anonymity fails

---

## 9. Implementation Checklist

A TATF-conformant AVX implementation MUST:

- [ ] Compute all four dimensions per the formulas above
- [ ] Apply dimension weights: PD=0.40, PV=0.30, DA=0.20, CR=0.10
- [ ] Bound final score to [0, 100]
- [ ] Enforce k-anonymity (suppress when unique_firms < K)
- [ ] Include `k_anonymity_satisfied` in output
- [ ] Document the sector taxonomy used
- [ ] Handle edge cases (empty windows, zero means, single-firm sectors)

---

*This concludes the TATF v0.1 specification.*

## Appendix: Reference Implementation

A reference implementation of TATF v0.1 is available:

```
pip install tatf
```

The reference implementation includes:
- Local scoring engine (offline capable)
- All six KYA-B dimensions
- ALPHA composite scoring
- AVX calculation with k-anonymity
- Attestation generation (TATF Native format)

Source: `truceprotocol/truce-py` (Apache 2.0)
