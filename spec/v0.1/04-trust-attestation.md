# TATF v0.1 — Trust Attestation

## 1. Overview

A trust attestation is a cryptographically signed statement by a
TATF-compliant scorer asserting an agent's trust level at a specific
point in time. Attestations are the **output artifact** of the scoring
process — they are what consumers (platforms, counterparties, regulators)
use to make trust decisions.

TATF defines two attestation formats:
1. **TATF Native** — Minimal, purpose-built format for high-throughput environments
2. **W3C Verifiable Credential** — Standards-compliant format for interoperability

Implementations MUST support at least one format and SHOULD support both.

---

## 2. Attestation Semantics

### What an Attestation Asserts

A TATF attestation makes the following claim:

> "The issuer attests that agent {agent_id}, operated by firm {firm_id},
> was scored at {timestamp} using TATF {version} methodology and received
> a trust score of {score} with confidence interval [{ci_low}, {ci_high}]
> based on {observation_count} observations."

### What an Attestation Does NOT Assert

- The attestation does NOT guarantee future behavior
- The attestation does NOT verify the truth of the agent's commercial claims
- The attestation does NOT constitute regulatory approval
- The attestation does NOT replace due diligence

The attestation is a **point-in-time assessment** based on available data.

---

## 3. Cryptographic Requirements

### Signing Algorithm

Implementations MUST use one of:

| Algorithm | Key Size | Use Case |
|-----------|----------|----------|
| **Ed25519** (RECOMMENDED) | 256-bit | Default; fast, compact signatures |
| ECDSA P-256 | 256-bit | Interop with existing PKI |
| RSA-PSS | 2048-bit minimum | Legacy environments only |

### Signature Process

```
1. Canonicalize the attestation payload (deterministic serialization)
2. Compute SHA-256 hash of canonical form: hash = SHA-256(canonical_bytes)
3. Construct signing input: sign_input = hash_hex + "|" + iso8601_timestamp
   Example: "a3f8c1...b7e2|2026-03-13T14:30:00Z"
4. Sign: signature = Sign(UTF-8(sign_input), private_key)
5. Encode signature as hex string
```

**Signing input format:** The pipe-delimited concatenation of the hex-encoded
hash and the ISO 8601 timestamp ensures deterministic, reproducible signing
input across implementations. Both fields MUST be present.

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

This ensures byte-identical serialization across implementations.

---

## 4. TATF Native Format

### Attestation Object

```json
{
  "spec_version": "tatf-v0.1",
  "attestation_id": "ATT-{16-hex}",
  "issuer": {
    "id": "string",
    "name": "string",
    "public_key": "ed25519:{hex}"
  },
  "subject": {
    "agent_id": "string",
    "firm_id": "string"
  },
  "score": {
    "alpha": 0.72,
    "confidence_low": 0.65,
    "confidence_high": 0.79,
    "observation_count": 47,
    "cold_start": false
  },
  "components": {
    "agent_trust": 0.85,
    "market_stability": 0.70,
    "transaction_history": 0.60,
    "counterparty_score": 0.50
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
    "computed_at": "2026-03-13T14:30:00Z",
    "valid_until": "2026-03-13T15:30:00Z",
    "sector": "electronics",
    "counterparty_id": "string | null"
  },
  "proof": {
    "type": "Ed25519Signature",
    "hash": "sha256:{hex}",
    "signature": "{hex}",
    "signed_at": "2026-03-13T14:30:00Z"
  }
}
```

### Field Requirements

| Field | Required | Description |
|-------|----------|-------------|
| spec_version | MUST | Spec version string (e.g. "tatf-v0.1") |
| attestation_id | MUST | Unique identifier |
| issuer.id | MUST | Scorer identifier |
| issuer.public_key | MUST | Verification key |
| subject.agent_id | MUST | Scored agent |
| subject.firm_id | MUST | Agent's firm |
| score.alpha | MUST | ALPHA composite score |
| score.confidence_low | MUST | 95% CI lower bound |
| score.confidence_high | MUST | 95% CI upper bound |
| score.observation_count | MUST | Data points used |
| score.cold_start | MUST | Whether in cold start |
| components.* | MUST | All four ALPHA components |
| anomaly.composite | MUST | Behavioral anomaly score |
| anomaly.routing | MUST | ATBF zone |
| anomaly.dimensions.* | SHOULD | Six dimension breakdown |
| metadata.computed_at | MUST | ISO 8601 timestamp |
| metadata.valid_until | SHOULD | Attestation expiry |
| proof.type | MUST | Signature algorithm |
| proof.hash | MUST | Canonical payload hash |
| proof.signature | MUST | Cryptographic signature |

