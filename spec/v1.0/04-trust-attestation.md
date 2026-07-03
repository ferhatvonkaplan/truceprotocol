# TATF v1.0 — Trust Attestation

## 1. Overview

A trust attestation is a cryptographically signed statement by a
TATF-conformant scorer asserting an agent's trust level at a specific
point in time. Attestations are the **output artifact** of the scoring
process — they are what consumers (platforms, counterparties, regulators)
use to make trust decisions.

TATF defines two attestation formats:

1. **TATF Native** — Minimal, purpose-built format for high-throughput
   environments. This is the format emitted by the reference
   implementation (`truce-py`).
2. **W3C Verifiable Credential** — Standards-compliant format for
   interoperability with existing identity and credential ecosystems.

Implementations MUST support at least one format and SHOULD support both.

*New in v1.0:* attestations carry the scorer's **profile** and applied
**weight vector**, the fifth ALPHA component (`external_signals`) for
aggregator-profile scores, and a **signal provenance** block so consumers
can audit which external-signal categories contributed to a score
(section 5).

---

## 2. Attestation Semantics

### What an Attestation Asserts

A TATF attestation makes the following claim:

> "The issuer attests that agent {agent_id} was scored at {timestamp}
> using TATF {spec_version} methodology under the {profile} profile and
> received a trust score of {alpha} with confidence interval
> [{confidence_low}, {confidence_high}] based on {observation_count}
> observations."

For aggregator-profile scores, the claim is extended:

> "…and the External Signals (XS) component was derived from
> {signals_count} external signals across categories {xs_coverage}."

### What an Attestation Does NOT Assert

- The attestation does NOT guarantee future behaviour.
- The attestation does NOT verify the truth of the agent's commercial
  claims.
- The attestation does NOT constitute regulatory approval.
- The attestation does NOT replace due diligence.

The attestation is a **point-in-time assessment** based on available data.

---

## 3. Cryptographic Requirements

### Signing Algorithm

Implementations MUST use one of:

| Algorithm | Key Size | Use Case |
|-----------|----------|----------|
| **Ed25519** (RECOMMENDED) | 256-bit | Default; fast, compact signatures. |
| ECDSA P-256 | 256-bit | Interop with existing PKI. |
| RSA-PSS | 2048-bit minimum | Legacy environments only. |

The reference implementation uses Ed25519 exclusively.

### Signature Process

```
1. Canonicalize the attestation payload (deterministic serialization)
2. Compute SHA-256 hash of canonical form: hash = SHA-256(canonical_bytes)
3. Construct signing input: sign_input = hash_hex + "|" + iso8601_timestamp
   Example: "a3f8c1...b7e2|2026-04-20T14:30:00Z"
4. Sign: signature = Sign(UTF-8(sign_input), private_key)
5. Encode signature as hex string
```

**Signing input format:** The pipe-delimited concatenation of the
hex-encoded hash and the ISO 8601 timestamp ensures deterministic,
reproducible signing input across implementations. Both fields MUST be
present. The timestamp used in `sign_input` MUST equal `proof.signed_at`.

### Canonicalization

The attestation payload MUST be canonicalized before signing using
**sorted-key JSON** with no optional whitespace:

```
canonical = JSON.serialize(payload, {
    sort_keys: true,
    separators: [",", ":"],   // no spaces
    ensure_ascii: false
})
```

This ensures byte-identical serialization across implementations. The
`proof` object MUST be excluded from the canonical form (it is appended
after signing).

---

## 4. TATF Native Format

### Attestation Object

The following object matches the reference implementation output. The
`components.external_signals` field and the `signal_provenance` block are
present for aggregator-profile scores and absent for core-profile scores.

