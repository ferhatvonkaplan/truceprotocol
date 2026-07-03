# TATF v1.0 — Scoring Model

## 1. The Five-Layer Trust Model

TATF defines trust as a composite assessment across five layers.
Each layer adds signal depth; implementations MAY adopt layers
incrementally.

```
Layer 5: ADVERSARIAL TESTING          ← Proactive resilience (optional)
Layer 4: EXTERNAL SIGNALS             ← Aggregated partner feeds (v1.0)
Layer 3: COMMUNITY SIGNALS            ← Cross-platform reputation
Layer 2: BEHAVIORAL BASELINES         ← Anomaly vs. own history
Layer 1: OBSERVABLE METRICS           ← Objective measurements
```

### Layer 1: Observable Metrics

Objective, externally verifiable facts about agent behaviour.

| Metric | Type | Description |
|--------|------|-------------|
| Task completion rate | ratio | Successful completions / total attempts. |
| Response consistency | score | Semantic similarity across equivalent queries. |
| Latency patterns | distribution | Response time profile and anomalies. |
| Error rate | ratio | Errors / total operations. |
| API compliance | binary | Conforms to declared protocol specification. |
| Uptime | ratio | Available time / total time. |

Layer 1 metrics are REQUIRED. They are the "credit history"
equivalent — observable, undeniable facts.

### Layer 2: Behavioural Baselines

Statistical anomaly detection against the agent's own historical
behaviour, using six scoring dimensions. The core of TATF's trust
assessment. See [02-behavioral-baselines.md](02-behavioral-baselines.md).

**Key principle:** An agent is scored relative to ITSELF, not to a
global standard.

### Layer 3: Community Signals

Cross-platform reputation data aggregated from multiple sources:

| Signal | Source |
|--------|--------|
| Peer reviews | Other agents |
| Dispute history | Platform records |
| Cross-platform reputation | Multiple TATF-compliant scorers |
| Industry benchmarks | Sector data |

Layer 3 signals emerge over time and through community adoption.
Implementations SHOULD incorporate community signals when available
but MUST NOT require them for basic scoring.

### Layer 4: External Signals (NEW in v1.0)

Aggregated inputs from specialised trust and security providers:

| Category | Example |
|----------|---------|
| Prompt injection / jailbreak | Lakera Guard |
| Governance maturity | Collibra |
| Runtime threats | CrowdStrike-tier runtime agents |
| Supply chain | Hardware attestation, model provenance |
| Regulatory flag | Sanctions / enforcement data |
| Network reputation | Community registries, incident databases |

Layer 4 signals are aggregated through the connector contract in
[07-signal-aggregation.md](07-signal-aggregation.md). Aggregator-
profile implementations consume at least one category; core-profile
implementations do not consume external signals.

### Layer 5: Adversarial Testing

Proactive resilience evaluation through controlled testing. Layer 5
is OPTIONAL and typically performed by specialised auditors or by
partnership with Layer 4 providers that run adversarial testing as
a service. See [05-adversarial-testing.md](05-adversarial-testing.md).

---

## 2. ALPHA Composite Trust Score

The ALPHA score is the primary output of TATF scoring. It represents
the **assessed probability that an agent will successfully fulfil a
given transaction**.

### 2.1 Formula

```
ALPHA = w_AT * AT + w_MS * MS + w_TH * TH + w_CS * CS + w_XS * XS
```

Where:

| Component | Aggregator Weight | Core Weight (v0.1-compat) | Range | Source |
|-----------|-------------------|---------------------------|-------|--------|
| **AT** (Agent Trust) | 0.30 | 0.35 | [0, 1] | Inverted behavioural anomaly score |
| **MS** (Market Stability) | 0.20 | 0.25 | [0, 1] | Inverted AVX market stress index |
| **TH** (Transaction History) | 0.25 | 0.25 | [0, 1] | Historical settlement rate |
| **CS** (Counterparty Score) | 0.10 | 0.15 | [0, 1] | Counterparty's trust level |
| **XS** (External Signals) | 0.15 | 0.00 | [0, 1] | Aggregated partner feeds (document 07) |

**Constraints:**

- All weights MUST sum to 1.0.
- Final score MUST be bounded to [0.0, 1.0].
- Implementations MAY adjust weights within documented rationale.
- Implementations MUST declare their profile (`core` or `aggregator`)
  and their weight vector in `/.well-known/tatf-aggregator.json`
  (aggregators) or in documentation (core).

### 2.2 Profile Declaration

| Profile | When to Use | XS Weight |
|---------|-------------|-----------|
| **Core** (v1.0) | Internal signals only; backward-compatible with v0.1. | 0.00 |
| **Aggregator** (v1.0) | Consumes at least one external signal category. | 0.15 (default) |

Implementations advertising aggregator profile without consuming
any external signals are non-conformant.

### 2.3 Component Definitions

#### AT — Agent Trust (Layer 2)

Derived from the behavioural anomaly score (see [02-behavioral-baselines.md](02-behavioral-baselines.md)):

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

Where `settled_count` includes only fully settled (both parties
confirmed) transactions. If no transaction history exists,
implementations MUST use a neutral default: **TH = 0.5**.

#### CS — Counterparty Score

The counterparty agent's AT component score:

