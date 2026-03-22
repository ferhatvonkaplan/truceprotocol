# TRUCE Agent Trust Framework (TATF)

**An open standard for autonomous agent trust scoring.**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Spec Version](https://img.shields.io/badge/spec-v0.1--draft-orange.svg)](spec/v0.1/)

---

## What is TATF?

TATF defines a protocol-agnostic methodology for scoring the trustworthiness
of autonomous LLM agents engaged in commercial transactions.

As agent-to-agent commerce scales, participants need a neutral, standardized
way to assess: **"Can I trust this agent to fulfill its obligations?"**

TATF provides that assessment through a four-layer scoring model.

## The Four Layers

```
Layer 4: ADVERSARIAL TESTING      Proactive resilience evaluation
Layer 3: COMMUNITY SIGNALS        Cross-platform reputation
Layer 2: BEHAVIORAL BASELINES     Anomaly detection vs. own history
Layer 1: OBSERVABLE METRICS       Objective, measurable behavior
```

- **Layers 1 & 2** are REQUIRED for conformance
- **Layer 3** is RECOMMENDED when cross-platform data is available
- **Layer 4** is OPTIONAL for enhanced assurance

## Quick Start

```python
pip install truce          # coming soon — see truceprotocol/truce-py

from truce import TruceClient

client = TruceClient()
score = client.score_agent("agent-123", sector="electronics")

print(score.alpha)           # 0.72
print(score.routing)         # AUTO_PASS
print(score.confidence)      # (0.65, 0.79)
```

## Specification

| Document | Description |
|----------|-------------|
| [00-introduction.md](spec/v0.1/00-introduction.md) | Motivation, scope, terminology |
| [01-scoring-model.md](spec/v0.1/01-scoring-model.md) | ALPHA composite score, four-layer model |
| [02-behavioral-baselines.md](spec/v0.1/02-behavioral-baselines.md) | EMA baselines, six scoring dimensions |
| [03-anomaly-detection.md](spec/v0.1/03-anomaly-detection.md) | ATBF zones, routing, review queue |
| [04-trust-attestation.md](spec/v0.1/04-trust-attestation.md) | Cryptographic attestation, W3C VC mapping |
| [05-adversarial-testing.md](spec/v0.1/05-adversarial-testing.md) | Adversarial resilience testing |
| [06-market-stress.md](spec/v0.1/06-market-stress.md) | AVX market stress indicator, k-anonymity |

## Key Design Decisions

- **Protocol-agnostic** — Works with A2A, ACP, MCP, or any agent protocol
- **Relative scoring** — Agents scored against their OWN baseline, not a global standard
- **Privacy-preserving** — k-anonymity on aggregate market metrics
- **Incrementally adoptable** — Implement layers independently
- **Fork-proof** — Apache 2.0 forever

## Benchmarks

The `benchmarks/` directory contains:
- Synthetic agent behavior datasets
- Evaluation tools for testing TATF implementations
- Community-contributed results

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### RFC Process

Significant changes to TATF follow an RFC process:
1. Open an issue describing the proposed change
2. Write an RFC document in `spec/rfcs/`
3. Community review period (minimum 14 days)
4. Core maintainer approval

## License

- Specification: [Apache 2.0](LICENSE)
- Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## Regulatory Alignment

| Regulation | TATF Coverage |
|-----------|---------------|
| EU AI Act (Aug 2026) | Trust scoring for high-risk AI agent supervision |
| NIST AI RMF | Maps to Govern, Map, Measure, Manage functions |
| ISO/IEC 42001 | Supports AI management system requirements |

---

*TATF is an open standard maintained by the TRUCE community.*