```json
{
  "spec_version": "tatf-v1.0.0",
  "attestation_id": "ATT-a3f8c1b7e2d4f5a9",
  "issuer": {
    "id": "truce-aggregator-eu-1",
    "name": "TRUCE Reference Aggregator",
    "public_key": "ed25519:{hex}"
  },
  "subject": {
    "agent_id": "agent-7f3c"
  },
  "score": {
    "alpha": 0.72,
    "confidence_low": 0.65,
    "confidence_high": 0.79,
    "observation_count": 47,
    "cold_start": false
  },
  "profile": "aggregator",
  "weights": {
    "AT": 0.30,
    "MS": 0.20,
    "TH": 0.25,
    "CS": 0.10,
    "XS": 0.15
  },
  "components": {
    "agent_trust": 0.85,
    "market_stability": 0.70,
    "transaction_history": 0.60,
    "counterparty_score": 0.50,
    "external_signals": 0.83
  },
  "signal_provenance": {
    "xs_coverage": ["prompt_injection", "governance"],
    "signals_count": 2
  },
  "anomaly": {
    "composite": 30.0,
    "routing": "AUTO_PASS",
    "dimensions": {
      "s_time": 0.0,
      "s_concurrent": 15.0,
      "s_price": 12.0,
      "s_category": 0.0,
      "s_rounds": 0.0,
      "s_counterparty": 3.0
    }
  },
  "metadata": {
    "computed_at": "2026-04-20T14:30:00Z",
    "valid_until": "2026-04-20T15:30:00Z",
    "sector": "electronics",
    "counterparty_id": "agent-9a1d | null"
  },
  "proof": {
    "type": "Ed25519Signature",
    "hash": "sha256:{hex}",
    "signature": "{hex}",
    "signed_at": "2026-04-20T14:30:00Z"
  }
}
```

For a **core-profile** score, `components.external_signals` is omitted,
the `signal_provenance` block is absent, and `weights` reflect the v0.1
vector (`AT` 0.35, `MS` 0.25, `TH` 0.25, `CS` 0.15, `XS` 0.00).

### Field Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `spec_version` | MUST | Spec version string — MUST be `"tatf-v1.0.0"` or a later v1 patch. |
| `attestation_id` | MUST | Unique identifier (`ATT-{16-hex}`). |
| `issuer.id` | MUST | Scorer identifier. |
| `issuer.name` | SHOULD | Human-readable issuer name. |
| `issuer.public_key` | MUST | Verification key (`ed25519:{hex}`). |
| `subject.agent_id` | MUST | Scored agent. |
| `score.alpha` | MUST | ALPHA composite score. |
| `score.confidence_low` | MUST | 95% CI lower bound. |
| `score.confidence_high` | MUST | 95% CI upper bound. |
| `score.observation_count` | MUST | Data points used. |
| `score.cold_start` | MUST | Whether in cold start. |
| `profile` | MUST | `"core"` or `"aggregator"` (v1.0). |
| `weights.*` | MUST | Declared weight vector actually applied (v1.0). |
| `components.agent_trust` | MUST | AT — inverted anomaly score. |
| `components.market_stability` | MUST | MS — inverted AVX. |
| `components.transaction_history` | MUST | TH — settlement rate. |
| `components.counterparty_score` | MUST | CS — counterparty AT. |
| `components.external_signals` | MUST (aggregator) | XS — external signal composite. Absent for core profile (v1.0). |
| `signal_provenance.xs_coverage` | MUST (aggregator) | Categories that contributed to XS (v1.0). |
| `signal_provenance.signals_count` | MUST (aggregator) | Count of valid, non-stale signals consumed (v1.0). |
| `anomaly.composite` | SHOULD | Behavioural anomaly score. |
| `anomaly.routing` | SHOULD | ATBF zone. |
| `anomaly.dimensions.*` | SHOULD | Six-dimension breakdown. |
| `metadata.computed_at` | MUST | ISO 8601 timestamp. |
| `metadata.valid_until` | SHOULD | Attestation expiry. |
| `metadata.sector` | MAY | Sector context (or `null`). |
| `metadata.counterparty_id` | MAY | Counterparty agent (or `null`). |
| `proof.type` | MUST | Signature algorithm. |
| `proof.hash` | MUST | Canonical payload hash. |
| `proof.signature` | MUST | Cryptographic signature (`"unsigned"` if crypto unavailable). |
| `proof.signed_at` | MUST | Timestamp used in `sign_input`. |

The `weights` vector MUST sum to 1.0 and MUST match the vector declared
in the scorer's profile metadata (see section 8 and
[07-signal-aggregation.md](07-signal-aggregation.md) §7.3). Consumers MAY
reject an attestation whose `profile` is `"aggregator"` but whose
`components.external_signals` or `signal_provenance` block is absent, as
this is a non-conformant aggregator score.

### Attestation Validity

Attestations SHOULD have a `valid_until` timestamp. Consumers SHOULD
reject expired attestations and request fresh scoring.

Recommended validity periods:

| Context | Validity | Rationale |
|---------|----------|-----------|
| Real-time API | 1 hour | High-frequency, always fresh. |
| Batch processing | 24 hours | Daily risk assessment. |
| Compliance reporting | 7 days | Audit trail purposes. |

