# TATF v1.0 — Regulatory Mapping

*New in v1.0.* This document maps the technical mechanisms defined by
TATF to the requirements of major AI-governance and data-protection
regimes. It provides an article-by-article crosswalk for the EU AI
Act, function-level mappings for the NIST AI Risk Management Framework
(AI RMF), and clause-level mappings for ISO/IEC 42001.

---

## 1. Scope of This Mapping

### 1.1 What This Document Is

TATF is a **trust-scoring methodology**. It defines mechanisms —
behavioural baselines, anomaly-triggered routing, cryptographic
attestation, aggregate-stress indicators — that produce evidence and
controls a deployer can rely on when meeting a regulatory obligation.

This document identifies **which TATF mechanism supports which
requirement**, so that a compliance team can locate the relevant
technical control quickly.

### 1.2 What This Document Is NOT

> **TATF maps *to* regulations; it does not discharge them.**

A conformant TATF implementation provides technical mechanisms that
**support** compliance. It does **not** constitute compliance, and
nothing in this document is legal advice.

Specifically:

- TATF does **not** determine whether a given deployment is
  in-scope for any regulation. That is a fact- and jurisdiction-specific
  legal determination that MUST be made by the deployer.
- TATF does **not** produce the organisational artefacts (policies,
  risk registers, DPIAs, records of processing, management-system
  documentation) that most regimes also require. It produces the
  technical evidence those artefacts can cite.
- A mapping entry of "supports" means the mechanism contributes to
  satisfying the requirement. It never means the requirement is fully
  met by the mechanism alone.

The mapping tables below use a deliberate verb discipline:

| Verb | Meaning |
|------|---------|
| **satisfies (technical)** | The mechanism directly implements the *technical* portion of the requirement; organisational obligations remain. |
| **supports** | The mechanism provides evidence or a partial control toward the requirement. |
| **out of scope** | The requirement is not addressed by TATF; the deployer must address it elsewhere. |

This posture is consistent with TRUCE's own regulatory
self-assessment, which is offered "as a starting point for legal
review by customers, partners, and regulators," not as a compliance
attestation.

### 1.3 Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119). Normative keywords
here bind *implementations that claim regulatory-support conformance*;
they do not create legal obligations.

---

## 2. Mechanism Inventory

The crosswalks reference the following TATF mechanisms. Each is defined
normatively in the cited document.

| Mechanism | Defined in | One-line summary |
|-----------|-----------|------------------|
| **KYA-B six-dimension anomaly scoring** | [02](02-behavioral-baselines.md) | Anomaly composite (0–200) vs. the agent's own EMA baseline. |
| **Behavioural baselines (EMA, cold-start)** | [02](02-behavioral-baselines.md) | Per-agent statistical profile; 14-day cold-start bypass. |
| **ATBF routing zones** | [03](03-anomaly-detection.md) | AUTO_PASS / SOFT_HOLD / HARD_BLOCK from the anomaly composite. |
| **SOFT_HOLD review queue** | [03](03-anomaly-detection.md) | Time-bounded human-review path with fail-open/fail-closed timeout. |
| **ALPHA composite + confidence interval** | [01](01-scoring-model.md) | Five-component trust score in [0,1] with a 95% CI and cold-start flag. |
| **NOTA attestation + audit trail** | [04](04-trust-attestation.md) | Ed25519-signed, canonicalised, timestamped conformance statement. |
| **Signal provenance** | [07](07-signal-aggregation.md) | Which external signals contributed to a score, individually verifiable. |
| **Adversarial resilience testing** | [05](05-adversarial-testing.md) | Layer-5 proactive attack-pattern evaluation. |
| **AVX k-anonymity** | [06](06-market-stress.md) | Sector stress index published only when ≥ K unique firms contribute. |
| **Compartmentalisation** | Implementation | Split identity / trade domains; the scoring surface sees no PII. |

> Documents [04](04-trust-attestation.md) (Trust Attestation) and
> [05](05-adversarial-testing.md) (Adversarial Testing) are referenced
> here as the normative home of NOTA attestation and Layer-5 testing
> respectively. Where an implementation has not yet adopted those
> documents, the corresponding mapping entries are aspirational and
> MUST be marked as such in any compliance packet.

