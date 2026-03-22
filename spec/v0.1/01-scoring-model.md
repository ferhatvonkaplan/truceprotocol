# TATF v0.1 — Scoring Model

## 1. The Four-Layer Trust Model

TATF defines trust as a composite assessment across four independent
layers. Each layer adds signal depth; implementations MAY adopt layers
incrementally.

```
Layer 4: ADVERSARIAL TESTING          ← Proactive resilience
Layer 3: COMMUNITY SIGNALS            ← Cross-platform reputation
Layer 2: BEHAVIORAL BASELINES         ← Anomaly vs. own history
Layer 1: OBSERVABLE METRICS           ← Objective measurements
```

### Layer 1: Observable Metrics

Objective, externally verifiable facts about agent behavior:

| Metric | Type | Description |
|--------|------|-------------|
| Task completion rate | ratio | Successful completions / total attempts |
| Response consistency | score | Semantic similarity across equivalent queries |
| Latency patterns | distribution | Response time profile and anomalies |
| Error rate | ratio | Errors / total operations |
| API compliance | binary | Conforms to declared protocol specification |
| Uptime | ratio | Available time / total time |

Layer 1 metrics are REQUIRED. They are the "credit history" equivalent
— observable, undeniable facts.

### Layer 2: Behavioral Baselines

Statistical anomaly detection against the agent's own historical behavior,
using six scoring dimensions. This is the core of TATF's trust
assessment. See [02-behavioral-baselines.md](02-behavioral-baselines.md)
for full specification.

**Key principle:** An agent is scored relative to ITSELF, not to a global
standard. A high-frequency trading agent operating 24/7 is normal; the
same pattern from a 9-to-5 procurement agent is anomalous.

### Layer 3: Community Signals

Cross-platform reputation data aggregated from multiple sources:

| Signal | Source | Description |
|--------|--------|-------------|
| Peer reviews | Other agents | Structured feedback from transaction counterparties |
| Dispute history | Platform records | Frequency and outcomes of disputed transactions |
| Cross-platform reputation | Multiple platforms | Trust scores from different TATF-compliant scorers |
| Industry benchmarks | Sector data | Performance relative to sector-specific criteria |

Layer 3 signals emerge over time and through community adoption.
Implementations SHOULD incorporate community signals when available
but MUST NOT require them for basic scoring.

### Layer 4: Adversarial Testing

Proactive resilience evaluation through controlled testing:

| Test Category | Description |
|---------------|-------------|
| Prompt injection | Can the agent be manipulated via adversarial inputs? |
| Consistency probes | Does the agent give contradictory responses to logically equivalent queries? |
| Boundary testing | How does the agent behave at operational limits? |
| Collusion detection | Is the agent coordinating with counterparties to manipulate outcomes? |

Layer 4 is OPTIONAL and typically performed by specialized auditors.
See [05-adversarial-testing.md](05-adversarial-testing.md).

---

## 2. ALPHA Composite Trust Score

The ALPHA score is the primary output of TATF scoring. It represents
the **assessed probability that an agent will successfully fulfill a
given transaction**.

### Formula

```
ALPHA = w_AT * AT + w_MS * MS + w_TH * TH + w_CS * CS
```

Where:

| Component | Weight | Range | Source |
|-----------|--------|-------|--------|
| **AT** (Agent Trust) | 0.35 | [0, 1] | Inverted behavioral anomaly score |
| **MS** (Market Stability) | 0.25 | [0, 1] | Inverted market stress index |
| **TH** (Transaction History) | 0.25 | [0, 1] | Historical settlement rate |
| **CS** (Counterparty Score) | 0.15 | [0, 1] | Counterparty's trust level |

**Constraints:**
- All weights MUST sum to 1.0
- Final score MUST be bounded to [0.0, 1.0]
- Implementations MAY adjust weights within documented rationale

### Component Definitions

#### AT — Agent Trust (Layer 2)

Derived from the behavioral anomaly score (see [02-behavioral-baselines.md](02-behavioral-baselines.md)):

```
anomaly_score ∈ [0, 200]    (six-dimension composite)
AT = (200.0 - anomaly_score) / 200.0
AT = max(0.0, min(1.0, AT))
```

An agent with zero anomaly (composite = 0) yields AT = 1.0.
An agent with maximum anomaly (composite = 200) yields AT = 0.0.

