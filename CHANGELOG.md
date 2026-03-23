# Changelog

All notable changes to TATF will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
TATF uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the specification.

---

## [0.1.0] — 2026-03-21

### Added

**Specification (7 documents)**
- `00-introduction.md` — Motivation, scope, terminology, design principles
- `01-scoring-model.md` — ALPHA composite trust score (4 components: AT, MS, TH, CS) with Wald confidence intervals
- `02-behavioral-baselines.md` — EMA baselines (alpha=0.15), 6-dimension KYA-B anomaly scoring, 14-day cold-start protection
- `03-anomaly-detection.md` — ATBF routing zones (AUTO_PASS / SOFT_HOLD / HARD_BLOCK), review queue with 15-minute timeout
- `04-trust-attestation.md` — Ed25519 cryptographic attestation (TATF Native format), W3C Verifiable Credentials v2 mapping
- `05-adversarial-testing.md` — Layer 4 adversarial resilience evaluation framework
- `06-market-stress.md` — AVX market stress indicator (4 dimensions: PD, PV, DA, CR), k-anonymity enforcement

**Six Scoring Dimensions**
- Time anomaly (cap 35) — z-score of operating hour deviation
- Concurrent sessions (cap 45) — z-score of parallel activity count
- Price deviation (cap 40) — z-score of price vs. historical mean
- Category anomaly (0 or 30) — binary flag for unseen product category
- Negotiation rounds (0 or 25) — exceeds agent's p95 threshold
- Counterparty concentration (cap 25) — HHI delta of counterparty diversity

**Reference Implementation**
- Python package `tatf` on PyPI (`pip install tatf`)
- `TATFScorer` — local 6-dimension scoring with EMA baseline management
- `AVXCalculator` — 4-dimension market stress with k-anonymity gate
- `TATFAttestor` — Ed25519 attestation generation and verification
- 12 Pydantic models (Transaction, AlphaScore, AnomalyScore, AVXScore, etc.)
- 44 passing tests (scorer: 28, AVX: 10, attestation: 6)
- Python 3.9+ support

**Benchmarks**
- Synthetic dataset generator (5 archetypes: normal, cautious, volatile, anomalous, cold_start)
- Evaluation harness with confusion matrix reporting
- Reference result: 1,000 agents, 97,370 transactions, 97% classification accuracy

**Community**
- CONTRIBUTING.md with RFC process (14-day review period)
- SECURITY.md with responsible disclosure policy
- GOVERNANCE.md with lazy consensus model
- FAQ.md

### Technical Details

- Z-scores use epsilon guard (0.5) on denominator: `z = |observed - mean| / (std + epsilon)`
- ALPHA composite: `0.35*AT + 0.25*MS + 0.25*TH + 0.15*CS`
- AVX weights: PD (0.40) + PV (0.30) + DA (0.20) + CR (0.10) = 1.0
- AVX suppressed when unique_firms < k_anonymity_min (default 5)
- Dual cold-start: ALPHA (5 observations) vs. KYA-B (14 calendar days)
- Signing input: `sha256_hex(canonical_json) + "|" + iso8601_timestamp`

---

[0.1.0]: https://github.com/ferhatvonkaplan/truceprotocol/releases/tag/v0.1.0
