# TATF v1.0 — Adversarial Testing

## 1. Overview

Layer 5 of TATF defines a methodology for proactively testing agent
resilience against adversarial scenarios. Unlike Layers 1–3, which
observe agent behaviour passively, and Layer 4, which aggregates
external signals, Layer 5 **actively probes** agents — and, new in
v1.0, the signal-ingestion path itself — to evaluate resistance to
manipulation.

**Status:** OPTIONAL in TATF v1.0. A conformant implementation **MAY**
implement Layer 5 for enhanced assurance (see [00-introduction.md](00-introduction.md),
Conformance). This document defines the framework and test taxonomy;
executable test suites are delivered with the reference implementation
and evolve through RFC.

Layer 5 testing is **typically** performed by specialised auditors or
through partnership with Layer 4 providers that run adversarial testing
as a service (see [01-scoring-model.md](01-scoring-model.md), Layer 5).
Results MAY be re-published as an external signal and folded into the
composite score through the document 07 contract (section 3).

---

## 2. Test Categories

### Category A: Input Manipulation

Tests whether the agent can be manipulated through crafted inputs.

| Test | Description | Severity |
|------|-------------|----------|
| A.1 Prompt injection | Adversarial prompts embedded in transaction metadata | HIGH |
| A.2 Schema evasion | Malformed inputs that exploit parser edge cases | MEDIUM |
| A.3 Encoding attacks | Unicode normalisation, homoglyph substitution | MEDIUM |
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

Tests agent behaviour at operational limits.

| Test | Description | Severity |
|------|-------------|----------|
| C.1 Rate limits | Behaviour under sustained high request rates | MEDIUM |
| C.2 Resource exhaustion | Response under memory/CPU pressure | LOW |
| C.3 Timeout handling | Behaviour when counterparty is slow | MEDIUM |
| C.4 Partial failures | Graceful degradation when dependencies fail | HIGH |

### Category D: Collusion Detection

Tests for coordinated behaviour between agents.

| Test | Description | Severity |
|------|-------------|----------|
| D.1 Price coordination | Multiple agents from different firms converging on non-market prices | CRITICAL |
| D.2 Volume manipulation | Artificial demand/supply signals | HIGH |
| D.3 Information leakage | Agent sharing counterparty information | CRITICAL |
| D.4 Wash trading | Agent trading with itself or affiliated agents | CRITICAL |

### Category E: Signal-Source Attacks (NEW in v1.0)

Tests whether an **aggregator** (an implementation that consumes
external signals per [07-signal-aggregation.md](07-signal-aggregation.md))
can be manipulated through a compromised, spoofed, or malicious signal
source. These tests exercise the connector and fusion path, not the
scored agent. Category E is only applicable to aggregator-profile
implementations.

| Test | Description | Severity |
|------|-------------|----------|
| E.1 Provider spoofing | Forged signal whose signature does not verify against the registered provider key | CRITICAL |
| E.2 Signal replay | A valid past signal re-submitted after its `valid_until` has elapsed | HIGH |
| E.3 Stale-signal acceptance | An expired or over-age signal offered for fusion | HIGH |
| E.4 Provider compromise | Legitimately signed signals exhibiting anomalous score shifts (stolen key or turned-malicious provider) | CRITICAL |
| E.5 Collusive inflation | Coordinated favourable signals for a target agent across one or more providers | HIGH |
| E.6 Signal flooding | High-rate signal submission intended to exhaust the connector or bias fusion | MEDIUM |

The expected outcome for each Category E test is defined in section 5
and cross-references the failure-handling requirements of document 07,
section 8.

---

## 3. Resilience Score

Adversarial testing produces a **resilience score** (0.0–1.0) computed
from test pass/fail rates weighted by severity:

```
resilience = Σ(w_i * pass_i) / Σ(w_i)
```

| Severity | Weight |
|----------|--------|
| CRITICAL | 4.0 |
| HIGH | 3.0 |
| MEDIUM | 2.0 |
| LOW | 1.0 |

### 3.1 Relationship to the ALPHA Composite

In v0.1 the resilience score was reported separately and reserved as a
candidate "fifth ALPHA component". In v1.0 that fifth-component slot is
occupied by **XS (External Signals)** (see [01-scoring-model.md](01-scoring-model.md),
section 2, and [07-signal-aggregation.md](07-signal-aggregation.md),
section 4).

The resilience score therefore remains **supplementary** in v1.0: it
**MUST NOT** be summed directly into ALPHA as an independent term.
Instead, the RECOMMENDED path for incorporating adversarial results
into the composite is via the document 07 signal contract:

- An adversarial-testing provider **MAY** publish resilience results as
  an external signal. Until a dedicated category is standardised, such a
  signal SHOULD use category `runtime_threat` (document 07, section 2).
- A dedicated `adversarial_resilience` category MAY be proposed through
  the RFC process (document 07, section 2 permits new categories).