---

## 3. EU AI Act — Article-by-Article Crosswalk

### 3.1 Regulatory Posture

The applicability of the EU AI Act (Regulation (EU) 2024/1689; core
provisions enforceable from **2026-08-02**) depends on the deployment,
not on TATF. TRUCE's self-assessed posture is that of a
**general-purpose AI infrastructure provider**, not a high-risk AI
system operator: KYA-B behavioural scoring is a statistical anomaly
detector, not a biometric or social-scoring system in the Act's sense.

That posture is a **starting position for legal review**, not a
determination. A deployer that embeds TATF inside a high-risk system
(Annex III use cases) inherits high-risk obligations regardless of
TATF's own classification. The crosswalk below is written to be useful
whether or not the high-risk regime applies: it shows which Article-13,
-14, and -15 *technical* expectations a TATF deployment can help meet.

Implementations claiming EU-AI-Act support:

- **MUST** publish model cards for every scoring model they operate
  (ALPHA, KYA-B, AVX), so downstream operators can meet their own
  transparency obligations.
- **MUST NOT** represent TATF conformance as an EU AI Act conformity
  assessment, CE marking, or equivalent.
- **SHOULD** document, per deployment, whether the high-risk regime is
  believed to apply and why.

### 3.2 Article 13 — Transparency and Provision of Information to Deployers

**Requirement (summary):** High-risk AI systems must be designed so
that their operation is sufficiently transparent to enable deployers to
interpret output and use it appropriately; they must be accompanied by
instructions and by information about characteristics, capabilities, and
limitations.

**Primary TATF mechanism: NOTA attestation + audit trail.**

| Art. 13 expectation | TATF mechanism | Verb |
|---|---|---|
| Output is interpretable by the deployer | ALPHA output format ([01 §4](01-scoring-model.md)) exposes every component (AT, MS, TH, CS, XS), the weight vector, `observation_count`, and `cold_start`. | supports |
| Operation is traceable / auditable | NOTA attestation: canonicalise (sorted JSON) → SHA-256 → `sign(hash \| timestamp)` with Ed25519 ([04](04-trust-attestation.md)); every scored event yields an immutable, timestamped record. | satisfies (technical) |
| Deployer can understand what was attested | The NOTA statement is scoped precisely — it attests that an offer "was received at {timestamp} and verified to conform to TCOS v1.0 schema", *not* to the truth of the offer content. This bounded claim is itself a transparency control. | satisfies (technical) |
| Limitations are communicated | Cold-start scores are flagged (`cold_start = true`) with a maximally wide CI; the 95% confidence interval ([01 §2.4](01-scoring-model.md)) quantifies uncertainty rather than hiding it. | supports |
| Provenance of contributing signals is visible | Signal provenance array ([07 §6](07-signal-aggregation.md)) — each external signal is individually re-verifiable by the deployer. | satisfies (technical) |
| Characteristics/capabilities documentation | Published model cards (ALPHA, KYA-B, AVX). | supports |

**Honesty note:** The Article-13 "instructions for use" document is an
organisational artefact. TATF supplies the machine-readable evidence
those instructions must reference; it does not author the instructions.

### 3.3 Article 14 — Human Oversight

**Requirement (summary):** High-risk AI systems must be designed to be
effectively overseen by natural persons, who can intervene, override,
or halt the system.

**Primary TATF mechanism: ATBF SOFT_HOLD review queue.**

| Art. 14 expectation | TATF mechanism | Verb |
|---|---|---|
| A human can intervene before an automated decision takes effect | ATBF routes anomaly composite 50–119 to **SOFT_HOLD**, holding the transaction in a durable, time-bounded review queue ([03 §2](03-anomaly-detection.md)) before it reaches the order book. | satisfies (technical) |
| The reviewer has enough information to decide | Review items carry the full six-dimension anomaly breakdown ([03 §2](03-anomaly-detection.md)), so oversight is informed, not blind. | satisfies (technical) |
| The system can be halted / a decision blocked | **HARD_BLOCK** (composite ≥ 120) rejects immediately; `fail_closed` timeout mode auto-blocks unreviewed items in high-assurance deployments. | satisfies (technical) |
| Automation bias is mitigated | No single anomaly dimension can reach HARD_BLOCK alone (max single dimension = 45); at least three concurrent anomalies are required, reducing spurious auto-blocks that would erode meaningful oversight. | supports |
| Oversight actions are recorded | Review queue records `reviewed_at`, `reviewer_note`, and terminal status (APPROVED / REJECTED / TIMED_OUT), producing a human sign-off audit trail. | satisfies (technical) |
| Oversight scales with risk appetite | Configurable zone thresholds and `timeout_behavior` (`fail_open` vs `fail_closed`) let operators tune the human-in-the-loop boundary. | supports |

