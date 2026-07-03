# TATF v1.0 — Signal Aggregation

*New in v1.0.* This document defines how TATF implementations incorporate
**external signals** from specialised trust and security providers into
the composite trust score.

---

## 1. Overview

TATF's internal layers (observable metrics, behavioural baselines,
community signals) cover a meaningful portion of the trust surface,
but specialised providers cover domains TATF does not:

- **Prompt-injection and jailbreak detection** — e.g. Lakera Guard.
- **Governance maturity and auditability** — e.g. Collibra AI Trust
  Score.
- **Runtime threat detection** — enterprise agent-security stacks
  (Check Point / CrowdStrike-tier).
- **Attestation verification of agent model provenance** — hardware
  attestation providers, supply-chain signal vendors.

An **aggregator** is a TATF implementation that combines its own
layer outputs with one or more of these external signals into a
single composite score. The aggregator publishes which signals it
consumed (signal provenance) so consumers can reason about coverage.

### Why a Contract, Not a Closed Integration

Proprietary integrations lock scoring into a single vendor stack.
A public contract:

- Keeps the scoring methodology open.
- Lets any provider participate with a conformant connector.
- Lets consumers verify that published scores reflect the signals
  claimed.
- Supports competition and comparison between providers.

The contract is deliberately minimal: an HTTP-level schema, a
normalisation rule, and a fusion formula. Signal semantics remain
with the provider.

---

## 2. Signal Categories

TATF v1.0 recognises six categories. New categories MAY be added
in later versions via RFC.

| Category | Description | Example Providers |
|----------|-------------|-------------------|
| `prompt_injection` | Detection of adversarial input attempting to manipulate agent behaviour. | Lakera Guard, Robust Intelligence. |
| `governance` | Maturity of the agent operator's governance and documentation. | Collibra, IBM watsonx.governance. |
| `runtime_threat` | Real-time detection of compromised or malicious agent behaviour. | CrowdStrike-tier runtime agents, Check Point CloudGuard + Lakera. |
| `supply_chain` | Provenance and integrity of agent model, tools, and dependencies. | Hardware attestation, model registry signers. |
| `regulatory_flag` | Regulatory-listing status (sanctions, enforcement actions). | Compliance data providers. |
| `network_reputation` | Historical incident and dispute data from cross-platform networks. | Community registries, shared incident databases. |

Aggregators MUST declare which categories they consume. Consumers
of scores MAY require specific categories to be present for trust
decisions.

---

## 3. Signal Contract

### 3.1 Signal Object

Each external signal consumed by an aggregator MUST conform to:

```json
{
  "spec_version": "tatf-signal-v1.0",
  "signal_id": "SIG-{16-hex}",
  "category": "prompt_injection",
  "provider": {
    "id": "string",
    "name": "string",
    "public_key": "ed25519:{hex}"
  },
  "subject": {
    "agent_id": "string",
    "firm_id": "string"
  },
  "score": {
    "value": 0.12,
    "direction": "risk",
    "scale": "[0,1]",
    "confidence": 0.95
  },
  "evidence": {
    "sample_count": 340,
    "detection_rate": 0.12,
    "lookback_hours": 24
  },
  "metadata": {
    "computed_at": "2026-04-20T14:30:00Z",
    "valid_until": "2026-04-20T15:30:00Z"
  },
  "proof": {
    "type": "Ed25519Signature",
    "signature": "{hex}"
  }
}
```

### 3.2 Field Requirements

| Field | Required | Description |
|-------|----------|-------------|
| `spec_version` | MUST | Signal contract version. |
| `category` | MUST | One of the categories in section 2. |
| `provider.id` | MUST | Stable identifier for the provider. |
| `provider.public_key` | MUST | Verification key for the signature. |
| `subject.agent_id` | MUST | Agent the signal pertains to. |
| `score.value` | MUST | Numeric score. |
| `score.direction` | MUST | `"risk"` (higher = worse) or `"trust"` (higher = better). |
| `score.scale` | MUST | Scale declaration; `"[0,1]"` is RECOMMENDED. |
| `score.confidence` | SHOULD | Provider's confidence in the signal ([0,1]). |
| `evidence.*` | SHOULD | Minimal supporting data. |
| `metadata.computed_at` | MUST | ISO 8601 timestamp. |
| `metadata.valid_until` | SHOULD | Expiry timestamp. |
| `proof.signature` | MUST | Signature over canonical payload. |