- When delivered this way, the resilience score flows into XS through
  the normalisation and fusion rules of document 07, and appears in
  attestation signal provenance (document 07, section 6) like any other
  signal.

### 3.2 Supplementary Output Format

When reported directly (i.e. not routed through XS), the resilience
score is emitted as supplementary data alongside the ALPHA output:

```json
{
  "adversarial": {
    "resilience_score": 0.85,
    "tests_passed": 20,
    "tests_failed": 3,
    "tests_total": 23,
    "last_tested": "2026-04-20T00:00:00Z",
    "categories": {
      "input_manipulation": 0.90,
      "consistency_probes": 0.80,
      "boundary_testing": 1.00,
      "collusion_detection": 0.75,
      "signal_source": 0.83
    },
    "spec_version": "tatf-v1.0.0"
  }
}
```

The `signal_source` category is present only for aggregator-profile
implementations that ran Category E. For core-profile implementations
it MUST be omitted.

---

## 4. Testing Requirements

### Who Performs Tests

Adversarial testing MAY be performed by:

- The TATF-conformant scorer (self-testing).
- Independent auditors.
- Layer 4 signal providers that offer adversarial testing as a service.
- The agent's own operators (self-assessment).
- Community-contributed test suites.

### Test Frequency

| Agent Type | Recommended Frequency |
|------------|----------------------|
| High-value commerce (>$100K/tx) | Weekly |
| Standard commerce | Monthly |
| Low-risk / informational | Quarterly |

Aggregator-profile implementations SHOULD run Category E (signal-source)
tests against their connectors at least as often as they add or rotate a
signal provider, and after any provider key rotation.

### Ethical Boundaries

Adversarial testing MUST NOT:

- Cause financial loss to uninvolved parties.
- Disrupt production systems without explicit consent.
- Violate the agent operator's terms of service.
- Perform tests that could be classified as unauthorised access.
- Submit spoofed signals to a live signal provider's production endpoint;
  Category E tests MUST target the aggregator's own connector and fusion
  path, using synthetic or sandboxed provider fixtures.

All adversarial tests MUST be conducted in:

- Sandboxed environments, OR
- Production environments with explicit operator consent.

---

## 5. Adversarial Signal Resilience (NEW in v1.0)

The addition of Layer 4 (external signals) expands the attack surface: a
composite score is only as trustworthy as the signals fused into it. An
attacker who can spoof, replay, or corrupt an external signal can move
the XS component — and therefore ALPHA — without ever touching the
scored agent's behaviour. This section defines how an aggregator SHOULD
defend the signal-ingestion path. Every requirement here ties back to
the contract in [07-signal-aggregation.md](07-signal-aggregation.md).

### 5.1 Threat Model for External Signal Sources

| Threat | Attacker capability | Category E test |
|--------|---------------------|-----------------|
| Provider spoofing | Emit signals impersonating a known provider | E.1 |
| Signal replay | Capture and re-submit a previously valid, favourable signal | E.2 |
| Stale injection | Present an expired or over-age signal as current | E.3 |
| Provider compromise | Sign malicious signals with a stolen or turned provider key | E.4 |
| Collusive inflation | Coordinate favourable signals to inflate a target agent's XS | E.5 |
| Signal flooding | Overwhelm a connector or bias fusion with volume | E.6 |

### 5.2 Required Defences

An aggregator that implements Layer 5 signal resilience:

**5.2.1 Signal proof verification.** The aggregator MUST verify every
signal's Ed25519 signature against the provider's **registered** public
key before fusion (document 07, sections 3.1 and 6.2). Provider keys
MUST be resolved from the aggregator's own connector registry
(`/.well-known/tatf-aggregator.json`, document 07, section 7.3) — not
from a field controlled by the signal payload or by attacker-influenced
DNS. A signal that fails verification MUST be excluded from fusion and
logged for operator review (document 07, section 8.2). This defeats E.1
and E.4-by-forgery.

**5.2.2 Staleness and replay bounds.** The aggregator MUST reject stale
signals per document 07, section 4.4: a signal is stale if
`metadata.valid_until < current_time` or if `computed_at` exceeds the
configured maximum age for its category (RECOMMENDED defaults: 1 hour
`runtime_threat`, 24 hours `prompt_injection`, 7 days `governance`).
To defeat replay (E.2/E.3), the aggregator SHOULD additionally:

- De-duplicate by `signal_id` within the freshness window; a repeated
  `signal_id` MUST NOT contribute more than once.
- Enforce monotonic `computed_at` per (provider, subject) pair, rejecting
  a signal older than the newest already fused for that pair.

**5.2.3 Provider reputation.** The aggregator SHOULD maintain a
reputation score per provider derived from observable provider behaviour:
signature-verification failure rate, staleness rate, contract-validation
failure rate, and score-stability over time. A provider whose reputation
falls below a configured floor SHOULD have its signals de-weighted or
quarantined pending operator review, and repeated invalid emissions
SHOULD raise an alert (document 07, section 8.2). This bounds the blast
radius of E.4 (provider compromise).