**Honesty note:** Article 14 also requires that oversight persons be
competent, adequately resourced, and organisationally empowered. TATF
provides the *mechanism* for intervention; staffing and authority are
the deployer's responsibility.

### 3.4 Article 15 — Accuracy, Robustness, and Cybersecurity

**Requirement (summary):** High-risk AI systems must achieve an
appropriate level of accuracy, robustness, and cybersecurity, and
perform consistently across their lifecycle, including resilience
against attempts to alter use or performance by exploiting
vulnerabilities.

**Primary TATF mechanisms: adversarial resilience testing
([05](05-adversarial-testing.md)) + behavioural baselines
([02](02-behavioral-baselines.md)).**

| Art. 15 expectation | TATF mechanism | Verb |
|---|---|---|
| Accuracy is declared and measurable | ALPHA scores carry a 95% confidence interval; aggregator CIs widen when low-confidence signals contribute ([01 §2.4](01-scoring-model.md)). Accuracy is stated with its uncertainty, not asserted. | supports |
| Robustness across the lifecycle | EMA baselines ([02 §2](02-behavioral-baselines.md)) adapt to legitimate drift while the epsilon guard (ε = 0.5) prevents degenerate z-scores; the 14-day cold-start bypass prevents false anomalies on thin data. | satisfies (technical) |
| Resilience to adversarial manipulation | Layer-5 adversarial resilience testing ([05](05-adversarial-testing.md)) evaluates known attack patterns (credential compromise, price manipulation, full account takeover — [03 §5](03-anomaly-detection.md)) before deployment. | supports |
| Detection of runtime attempts to alter behaviour | KYA-B dimensions target attack signatures directly: `s_concurrent` (cap 45) for credential compromise / bot amplification, `s_price` (cap 40) for manipulation, `s_counterparty` (cap 25) for value-funnelling collusion. | satisfies (technical) |
| Cybersecurity of the attestation surface | Ed25519 signing, SHA-256 hashing, canonical serialisation, and signature verification of every external signal ([07 §6.2](07-signal-aggregation.md)) protect integrity of the trust record. | satisfies (technical) |
| Consistent, reproducible performance | Deterministic scoring formulas plus a benchmark dataset (referenced in [00](00-introduction.md)) let any conformant implementation reproduce results — a robustness and auditability property. | supports |
| Fail-safe behaviour | Provider outages degrade gracefully (category treated as absent; scoring never fails — [07 §8](07-signal-aggregation.md)); neutral defaults (MS/TH/CS/XS = 0.5) prevent silent failure into false confidence. | satisfies (technical) |

**Honesty note:** Adversarial testing (Layer 5) is OPTIONAL under TATF
conformance. A deployment invoking this mapping for Article 15
robustness **MUST** actually run Layer-5 testing; citing the capability
without exercising it would be an overclaim.

### 3.5 EU AI Act Crosswalk — Summary

| Article | Topic | Primary TATF mechanism | Coverage |
|---|---|---|---|
| **13** | Transparency to deployers | NOTA attestation + audit trail; ALPHA output format; signal provenance | Technical transparency satisfied; instructions-for-use remain organisational. |
| **14** | Human oversight | ATBF SOFT_HOLD review queue; HARD_BLOCK; reviewer audit trail | Intervention mechanism satisfied; oversight staffing organisational. |
| **15** | Accuracy / robustness / cybersecurity | Layer-5 adversarial testing + behavioural baselines; Ed25519 integrity | Technical robustness supported; requires Layer-5 to be exercised. |

