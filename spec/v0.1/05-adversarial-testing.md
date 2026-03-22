# TATF v0.1 — Adversarial Testing

## 1. Overview

Layer 4 of TATF defines a methodology for proactively testing agent
resilience against adversarial scenarios. Unlike Layers 1-3 which
observe agent behavior passively, Layer 4 **actively probes** agents
to evaluate their resistance to manipulation.

**Status:** OPTIONAL in TATF v0.1. This section defines the framework;
detailed test suites will be specified in future versions.

---

## 2. Test Categories

### Category A: Input Manipulation

Tests whether the agent can be manipulated through crafted inputs.

| Test | Description | Severity |
|------|-------------|----------|
| A.1 Prompt injection | Adversarial prompts embedded in transaction metadata | HIGH |
| A.2 Schema evasion | Malformed inputs that exploit parser edge cases | MEDIUM |
| A.3 Encoding attacks | Unicode normalization, homoglyph substitution | MEDIUM |
| A.4 Overflow conditions | Extreme numeric values, oversized payloads | LOW |

### Category B: Consistency Probes

Tests whether the agent produces contradictory outputs.

| Test | Description | Severity |
|------|-------------|----------|
| B.1 Semantic equivalence | Same query, different phrasing → same answer? | HIGH |
| B.2 Temporal consistency | Same query repeated over time → stable answer? | MEDIUM |
| B.3 Ordering sensitivity | Does response change based on information presentation order? | MEDIUM |
| B.4 Negation handling | Does the agent correctly process negated conditions? | HIGH |

### Category C: Boundary Testing

Tests agent behavior at operational limits.

| Test | Description | Severity |
|------|-------------|----------|
| C.1 Rate limits | Behavior under sustained high request rates | MEDIUM |
| C.2 Resource exhaustion | Response under memory/CPU pressure | LOW |
| C.3 Timeout handling | Behavior when counterparty is slow | MEDIUM |
| C.4 Partial failures | Graceful degradation when dependencies fail | HIGH |

### Category D: Collusion Detection

Tests for coordinated behavior between agents.

| Test | Description | Severity |
|------|-------------|----------|
| D.1 Price coordination | Multiple agents from different firms converging on non-market prices | CRITICAL |
| D.2 Volume manipulation | Artificial demand/supply signals | HIGH |
| D.3 Information leakage | Agent sharing counterparty information | CRITICAL |
| D.4 Wash trading | Agent trading with itself or affiliated agents | CRITICAL |

---

## 3. Resilience Score

Adversarial testing produces a **resilience score** (0.0–1.0)
computed from test pass/fail rates weighted by severity:

```
resilience = Σ(w_i * pass_i) / Σ(w_i)
```

| Severity | Weight |
|----------|--------|
| CRITICAL | 4.0 |
| HIGH | 3.0 |
| MEDIUM | 2.0 |
| LOW | 1.0 |

### Integration with ALPHA Score

The resilience score is NOT directly included in the ALPHA composite
in v0.1. It is reported separately as supplementary data:

```json
{
  "adversarial": {
    "resilience_score": 0.85,
    "tests_passed": 14,
    "tests_failed": 2,
    "tests_total": 16,
    "last_tested": "2026-03-01T00:00:00Z",
    "categories": {
      "input_manipulation": 0.90,
      "consistency_probes": 0.80,
      "boundary_testing": 1.00,
      "collusion_detection": 0.75
    }
  }
}
```

Future TATF versions MAY incorporate the resilience score as a
fifth ALPHA component.

---

## 4. Testing Requirements

### Who Performs Tests

Adversarial testing MAY be performed by:
- The TATF-compliant scorer (self-testing)
- Independent auditors
- The agent's own operators (self-assessment)
- Community-contributed test suites

### Test Frequency

| Agent Type | Recommended Frequency |
|------------|----------------------|
| High-value commerce (>$100K/tx) | Weekly |
| Standard commerce | Monthly |
| Low-risk/informational | Quarterly |

### Ethical Boundaries

Adversarial testing MUST NOT:
- Cause financial loss to uninvolved parties
- Disrupt production systems without explicit consent
- Violate the agent's operator terms of service
- Perform tests that could be classified as unauthorized access

All adversarial tests MUST be conducted in:
- Sandboxed environments, OR
- Production environments with explicit operator consent

---

## 5. Collusion Detection Framework

Collusion detection requires cross-agent analysis and is the most
complex adversarial test category. TATF v0.1 defines the conceptual
framework; detailed detection algorithms will follow in v0.2.

### Signals

| Signal | Detection Method |
|--------|-----------------|
| Price clustering | Statistical test for non-random price convergence among "independent" agents |
| Timing correlation | Cross-correlation of transaction timing across agents |
| Counterparty preference | Abnormal mutual preference between specific agent pairs |
| Volume patterns | Coordinated volume spikes across agents |

### Graph Analysis

Collusion detection benefits from a **trust graph** where nodes are
agents and edges are transactions. Suspicious patterns include:
- Closed loops (A→B→C→A)
- Abnormal clustering coefficients
- Sudden graph topology changes

---

## 6. Benchmark Integration

Adversarial test results feed into the TATF benchmark system.
Implementations can compare their resilience scores against the
community benchmark dataset:

```
benchmark_percentile = percentile_rank(
    agent_resilience,
    benchmark_dataset.resilience_scores
)
```

This allows agents to understand their relative resilience compared
to the ecosystem average.

---

## 7. Future Work (v0.2+)

- Standardized adversarial test suite (executable)
- Automated collusion detection algorithms
- Resilience score integration into ALPHA composite
- Red team / blue team testing protocol
- Adversarial test certification program

---

*Next: [06-market-stress.md](06-market-stress.md) — Market Stress Indicator (AVX)*