### 3.3 Direction and Normalisation

Different providers use different conventions (higher-is-worse,
higher-is-better, arbitrary scales). Signals MUST be normalised to
a **trust-oriented** float in `[0,1]` (higher = better) before
fusion.

```
if signal.score.direction == "risk":
    normalised = 1.0 - clamp(signal.score.value, 0, max_scale) / max_scale
elif signal.score.direction == "trust":
    normalised = clamp(signal.score.value, 0, max_scale) / max_scale

normalised = max(0.0, min(1.0, normalised))
```

Where `max_scale` is inferred from `signal.score.scale` (e.g.
`"[0,1]"` → 1.0, `"[0,100]"` → 100.0).

Example: Lakera Guard returns a prompt-injection *risk* score in
`[0,1]`. A raw value of `0.12` normalises to `0.88` (trust-oriented).

---

## 4. Fusion: The XS Composite

An aggregator combines normalised signals into a single **XS**
(External Signal) component. XS is the fifth component of the
ALPHA composite score (document 01, section 2).

### 4.1 Default Weighted Average

```
categories_with_signals = {c : signals for c, signals in inbox}

for each category c:
    category_score[c] = weighted_mean(
        [normalised(s) for s in signals[c]],
        weights=[s.score.confidence for s in signals[c]]
    )

XS = weighted_mean(
    [category_score[c] for c in categories_with_signals],
    weights=[CATEGORY_WEIGHT[c] for c in categories_with_signals]
)
```

### 4.2 Default Category Weights

| Category | Weight |
|----------|--------|
| `prompt_injection` | 0.25 |
| `runtime_threat` | 0.25 |
| `governance` | 0.15 |
| `supply_chain` | 0.15 |
| `regulatory_flag` | 0.10 |
| `network_reputation` | 0.10 |

Weights sum to 1.0 across *categories with signals present*.
Aggregators MAY customise weights within documented rationale.

### 4.3 Missing Signals

If no external signals are available for any category, `XS = 0.5`
(neutral default). The aggregator MUST flag the absence in the
attestation output (section 6).

If some but not all categories have signals, available-category
weights are renormalised to sum to 1.0.

### 4.4 Stale Signals

A signal is **stale** if `metadata.valid_until < current_time` or
if `computed_at` is older than the aggregator's configured maximum
age (RECOMMENDED: 1 hour for `runtime_threat`, 24 hours for
`prompt_injection`, 7 days for `governance`).

Stale signals MUST be excluded from fusion. If all signals in a
category are stale, the category is treated as absent (section 4.3).

---

## 5. ALPHA with External Signals

Document 01 defines ALPHA as a five-component composite. When XS
is incorporated:

```
ALPHA = w_AT * AT + w_MS * MS + w_TH * TH + w_CS * CS + w_XS * XS
```

### 5.1 Recommended Weights (v1.0 Aggregator Profile)

| Component | Weight | Range | Source |
|-----------|--------|-------|--------|
| AT (Agent Trust) | 0.30 | [0, 1] | Inverted anomaly score. |
| MS (Market Stability) | 0.20 | [0, 1] | Inverted AVX. |
| TH (Transaction History) | 0.25 | [0, 1] | Settlement rate. |
| CS (Counterparty Score) | 0.10 | [0, 1] | Counterparty AT. |
| **XS (External Signals)** | **0.15** | **[0, 1]** | **This document.** |

### 5.2 Core-Only Profile (Backward Compatible with v0.1)