---

## 4. GDPR — Data Protection by Design

### 4.1 Article 25 — Data Protection by Design and by Default

**Requirement (summary):** Controllers must implement appropriate
technical and organisational measures — such as data minimisation and
pseudonymisation — both at the time of determining the means of
processing and at the time of the processing itself, ensuring that by
default only personal data necessary for each purpose is processed.

**Primary TATF mechanisms: AVX k-anonymity +
compartmentalisation.**

| Art. 25 expectation | TATF mechanism | Verb |
|---|---|---|
| Data minimisation by design | **Compartmentalisation**: the trade/scoring domain operates on agent identifiers and behavioural metrics and **never sees PII**; identity data is isolated behind a bridge at the module boundary. The scoring surface is architecturally blind to personal data. | satisfies (technical) |
| By-default minimisation of exposed data | **AVX k-anonymity** ([06 §5](06-market-stress.md)): a sector stress index is published **only** when ≥ `K_ANONYMITY_MIN` (default 5) unique firms contribute; below the threshold the index is suppressed (returns null), preventing re-identification of an individual firm's volumes, prices, or demand from the aggregate. | satisfies (technical) |
| Minimise data sent to third parties | Connectors SHOULD transmit only the minimum needed; agent identifiers MAY be hashed before transmission and transaction details SHOULD NOT be shared unless the signal category requires them ([07 §9.1](07-signal-aggregation.md)). | supports |
| Pseudonymisation | Scoring keys on stable agent identifiers rather than principal PII; identifier hashing to providers is supported. | supports |
| Purpose limitation of the trust record | The NOTA statement is scoped to schema conformance and receipt time only ([04](04-trust-attestation.md)); it does not accrete personal data. | supports |

### 4.2 Broader GDPR Alignment (Reference)

For completeness, TRUCE's implementation-level self-assessment maps
additional GDPR articles. These are **implementation** properties, not
TATF-spec requirements, and are reproduced here only to situate
Article 25 in context.

| GDPR Article | Supporting mechanism | Status |
|---|---|---|
| Art. 5(1)(c) data minimisation | Two-layer tokens — trade domain never sees PII | Implemented |
| Art. 17 right to erasure | Identity-domain deletion propagates via bridge | Implemented |
| Art. 25 privacy by design | Compartmentalisation at module boundary + AVX k-anonymity | Implemented |
| Art. 30 records of processing | — | **Gap — draft in progress** |
| Art. 32 security of processing | NOTA audit log, Ed25519 signing, TLS 1.3 | Implemented |
| Art. 35 DPIA | DPIA template | **Planned (V1.1)** |

**Honesty note:** TATF/TRUCE does **not** yet maintain an Article-30
record of processing activities, and a DPIA template is planned rather
than delivered. These gaps are stated openly here and in the
implementation's `KNOWN_GAPS.md`. Article 25 is an architectural
property; several other GDPR obligations remain organisational work for
the controller.

---

## 5. NIST AI Risk Management Framework (AI RMF 1.0)

The NIST AI RMF organises AI risk management into four functions:
**Govern, Map, Measure, Manage**. TATF's component surfaces map to each
function. Representative subcategories are cited for orientation only;
they are not an exhaustive conformance claim.