For aggregator-profile scores, `valid_until` SHOULD NOT exceed the
shortest `valid_until` of the contributing external signals. A signal
that is stale per [07-signal-aggregation.md](07-signal-aggregation.md)
§4.4 MUST NOT be counted in `signal_provenance` as though it were live.

---

## 5. Signal Provenance (NEW in v1.0)

When an aggregator-profile score is attested, the attestation MUST
include a `signal_provenance` block recording which external-signal
categories contributed to the External Signals (XS) component and how
many signals were consumed. This allows a consumer to audit the
aggregation without access to the raw signals.

### 5.1 Provenance Block

```json
"signal_provenance": {
  "xs_coverage": ["prompt_injection", "governance"],
  "signals_count": 2
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `xs_coverage` | MUST (aggregator) | Array of external-signal categories that contributed to the XS composite. One or more of the categories defined in [07-signal-aggregation.md](07-signal-aggregation.md) §2. |
| `signals_count` | MUST (aggregator) | Count of valid, non-stale signals fused into XS. |

### 5.2 When the Block Is Present

- An **aggregator-profile** attestation MUST include `signal_provenance`.
- A **core-profile** attestation MUST NOT include it, because a core
  profile does not consume external signals.
- If an aggregator produced a score with no available signals, it MUST
  still include the block with `"xs_coverage": []` and
  `"signals_count": 0`, and `components.external_signals` MUST be the
  neutral default `0.5` (see [01-scoring-model.md](01-scoring-model.md)
  §2.3 and [07-signal-aggregation.md](07-signal-aggregation.md) §4.3).
  An empty coverage array is itself an auditable fact: it tells the
  consumer that XS did not corroborate the internal score.

### 5.3 Relationship to the Detailed Signals Array

The `signal_provenance` block is the compact, always-present provenance
summary. For full auditability, an aggregator MAY additionally attach the
per-signal `signals` array defined in
[07-signal-aggregation.md](07-signal-aggregation.md) §6.1 — each entry
carrying `signal_id`, `category`, `provider_id`, `normalised_score`,
`weight_applied`, `computed_at`, and `included`. When both are present:

- `signal_provenance.xs_coverage` MUST equal the set of `category`
  values among entries with `"included": true`.
- `signal_provenance.signals_count` MUST equal the number of entries with
  `"included": true`.

A consumer that requires cryptographic re-verification of the XS
composite (recomputing XS from the individual signals) MUST use the
detailed `signals` array per document 07 §6.2. The compact block alone is
sufficient for coverage auditing but not for XS recomputation.

### 5.4 Consumer Use of Provenance

Consumers MAY require specific categories to be present in `xs_coverage`
before making a trust decision — for example, requiring
`prompt_injection` coverage for agents that process untrusted natural-
language input. A category defined in document 07 §2 but absent from
`xs_coverage` indicates a missing signal source, not a passing result.

---

## 6. W3C Verifiable Credential Format

For interoperability with existing identity and credential ecosystems,
TATF scores MAY be expressed as W3C Verifiable Credentials. (The
reference implementation emits TATF Native today; VC emission is planned
for a future reference release.)

### VC Mapping

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://tatf.dev/credentials/v1.0"
  ],
  "type": ["VerifiableCredential", "TATFTrustAttestation"],
  "issuer": "did:web:scorer.example.com",
  "validFrom": "2026-04-20T14:30:00Z",
  "validUntil": "2026-04-20T15:30:00Z",
  "credentialSubject": {
    "id": "did:web:agent.example.com",
    "type": "AutonomousAgent",
    "trustScore": {
      "alpha": 0.72,
      "confidenceLow": 0.65,
      "confidenceHigh": 0.79,
      "observationCount": 47,
      "coldStart": false,
      "profile": "aggregator",
      "specVersion": "tatf-v1.0.0"
    },
    "weights": {
      "AT": 0.30,
      "MS": 0.20,
      "TH": 0.25,
      "CS": 0.10,
      "XS": 0.15
    },
    "components": {
      "agentTrust": 0.85,
      "marketStability": 0.70,
      "transactionHistory": 0.60,
      "counterpartyScore": 0.50,
      "externalSignals": 0.83
    },
    "signalProvenance": {
      "xsCoverage": ["prompt_injection", "governance"],
      "signalsCount": 2
    },
    "behavioralRouting": "AUTO_PASS"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-04-20T14:30:00Z",
    "verificationMethod": "did:web:scorer.example.com#key-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z..."
  }
}
```

