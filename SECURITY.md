# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in TATF, please report it responsibly.

**Email:** security@truceprotocol.com

Do **not** open a public GitHub issue for security vulnerabilities.

---

## Scope

The following are in scope for security reports:

| Category | Examples |
|----------|---------|
| **Scoring algorithm** | Inputs that produce incorrect routing decisions; systematic bias in dimension scoring |
| **ATBF bypass** | Transactions that should be HARD_BLOCK but route to AUTO_PASS |
| **AVX k-anonymity** | Attacks that reveal individual firm behavior from aggregate AVX scores with fewer than k participants |
| **Attestation forgery** | Ed25519 signature bypass; attestation tampering that passes verification |
| **Benchmark manipulation** | Crafted agent profiles that produce misleading accuracy metrics |
| **Cold-start exploitation** | Abuse of the 14-day warm-up period to avoid anomaly detection |
| **Dimension cap bypass** | Inputs that exceed documented dimension caps (e.g., s_time > 35) |

### Out of Scope

- Social engineering attacks against maintainers
- Denial of service (the reference implementation is a local library)
- Issues in dependencies (report to the upstream project)
- Theoretical attacks without a proof of concept

---

## Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Triage and severity assessment | Within 7 days |
| Fix for critical vulnerabilities | Within 30 days |
| Fix for non-critical vulnerabilities | Within 90 days |
| Public disclosure | After fix is released, coordinated with reporter |

---

## Severity Classification

| Severity | Description | Example |
|----------|-------------|---------|
| **Critical** | Scoring bypass that affects routing decisions | HARD_BLOCK transaction routed as AUTO_PASS |
| **High** | Privacy violation in aggregate metrics | Individual firm data extractable from AVX |
| **Medium** | Attestation integrity issue | Signature verification passes for modified payload |
| **Low** | Informational or edge-case behavior | Unexpected score for pathological input |

---

## Recognition

Security researchers who report valid vulnerabilities will be credited in `SECURITY_HALL_OF_FAME.md` (with your permission). We believe in recognizing the people who make TATF stronger.

---

## Design Note

TATF's scoring algorithm is **deterministic and auditable by design**. Given identical inputs, the scorer produces identical outputs — every time, on every platform. There is no randomness, no external state, and no network dependency at scoring time.

This means:
- Every scoring decision can be independently reproduced and verified
- Ed25519 attestations provide cryptographic proof of score computation
- The algorithm is fully specified in the [TATF v0.1 specification](spec/v0.1/)

Auditability is not a feature — it is a requirement for trust infrastructure.

---

## PGP Key

A PGP key for encrypted security communications will be published here once the key ceremony is complete.

In the interim, please use the email address above. If you require encrypted communication before the key is available, note this in your initial email and we will coordinate a secure channel.