| Function | Intent | TATF mechanisms | Representative subcategories | Verb |
|---|---|---|---|---|
| **Govern** | Cultivate a risk-management culture; accountability, policies, transparency. | Open, auditable methodology; published weight vectors and `/.well-known/tatf-aggregator.json` ([07 §7.3](07-signal-aggregation.md)); model cards; `spec_version` on every output; NOTA audit trail. | GOVERN 1.1–1.4 (policies, accountability), GOVERN 4.1 (documentation/transparency) | supports |
| **Map** | Establish context; identify and categorise risks. | MAESTRO gap coverage ([00](00-introduction.md)); six external signal categories ([07 §2](07-signal-aggregation.md)); documented sector taxonomy ([06 §8](06-market-stress.md)); adversarial attack-pattern catalogue ([03 §5](03-anomaly-detection.md), [05](05-adversarial-testing.md)). | MAP 1.1 (context), MAP 3.x (risk categorisation), MAP 5.1 (impact) | supports |
| **Measure** | Analyse, assess, benchmark, and track risk metrics. | ALPHA composite with 95% CI ([01](01-scoring-model.md)); six-dimension KYA-B anomaly scoring ([02](02-behavioral-baselines.md)); AVX sector stress ([06](06-market-stress.md)); benchmark dataset for reproducibility. | MEASURE 1.1 (metrics), MEASURE 2.5–2.7 (validity, robustness, security), MEASURE 3.x (tracking) | satisfies (technical) |
| **Manage** | Prioritise, respond to, and recover from risks. | ATBF routing zones + SOFT_HOLD review queue ([03](03-anomaly-detection.md)); threshold alerts (`alpha.breach`, `alpha.recovery`, `alpha.signal_divergence` — [01 §3.2](01-scoring-model.md)); graceful degradation on provider failure ([07 §8](07-signal-aggregation.md)); webhook-driven incident response. | MANAGE 1.x (prioritisation), MANAGE 2.x (response), MANAGE 4.1 (monitoring) | satisfies (technical) |

**Honesty note:** The AI RMF is a *voluntary* framework, and Govern in
particular is dominated by organisational practices (roles, culture,
legal review). TATF strongly supports the **Measure** and **Manage**
functions with concrete technical controls; it *supports but does not
complete* **Govern** and **Map**, which require deployer-side policy and
context work.

---

## 6. ISO/IEC 42001:2023 — AI Management System

ISO/IEC 42001 specifies requirements for an AI Management System
(AIMS). An AIMS is fundamentally an **organisational** construct;
certification is against the management system, not against a scoring
library. TATF supplies technical controls and evidence that an AIMS can
incorporate — principally under the operation, performance-evaluation,
and Annex A control clauses.

| ISO/IEC 42001 area | Requirement focus | TATF contribution | Verb |
|---|---|---|---|
| **Clause 6** — Planning | AI risk assessment and treatment; objectives. | KYA-B dimensions and ATBF thresholds are documented, tunable risk-treatment controls with stated rationale ([02](02-behavioral-baselines.md), [03 §1](03-anomaly-detection.md)). | supports |
| **Clause 8** — Operation | AI risk assessment during operation; operational controls; impact assessment. | Real-time ATBF routing, SOFT_HOLD containment, HARD_BLOCK circuit-breaker; per-transaction scoring ([03](03-anomaly-detection.md)). | satisfies (technical) |
| **Clause 9** — Performance evaluation | Monitoring, measurement, analysis, evaluation. | ALPHA + CI, AVX time series, threshold alert events, review-latency and queue-depth metrics ([01](01-scoring-model.md), [03 §2](03-anomaly-detection.md), [06 §7](06-market-stress.md)). | satisfies (technical) |
| **Clause 10** — Improvement | Corrective action; continual improvement. | EMA baseline adaptation; documented threshold re-tuning; RFC-based methodology evolution ([00](00-introduction.md)). | supports |
| **Annex A.6** — AI system lifecycle | Responsible design, verification, deployment. | Cold-start observation period; adversarial testing before promotion ([05](05-adversarial-testing.md)); benchmark validation. | supports |
| **Annex A.7** — Data for AI systems | Data quality, provenance, management. | Signal provenance and re-verification ([07 §6](07-signal-aggregation.md)); documented default baselines and edge-case handling ([02 §2](02-behavioral-baselines.md)). | supports |
| **Annex A.8** — Information for interested parties | Transparency to users/deployers. | NOTA attestation, model cards, published output schema. | satisfies (technical) |
| **Annex A.10** — Third-party relationships | Governance of external suppliers. | External-signal connector contract, per-provider signature verification, `/.well-known` connector declaration ([07 §7](07-signal-aggregation.md)). | supports |

**Honesty note:** No amount of TATF conformance yields ISO/IEC 42001
certification. Certification requires an audited management system —
leadership commitment (Clause 5), context definition (Clause 4),
support and competence (Clause 7), and internal audit. TATF provides
technical controls that such an AIMS can *reference as evidence*.

---

## 7. PCI DSS v4.0 (Card-Data Environments)