```
CS = AT_counterparty
```

This creates a reflexive trust relationship: dealing with a high-trust
counterparty improves the transaction score. If no counterparty is
specified, implementations MUST use a neutral default: **CS = 0.5**.

#### XS — External Signals (NEW in v1.0)

The composite of aggregated external signals per [07-signal-aggregation.md](07-signal-aggregation.md). When the aggregator has at least one valid,
non-stale signal:

```
XS = weighted_mean_over_categories(
       weighted_mean_within_category(normalised_signals)
     )
```

Full definition in document 07, section 4. When no signals are
available, the aggregator MUST use: **XS = 0.5** (neutral) and MUST
record `xs_coverage = []` in the attestation.

### 2.4 Confidence Interval

TATF scores MUST include a confidence interval computed using the
Wald binomial method:

```
n = observation_count
margin = 1.96 * sqrt(ALPHA * (1 - ALPHA) / n)
ci_low  = max(0.0, ALPHA - margin)
ci_high = min(1.0, ALPHA + margin)
```

The 1.96 multiplier corresponds to a 95% confidence level.

For aggregator profiles, the confidence interval SHOULD additionally
be widened when significant XS weight comes from signals with
self-declared `confidence < 1.0`. A simple adjustment:

```
min_signal_confidence = min(s.confidence for s in contributing_signals)
ci_adjusted_margin = margin / min_signal_confidence
```

This ensures that low-confidence external signals do not produce
misleadingly narrow confidence intervals.

### 2.5 Cold-Start Handling

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
observation data bypass behavioural anomaly scoring entirely
(see [02-behavioral-baselines.md](02-behavioral-baselines.md)).
During this period, `anomaly_score = 0` and `routing = AUTO_PASS`.

These are complementary mechanisms. External signals (XS) are
evaluated during cold start; specifically, aggregator-profile
implementations MAY produce a meaningful XS composite even when
AT is neutral, and this is often the intended value proposition of
aggregation (signal coverage for new agents without transaction
history).

The cold-start score is intentionally neutral — neither trusting
nor distrusting the agent. The wide confidence interval signals
to consumers that the score is not yet meaningful.

Implementations MUST flag cold-start scores to prevent routing
decisions based on insufficient data.

---

## 3. Score Interpretation

### 3.1 Trust Tiers

Implementations SHOULD provide human-readable trust tiers:

| ALPHA Range | Tier | Interpretation |
|-------------|------|----------------|
| 0.80 – 1.00 | HIGH | Agent has strong trust indicators; low-risk transaction. |
| 0.50 – 0.79 | MODERATE | Normal operating range; standard precautions apply. |
| 0.30 – 0.49 | LOW | Elevated risk indicators; enhanced review recommended. |
| 0.00 – 0.29 | CRITICAL | Significant trust concerns; manual review required. |

### 3.2 Threshold Alerts

Implementations SHOULD emit events when scores cross defined
thresholds:

| Event | Condition |
|-------|-----------|
| `alpha.breach` | Score drops below 0.30 |
| `alpha.recovery` | Score rises above 0.80 |
| `alpha.signal_divergence` | AT and XS components differ by > 0.30 (aggregator-profile only) |

Threshold values are RECOMMENDED defaults. Implementations MAY
customise thresholds based on risk appetite.

`alpha.signal_divergence` is a v1.0 addition: when internal signals
(AT) and external signals (XS) materially disagree, it indicates
that corroboration is weak. Consumers may choose to require
reconciliation before trusting the score.

---

## 4. Score Output Format

A TATF v1.0 compliant score MUST include the following fields:

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
    "counterparty_score": 0.50,
    "external_signals": 0.83
  },
  "weights": {
    "AT": 0.30,
    "MS": 0.20,
    "TH": 0.25,
    "CS": 0.10,
    "XS": 0.15
  },
  "profile": "aggregator",
  "observation_count": 47,
  "cold_start": false,
  "counterparty_id": "string | null",
  "sector": "string | null",
  "xs_coverage": ["prompt_injection", "governance"],
  "signals_count": 2,
  "computed_at": "2026-04-20T14:30:00Z",
  "spec_version": "tatf-v1.0.0"
}
```

### 4.1 Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| `agent_id` | MUST | Scored agent. |
| `score` | MUST | ALPHA composite. |
| `confidence_low` | MUST | 95% CI lower bound. |
| `confidence_high` | MUST | 95% CI upper bound. |
| `components.*` | MUST | All components (XS absent for core profile). |
| `weights.*` | MUST | Declared weight vector. |
| `profile` | MUST | `"core"` or `"aggregator"`. |
| `observation_count` | MUST | Data points used. |
| `cold_start` | MUST | Boolean. |
| `xs_coverage` | MUST (aggregator) | Array of categories that contributed to XS. |
| `signals_count` | MUST (aggregator) | Count of valid, non-stale signals consumed. |
| `computed_at` | MUST | ISO 8601 timestamp. |
| `spec_version` | MUST | `"tatf-v1.0.0"` or later v1 patch. |

The `spec_version` field MUST be present and MUST match the TATF
version the implementation conforms to.

---

*Next: [02-behavioral-baselines.md](02-behavioral-baselines.md) — Behavioural Baselines*