#### MS — Market Stability

Derived from the AVX market stress index (see [06-market-stress.md](06-market-stress.md)):

```
avx_score ∈ [0, 100]    (sector-level stress indicator)
MS = (100.0 - avx_score) / 100.0
MS = max(0.0, min(1.0, MS))
```

If no sector data is available, implementations MUST use a neutral
default: **MS = 0.5**.

#### TH — Transaction History (Layer 1)

Settlement success rate from the agent's transaction record:

```
TH = settled_count / total_count
```

Where `settled_count` includes only fully settled (both parties confirmed)
transactions. If no transaction history exists, implementations MUST
use a neutral default: **TH = 0.5**.

#### CS — Counterparty Score

The counterparty agent's AT component score:

```
CS = AT_counterparty
```

This creates a reflexive trust relationship: dealing with a high-trust
counterparty improves your transaction score. If no counterparty is
specified, implementations MUST use a neutral default: **CS = 0.5**.

### Confidence Interval

TATF scores MUST include a confidence interval computed using the
Wald binomial method:

```
n = observation_count
margin = 1.96 * sqrt(ALPHA * (1 - ALPHA) / n)
ci_low  = max(0.0, ALPHA - margin)
ci_high = min(1.0, ALPHA + margin)
```

The 1.96 multiplier corresponds to a 95% confidence level.

As observation count increases, the confidence interval narrows,
reflecting increased certainty in the score.

### Cold-Start Handling

TATF defines two independent cold-start mechanisms:

**1. ALPHA Cold Start (observation count):**
Agents with fewer than `COLD_START_MIN` observations (default: 5)
MUST receive a neutral ALPHA score:

```
ALPHA = 0.50    (neutral score)
ci_low = 0.0
ci_high = 1.0
cold_start = true
```

**2. KYA-B Cold Start (calendar days):**
Agents with fewer than `COLD_START_DAYS` (default: 14) days of
observation data bypass behavioral anomaly scoring entirely
(see [02-behavioral-baselines.md](02-behavioral-baselines.md)).
During this period, `anomaly_score = 0` and `routing = AUTO_PASS`.

These are complementary mechanisms. An agent may exit ALPHA cold
start (after 5 observations) while still in KYA-B cold start
(before 14 days), in which case the ALPHA score is computed but
the AT component uses `anomaly_score = 0`.

The cold-start score is intentionally neutral — neither trusting
nor distrusting the agent. The wide confidence interval signals
to consumers that the score is not yet meaningful.

Implementations MUST flag cold-start scores to prevent routing
decisions based on insufficient data.

---

## 3. Score Interpretation

### Trust Tiers

Implementations SHOULD provide human-readable trust tiers:

| ALPHA Range | Tier | Interpretation |
|-------------|------|----------------|
| 0.80 – 1.00 | HIGH | Agent has strong trust indicators; low-risk transaction |
| 0.50 – 0.79 | MODERATE | Normal operating range; standard precautions apply |
| 0.30 – 0.49 | LOW | Elevated risk indicators; enhanced review recommended |
| 0.00 – 0.29 | CRITICAL | Significant trust concerns; manual review required |

### Threshold Alerts

Implementations SHOULD emit events when scores cross defined thresholds:

| Event | Condition | Description |
|-------|-----------|-------------|
| `alpha.breach` | score drops below 0.30 | Agent has entered critical trust zone |
| `alpha.recovery` | score rises above 0.80 | Agent has returned to high trust |

Threshold values are RECOMMENDED defaults. Implementations MAY
customize thresholds based on risk appetite.

---

## 4. Score Output Format

A TATF-compliant score MUST include the following fields:

```json
{
  "agent_id": "string",
  "score": 0.72,
  "confidence_low": 0.65,
  "confidence_high": 0.79,
  "components": {
    "agent_trust": 0.85,
    "market_stability": 0.70,
    "transaction_history": 0.60,
    "counterparty_score": 0.50
  },
  "observation_count": 47,
  "cold_start": false,
  "counterparty_id": "string | null",
  "sector": "string | null",
  "computed_at": "2026-03-13T14:30:00Z",
  "spec_version": "tatf-v0.1"
}
```

The `spec_version` field MUST be present and MUST match the
TATF version the implementation conforms to.

---

*Next: [02-behavioral-baselines.md](02-behavioral-baselines.md) — Behavioral Baselines*