The `externalSignals` component and the `signalProvenance` object MUST be
present for aggregator-profile credentials and MUST be omitted for
core-profile credentials, mirroring the TATF Native rules in sections 4
and 5.

### DID Methods

For agent and issuer identification in the VC format:

| Entity | Recommended DID Method | Example |
|--------|------------------------|---------|
| Scorer (issuer) | `did:web` | `did:web:scorer.truce.dev` |
| Agent (subject) | `did:web` or `did:key` | `did:web:agent.firm.com` |
| Firm | `did:web` | `did:web:firm.com` |

---

## 7. Notarization (Transaction-Level Attestation)

In addition to trust attestations (agent-level), TATF defines
**notarization** for individual transactions.

### Nota Statement

A notarization attests that a transaction input (offer, order, etc.)
conforms to a declared schema:

> "The issuer attests: this [document_type] was received at {timestamp}
> and verified to conform to {schema_name} {schema_version} schema.
> The issuer attests to schema conformance ONLY."

### Notarization Pipeline

```
1. Receive document
2. Validate against declared schema
3. Canonicalize: sorted JSON, no whitespace
4. Hash: SHA-256 of canonical bytes
5. Sign: Ed25519(hash | timestamp)
6. Store: append to immutable nota ledger
```

### Nota Object

```json
{
  "nota_id": "NOTA-a3f8c1b7e2d4f5a9",
  "document_type": "offer",
  "schema": "TCOS v1.0",
  "nota_hash": "sha256:{hex}",
  "nota_timestamp": "2026-04-20T14:30:00Z",
  "nota_statement": "The issuer attests: this offer was received at ... and verified to conform to TCOS v1.0 schema. The issuer attests to schema conformance ONLY.",
  "signature": "{hex}",
  "agent_id": "string",
  "firm_id": "string"
}
```

### Key Distinction

| Type | Scope | Assertion |
|------|-------|-----------|
| Trust Attestation | Agent-level | "This agent has trust score X (derived from these signals)." |
| Notarization | Transaction-level | "This document conforms to schema Y." |

Both are cryptographically signed but serve different purposes. Trust
attestations inform routing decisions; notarizations provide an immutable
audit trail. Notarization attests to schema conformance ONLY — it makes
no claim about the truth of the document's content.

---

## 8. Verification

### Attestation Verification Steps

A consumer verifying a TATF attestation MUST:

1. **Check version:** `spec_version` is a supported TATF spec version
   (`"tatf-v1.0.0"` or a compatible v1 patch).
2. **Check validity:** `metadata.valid_until` >= current time.
3. **Resolve issuer key:** Obtain the issuer's public key (section 8.1).
4. **Reconstruct canonical form:** Re-canonicalize the payload, excluding
   the `proof` object.
5. **Verify hash:** `sha256:` + SHA-256(canonical) == `proof.hash`.
6. **Verify signature:** Reconstruct
   `sign_input = hash_hex + "|" + proof.signed_at`, then
   `Ed25519.verify(UTF-8(sign_input), signature, public_key)`.
7. **Check weight consistency:** `weights.*` sum to 1.0 and match the
   `profile`. An `"aggregator"` profile MUST carry a non-zero `XS`
   weight; a `"core"` profile MUST carry `XS = 0.00`.
8. **Check provenance (aggregator only):** `signal_provenance` is present,
   `components.external_signals` is present, and `signals_count` is
   consistent with `xs_coverage` (an empty coverage array requires
   `signals_count = 0` and `external_signals = 0.5`).

If any step fails, the attestation MUST be rejected.

A consumer that additionally requires XS to be independently recomputed
MUST obtain the detailed `signals` array (document 07 §6.1) and follow
the consumer verification procedure in document 07 §6.2, rejecting the
attestation if any signal signature is invalid, any signal is stale, or
the recomputed XS differs from the attested value beyond a floating-point
tolerance of `1e-6`.

### 8.1 Key Distribution

Issuer public keys MAY be distributed via:

- Direct exchange (API endpoint).
- DID resolution (for the VC format).
- Well-known URI: `/.well-known/tatf-keys.json`.

For aggregators, the profile, weight vector, and consumed connectors are
additionally published at `/.well-known/tatf-aggregator.json` (see
[07-signal-aggregation.md](07-signal-aggregation.md) §7.3). Consumers
SHOULD cross-check that an attestation's `profile`, `weights`, and
`xs_coverage` are consistent with the aggregator's published metadata.

---

*Next: [05-adversarial-testing.md](05-adversarial-testing.md) — Adversarial Testing*