Where TATF is deployed inside an environment that handles cardholder
data, its continuous behavioural monitoring aligns with PCI DSS v4.0's
monitoring requirements.

| PCI DSS v4.0 area | TATF contribution | Verb |
|---|---|---|
| Req. 10 — Log and monitor all access; audit trails | NOTA immutable, timestamped, signed attestation ledger. | supports |
| Req. 10.7 / anomaly detection | KYA-B six-dimension anomaly scoring + ATBF routing. | supports |
| Req. 12 — Continuous risk assessment | ALPHA trend + AVX sector stress as ongoing risk signals. | supports |

**Honesty note:** PCI DSS scope, network segmentation, encryption of
stored cardholder data, and QSA assessment are entirely the deployer's
responsibility. TATF touches only the continuous-monitoring surface.

---

## 8. What TATF Does Not Provide

To prevent overclaiming, implementations invoking this mapping **MUST
NOT** represent TATF as delivering any of the following:

- Legal advice, legal opinions, or a determination of regulatory
  applicability.
- An EU AI Act conformity assessment, CE marking, or notified-body
  certification.
- ISO/IEC 42001 certification, or any accredited certification.
- A GDPR Article-30 record of processing, a completed DPIA, or a lawful
  basis determination.
- VASP / CASP / MSB / payment-institution authorisation. TATF does not
  custody funds, execute transfers, or onboard end-users for financial
  services; regulated deployments remain responsible for their own
  registrations.
- Foundation-model provider obligations. Where an implementation uses a
  third-party LLM (e.g. for claim extraction), the LLM provider's
  obligations rest with that provider and the operator.

These boundaries mirror the implementation's published regulatory
position and `KNOWN_GAPS.md`, and are stated here so that a compliance
reader forms accurate expectations.

---

## 9. Conformance for Regulatory-Support Claims

An implementation that advertises "TATF regulatory-support conformance":

- **MUST** state, for each regulation it references, which specific
  TATF mechanisms it operates and which requirements those mechanisms
  *support* versus *satisfy technically*, using the verb discipline in
  §1.2.
- **MUST NOT** describe any TATF mechanism as achieving legal
  compliance, certification, or conformity assessment.
- **MUST** exercise any mechanism it cites — in particular, it MUST NOT
  claim Article 15 robustness support via Layer-5 adversarial testing
  ([05](05-adversarial-testing.md)) unless that testing is actually
  performed.
- **MUST** publish model cards for every scoring model it operates when
  claiming EU AI Act Article 13 support.
- **MUST** disclose known gaps (e.g. GDPR Article 30) rather than imply
  full coverage.
- **SHOULD** re-review this mapping whenever a referenced regulation is
  amended or a referenced TATF document (notably
  [04](04-trust-attestation.md) and [05](05-adversarial-testing.md))
  changes normative status.
- **SHOULD** treat every mapping entry as an input to legal review, not
  a substitute for it.

---

## 10. Summary

| Regime | Primary TATF support | Ceiling (what TATF cannot do) |
|---|---|---|
| **EU AI Act** Art. 13 / 14 / 15 | NOTA + audit trail; SOFT_HOLD review queue; adversarial testing + behavioural baselines | Not a conformity assessment; instructions-for-use and oversight staffing remain organisational. |
| **GDPR** Art. 25 (+ context) | Compartmentalisation; AVX k-anonymity; data-minimising connectors | No Art. 30 record; no DPIA; no lawful-basis determination. |
| **NIST AI RMF** | Strong on Measure + Manage; supports Govern + Map | Voluntary framework; Govern is organisational. |
| **ISO/IEC 42001** | Clause 8/9 operational + monitoring controls; Annex A evidence | No certification; AIMS is organisational. |
| **PCI DSS v4.0** | Continuous behavioural monitoring | Scope, segmentation, QSA assessment are the deployer's. |

TATF gives compliance teams **auditable, reproducible, cryptographically
verifiable technical mechanisms** to point at when meeting these
obligations. The obligations themselves remain with the deploying
organisation and its counsel.

---

*This is the final document in the TATF v1.0 specification. For the
framework overview, terminology, and document map, return to
[00-introduction.md](00-introduction.md).*