**5.2.4 Bounded influence and outlier de-emphasis.** No single provider
or category should be able to dominate the composite:

- The effective weight contributed by any single provider SHOULD be
  capped, so that one signal cannot swing XS beyond a documented bound.
- Signals SHOULD be weighted by their self-declared
  `score.confidence` (document 07, section 4.1), and the confidence-widened
  interval of [01-scoring-model.md](01-scoring-model.md), section 2.4,
  MUST be applied when low-confidence signals contribute materially.
- An individual signal that is a statistical outlier relative to
  corroborating signals in the same category SHOULD be de-emphasised
  rather than allowed to move XS on its own. This applies the framework's
  guiding principle: concordant scores across sources indicate real
  signal; a single-dimension outlier is de-emphasised
  ([00-introduction.md](00-introduction.md), "The Ground Truth Problem").
  This blunts E.5 (collusive inflation).

Signal flooding (E.6) is handled by the connector back-pressure and
rate-limit requirements of document 07, section 8.3; a flooded connector
MUST fail open to "category absent" (XS neutral) rather than blocking the
scoring path.

### 5.3 Cross-Signal Corroboration and Divergence

Adversarial manipulation of a single source often reveals itself as
disagreement between internal and external signals. Aggregators SHOULD
monitor the `alpha.signal_divergence` event defined in
[01-scoring-model.md](01-scoring-model.md), section 3.2: when the
internal Agent Trust component (AT) and the external XS component differ
by more than 0.30, corroboration is weak and the score SHOULD be treated
as unreconciled. A compromised signal source that inflates XS while the
agent's own behaviour degrades AT is a canonical trigger for this event.

### 5.4 Signal Red-Team Testing (Category E)

An aggregator implementing Layer 5 SHOULD run the Category E suite
against its own connectors, using synthetic provider fixtures. Expected
outcomes:

| Test | Expected result | Reference |
|------|-----------------|-----------|
| E.1 Provider spoofing | Signal rejected at signature verification; excluded and logged | Doc 07, §3.1, §6.2, §8.2 |
| E.2 Signal replay | Duplicate `signal_id` / non-monotonic `computed_at` rejected | §5.2.2 |
| E.3 Stale-signal acceptance | Signal excluded as stale; category treated as absent if all stale | Doc 07, §4.4 |
| E.4 Provider compromise | Anomalous shift de-weighted / quarantined; alert raised | §5.2.3 |
| E.5 Collusive inflation | Outlier de-emphasised; single-provider influence capped | §5.2.4 |
| E.6 Signal flooding | Connector rate-limits; fails open to XS-neutral | Doc 07, §8.3 |

A failed Category E test indicates a defect in the signal-ingestion path
that MUST be remediated before the aggregator advertises Layer 5 signal
resilience.

---

## 6. Collusion Detection Framework

Collusion detection requires cross-agent analysis and is the most complex
adversarial test category. TATF v1.0 defines the conceptual framework;
detailed detection algorithms continue to be specified through RFC.

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

- Closed loops (A→B→C→A).
- Abnormal clustering coefficients.
- Sudden graph topology changes.

Note that Category E collusion (E.5, collusive signal inflation) is a
distinct concern: it operates at the *signal* layer rather than the
*transaction* layer, and is detected through the provider-reputation and
outlier-de-emphasis mechanisms of section 5.2, not through the trust
graph above.

---

## 7. Benchmark Integration

Adversarial test results feed into the TATF benchmark system.
Implementations can compare their resilience scores against the community
benchmark dataset:

```
benchmark_percentile = percentile_rank(
    agent_resilience,
    benchmark_dataset.resilience_scores
)
```

This allows agents and aggregators to understand their relative
resilience compared to the ecosystem average. The v1.0 benchmark dataset
SHOULD report Category E results separately from Categories A–D so that
signal-ingestion resilience can be compared independently of agent-level
resilience.

---

## 8. Conformance

Layer 5 is OPTIONAL. An implementation that advertises Layer 5
conformance:

- **MUST** document which test categories (A–E) it exercises.
- **MUST NOT** sum the resilience score directly into ALPHA; adversarial
  results are incorporated only via the document 07 signal path
  (section 3.1).
- **MUST**, if it advertises Layer 5 *signal resilience*, implement the
  required defences of section 5.2 and pass the Category E suite.
- **MUST NOT** run Category E against a third party's production signal
  endpoint (section 4, Ethical Boundaries).

A core-profile implementation (no external signals) MAY implement
Categories A–D and MUST omit Category E and the `signal_source`
resilience sub-score.

---

## 9. Future Work (v1.1+)

- Standardised, executable adversarial test suite covering Categories A–E.
- A dedicated `adversarial_resilience` signal category (RFC to document 07).
- Automated collusion detection algorithms (transaction-layer and signal-layer).
- Red team / blue team testing protocol.
- Adversarial test certification programme.

---

*Next: [06-market-stress.md](06-market-stress.md) — Market Stress Indicator (AVX)*