### Attestation Validity

Attestations SHOULD have a `valid_until` timestamp. Consumers SHOULD
reject expired attestations and request fresh scoring.

Recommended validity periods:

| Context | Validity | Rationale |
|---------|----------|-----------|
| Real-time API | 1 hour | High-frequency, always fresh |
| Batch processing | 24 hours | Daily risk assessment |
| Compliance reporting | 7 days | Audit trail purposes |

---

## 5. W3C Verifiable Credential Format

For interoperability with existing identity and credential ecosystems,
TATF scores MAY be expressed as W3C Verifiable Credentials.

### VC Mapping

```json
{
  "@context": [
    "https://www.w3.org/ns/credentials/v2",
    "https://tatf.dev/credentials/v0.1"
  ],
  "type": ["VerifiableCredential", "TATFTrustAttestation"],
  "issuer": "did:web:scorer.example.com",
  "validFrom": "2026-03-13T14:30:00Z",
  "validUntil": "2026-03-13T15:30:00Z",
  "credentialSubject": {
    "id": "did:web:agent.example.com",
    "type": "AutonomousAgent",
    "firmId": "string",
    "trustScore": {
      "alpha": 0.72,
      "confidenceLow": 0.65,
      "confidenceHigh": 0.79,
      "observationCount": 47,
      "coldStart": false,
      "specVersion": "tatf-v0.1"
    },
    "components": {
      "agentTrust": 0.85,
      "marketStability": 0.70,
      "transactionHistory": 0.60,
      "counterpartyScore": 0.50
    },
    "behavioralRouting": "AUTO_PASS"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-03-13T14:30:00Z",
    "verificationMethod": "did:web:scorer.example.com#key-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z..."
  }
}
```

### DID Methods

For agent and issuer identification in the VC format:

| Entity | Recommended DID Method | Example |
|--------|----------------------|---------|
| Scorer (issuer) | did:web | did:web:scorer.truce.dev |
| Agent (subject) | did:web or did:key | did:web:agent.firm.com |
| Firm | did:web | did:web:firm.com |

---

## 6. Notarization (Transaction-Level Attestation)

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
  "nota_id": "NOTA-{16-hex}",
  "document_type": "offer",
  "schema": "TCOS v1.0",
  "nota_hash": "sha256:{hex}",
  "nota_timestamp": "2026-03-13T14:30:00Z",
  "nota_statement": "The issuer attests: this offer was received at ... and verified to conform to TCOS v1.0 schema. The issuer attests to schema conformance ONLY.",
  "signature": "{hex}",
  "agent_id": "string",
  "firm_id": "string"
}
```

### Key Distinction

| Type | Scope | Assertion |
|------|-------|-----------|
| Trust Attestation | Agent-level | "This agent has trust score X" |
| Notarization | Transaction-level | "This document conforms to schema Y" |

Both are cryptographically signed but serve different purposes.
Trust attestations inform routing decisions; notarizations provide
an immutable audit trail.

---

## 7. Verification

### Attestation Verification Steps

A consumer verifying a TATF attestation MUST:

1. **Check validity:** `valid_until` >= current time
2. **Resolve issuer key:** Obtain the issuer's public key
3. **Reconstruct canonical form:** Re-canonicalize the payload
4. **Verify hash:** SHA-256 of canonical == `proof.hash`
5. **Verify signature:** Reconstruct `sign_input = hash_hex + "|" + signed_at`, then Ed25519.verify(UTF-8(sign_input), signature, public_key)
6. **Check version:** `tatf_version` is a supported spec version

If any step fails, the attestation MUST be rejected.

### Key Distribution

Issuer public keys MAY be distributed via:
- Direct exchange (API endpoint)
- DID resolution (for VC format)
- Well-known URI: `/.well-known/tatf-keys.json`

---

*Next: [05-adversarial-testing.md](05-adversarial-testing.md) — Adversarial Testing*