Aggregators that do not incorporate external signals MUST use the
v0.1 weights (AT 0.35, MS 0.25, TH 0.25, CS 0.15) and MUST declare
themselves as "TATF v1.0 core" rather than "TATF v1.0 aggregator".

---

## 6. Signal Provenance in Attestations

Attestations produced by aggregators MUST include signal provenance
so consumers can audit which signals influenced the score.

### 6.1 Attestation Extension

The trust attestation object (document 04) gains an optional
`signals` array:

```json
{
  "...": "...",
  "signals": [
    {
      "signal_id": "SIG-a3f8c1b7e2d4f5a9",
      "category": "prompt_injection",
      "provider_id": "lakera",
      "normalised_score": 0.88,
      "weight_applied": 0.25,
      "computed_at": "2026-04-20T14:30:00Z",
      "included": true
    },
    {
      "signal_id": "SIG-b9c7d1e4a2f8",
      "category": "governance",
      "provider_id": "collibra",
      "normalised_score": 0.72,
      "weight_applied": 0.15,
      "computed_at": "2026-04-19T09:00:00Z",
      "included": true
    }
  ],
  "xs_composite": 0.83,
  "xs_coverage": ["prompt_injection", "governance"]
}
```

The `xs_coverage` array lists categories that contributed to the
XS composite. Categories listed in section 2 but absent from
coverage indicate missing signal sources.

### 6.2 Consumer Verification

A consumer verifying an attestation with signal provenance:

1. Verifies the outer attestation signature (document 04).
2. For each entry in `signals`, resolves the provider's public key.
3. Verifies the signal's signature against its provider key.
4. Recomputes `xs_composite` using the published normalisation and
   fusion formulas; verifies it matches the attestation value.
5. Rejects the attestation if any signal signature is invalid, any
   signal is stale per section 4.4, or if the recomputed XS value
   differs from the attested value beyond floating-point tolerance
   (1e-6).

---

## 7. Connector Architecture

Aggregators SHOULD implement signal consumption via a **connector**
abstraction. Connectors are stateless, single-responsibility
adapters between a specific provider's API and the TATF signal
contract.

### 7.1 Connector Contract

```
connector.fetch(agent_id, category, max_age_seconds) -> Signal | None
```

A connector:

- **MUST** accept the TATF agent identifier and translate to the
  provider's identifier if different.
- **MUST** return a signal that conforms to section 3.1, or `None`
  if no signal is available within `max_age_seconds`.
- **MUST** verify the provider's signature before returning.
- **SHOULD** cache recent signals to reduce provider API load.
- **SHOULD** implement exponential backoff on provider errors.
- **MUST NOT** block the aggregator's scoring path for more than
  a configured timeout (RECOMMENDED: 500ms).

### 7.2 Provider-Side Contribution

Signal providers SHOULD expose a TATF-conformant endpoint returning
the contract object from section 3.1. Providers MAY also serve
existing proprietary APIs; connectors handle translation.

A "TATF-native" provider endpoint is a simple mapping from internal
score → contract schema + Ed25519 signing. A reference connector
template is included with the reference implementation.

### 7.3 Aggregator Registration

An aggregator publishing signed attestations SHOULD maintain a
well-known metadata endpoint:

```
GET /.well-known/tatf-aggregator.json
```

Returning:

```json
{
  "aggregator_id": "string",
  "public_key": "ed25519:{hex}",
  "spec_version": "tatf-v1.0.0",
  "profile": "aggregator",
  "connectors": [
    {"category": "prompt_injection", "provider_id": "lakera"},
    {"category": "governance", "provider_id": "collibra"}
  ],
  "weights": {
    "AT": 0.30, "MS": 0.20, "TH": 0.25, "CS": 0.10, "XS": 0.15
  }
}
```

This allows consumers and regulators to audit which signals a given
aggregator consumes.

---

## 8. Failure Handling

### 8.1 Provider Unavailable

If a connector cannot reach its provider within the configured
timeout, the aggregator MUST:

- Treat the category as absent for this scoring event.
- Log the provider outage with the signal request timestamp.
- Continue scoring with remaining signals; do not fail the scoring
  call.

### 8.2 Invalid Signal

If a signal fails signature verification or contract validation:

- The signal MUST be excluded from fusion.
- The event MUST be logged for operator review.
- The aggregator SHOULD alert if a provider repeatedly emits
  invalid signals.

### 8.3 Rate Limiting and Back-Pressure

Connectors MUST respect provider rate limits. If a provider returns
`429 Too Many Requests`, the connector MUST apply exponential
backoff and MAY serve from cache during the backoff window (if
cache is still fresh per section 4.4).

---

## 9. Privacy Considerations

### 9.1 Minimising Data to Providers

Connectors SHOULD send only the minimum information required for
the provider to compute its signal. In particular:

- Agent identifiers MAY be hashed before transmission if the
  provider does not require the raw identifier.
- Transaction details (amounts, counterparties) SHOULD NOT be
  transmitted to signal providers unless the provider's signal
  category requires them (rare for `prompt_injection`, `governance`,
  `supply_chain`).

### 9.2 Signal Provenance and PII

Signal provenance (section 6) reveals which providers scored an
agent. Agents and principals SHOULD be informed of signal-provider
relationships at onboarding (a straightforward privacy-notice
item).

### 9.3 Cross-Aggregator Consistency

Two aggregators consuming the same set of signals SHOULD produce
identical XS composites if they use identical weights. This is
explicitly designed for auditability — divergent XS values from
the same signals indicate a configuration difference that
consumers can detect.

---

## 10. Reference Connector Example (Lakera Guard)

A minimal Lakera Guard connector, in pseudocode:

```python
class LakeraConnector:
    category = "prompt_injection"
    provider_id = "lakera"

    def fetch(self, agent_id, category, max_age_seconds):
        if category != self.category:
            return None

        # Provider-side call (simplified)
        resp = lakera_api.get_agent_risk(agent_id, lookback=24*3600)
        if resp.timestamp < now() - max_age_seconds:
            return None

        signal = {
            "spec_version": "tatf-signal-v1.0",
            "signal_id": f"SIG-{random_hex(16)}",
            "category": "prompt_injection",
            "provider": {
                "id": "lakera",
                "name": "Lakera Guard",
                "public_key": LAKERA_PUBLIC_KEY,
            },
            "subject": {"agent_id": agent_id, "firm_id": resp.firm_id},
            "score": {
                "value": resp.risk_score,
                "direction": "risk",
                "scale": "[0,1]",
                "confidence": resp.confidence,
            },
            "evidence": {
                "sample_count": resp.samples,
                "detection_rate": resp.detection_rate,
                "lookback_hours": 24,
            },
            "metadata": {
                "computed_at": resp.timestamp,
                "valid_until": resp.timestamp + 3600,
            },
        }
        signal["proof"] = sign(canonical(signal), LAKERA_PRIVATE_KEY)
        return signal
```

The reference implementation (`truce-py`) ships this and other
connectors as optional plugins; see `truce/connectors/`.

---

## 11. Conformance Requirements

A TATF v1.0 **aggregator** implementation:

- **MUST** implement at least one connector per the contract in
  section 7.
- **MUST** normalise signals per section 3.3 before fusion.
- **MUST** compute XS per section 4 and incorporate into ALPHA per
  section 5.
- **MUST** include signal provenance in attestations per section 6.
- **MUST** expose `/.well-known/tatf-aggregator.json` per section 7.3.
- **MUST** handle provider failures without failing the scoring
  call (section 8).
- **SHOULD** implement at least two signal categories to be marketed
  as an aggregator.

A TATF v1.0 **core** implementation (no aggregation):

- **MUST NOT** advertise signal aggregation.
- **MAY** consume community-contributed connectors for experimentation
  without claiming aggregator conformance.

---

*Next: [08-regulatory-mapping.md](08-regulatory-mapping.md) — Regulatory Mapping Detail*
