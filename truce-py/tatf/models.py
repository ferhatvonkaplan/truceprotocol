"""TATF data models — Pydantic models for scoring inputs and outputs.

Implements the output formats defined in TATF spec v1.0:
  - §01 Score Output Format (5-component ALPHA)
  - §02 Anomaly Score Output Format
  - §04 Trust Attestation Format (with signal provenance)
  - §06 AVX Output Format
  - §07 External Signal Contract (NEW in v1.0)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────


class RoutingDecision(str, Enum):
    """ATBF zone routing decisions (spec §03)."""

    AUTO_PASS = "AUTO_PASS"
    SOFT_HOLD = "SOFT_HOLD"
    HARD_BLOCK = "HARD_BLOCK"


class TrustTier(str, Enum):
    """Human-readable trust tier (spec §01)."""

    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    CRITICAL = "CRITICAL"


class ScorerProfile(str, Enum):
    """TATF implementation profile (spec §01, NEW in v1.0).

    * ``core`` — internal signals only; backward-compatible with v0.1 weights.
    * ``aggregator`` — consumes at least one external signal category.
    """

    CORE = "core"
    AGGREGATOR = "aggregator"


class SignalCategory(str, Enum):
    """External signal categories (spec §07)."""

    PROMPT_INJECTION = "prompt_injection"
    GOVERNANCE = "governance"
    RUNTIME_THREAT = "runtime_threat"
    SUPPLY_CHAIN = "supply_chain"
    REGULATORY_FLAG = "regulatory_flag"
    NETWORK_REPUTATION = "network_reputation"


class SignalDirection(str, Enum):
    """Direction of an external signal's numeric value (spec §07)."""

    RISK = "risk"    # Higher value = worse (inverted before fusion)
    TRUST = "trust"  # Higher value = better (used directly)


# ── Anomaly Score (Layer 2 output) ──────────────────────────────


class AnomalyDimensions(BaseModel):
    """Six-dimension breakdown of behavioral anomaly score (spec §02)."""

    s_time: float = Field(ge=0, le=35, description="Time anomaly (cap 35)")
    s_concurrent: float = Field(ge=0, le=45, description="Concurrent sessions (cap 45)")
    s_price: float = Field(ge=0, le=40, description="Price deviation (cap 40)")
    s_category: float = Field(ge=0, le=30, description="Category anomaly (0 or 30)")
    s_rounds: float = Field(ge=0, le=25, description="Negotiation rounds (0 or 25)")
    s_counterparty: float = Field(ge=0, le=25, description="Counterparty concentration (cap 25)")


class AnomalyScore(BaseModel):
    """Composite anomaly score with routing decision (spec §02-03)."""

    agent_id: str
    composite: float = Field(ge=0, le=200)
    dimensions: AnomalyDimensions
    routing: RoutingDecision
    cold_start: bool = False
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spec_version: str = "tatf-v1.0.0"


# ── External Signal (Layer 4 — NEW in v1.0) ─────────────────────


class SignalProvider(BaseModel):
    """External signal provider identity (spec §07.3)."""

    id: str
    name: str = ""
    public_key: str = ""  # "ed25519:{hex}" when available


class SignalScore(BaseModel):
    """Provider's raw score for a subject agent (spec §07.3)."""

    value: float
    direction: SignalDirection
    scale: str = "[0,1]"
    confidence: float = Field(default=1.0, ge=0, le=1)


class SignalSubject(BaseModel):
    """The agent being scored by an external signal."""

    agent_id: str
    firm_id: str = ""


class SignalEvidence(BaseModel):
    """Optional supporting data for an external signal."""

    sample_count: Optional[int] = None
    detection_rate: Optional[float] = None
    lookback_hours: Optional[float] = None


class SignalMetadata(BaseModel):
    """Timing metadata for an external signal."""

    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None


class Signal(BaseModel):
    """External trust signal from a TATF-compatible provider (spec §07.1).

    A signal is the unit of data flowing from a third-party provider
    (e.g. Lakera, Collibra) into a TATF aggregator.
    """

    spec_version: str = "tatf-signal-v1.0"
    signal_id: str
    category: SignalCategory
    provider: SignalProvider
    subject: SignalSubject
    score: SignalScore
    evidence: SignalEvidence = Field(default_factory=SignalEvidence)
    metadata: SignalMetadata = Field(default_factory=SignalMetadata)
    proof: Optional[Dict[str, str]] = None

    def normalized_score(self) -> float:
        """Normalize the signal to trust-oriented [0, 1] (higher = better).

        Spec §07.3 normalisation rule.

        Returns
        -------
        float
            Normalised score in [0, 1] where 1.0 means maximum trust.
        """
        # Parse the scale declaration; default to [0,1] if malformed.
        try:
            cleaned = self.score.scale.strip().strip("[]")
            parts = [p.strip() for p in cleaned.split(",")]
            lo = float(parts[0]) if len(parts) >= 1 else 0.0
            hi = float(parts[1]) if len(parts) >= 2 else 1.0
            span = hi - lo if hi > lo else 1.0
        except (ValueError, IndexError):
            lo, hi, span = 0.0, 1.0, 1.0

        clamped = max(lo, min(hi, self.score.value))
        raw = (clamped - lo) / span

        if self.score.direction == SignalDirection.RISK:
            trust_oriented = 1.0 - raw
        else:
            trust_oriented = raw

        return max(0.0, min(1.0, trust_oriented))

    def is_stale(self, max_age_seconds: int = 3600) -> bool:
        """Return True if this signal is stale per spec §07.4."""
        now = datetime.now(timezone.utc)

        if self.metadata.valid_until is not None and now > self.metadata.valid_until:
            return True

        age = (now - self.metadata.computed_at).total_seconds()
        return age > max_age_seconds


# ── ALPHA Score (composite trust score) ─────────────────────────


class AlphaComponents(BaseModel):
    """ALPHA components (spec §01, extended in v1.0).

    Core-profile implementations leave ``external_signals`` unset
    (``None``). Aggregator-profile implementations MUST set it.
    """

    agent_trust: float = Field(ge=0, le=1, description="AT — inverted anomaly score")
    market_stability: float = Field(ge=0, le=1, description="MS — inverted AVX")
    transaction_history: float = Field(ge=0, le=1, description="TH — settlement rate")
    counterparty_score: float = Field(ge=0, le=1, description="CS — counterparty AT")
    external_signals: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="XS — aggregated external signals (aggregator profile only)",
    )


class AlphaScore(BaseModel):
    """TATF ALPHA composite trust score (spec §01 v1.0)."""

    agent_id: str
    score: float = Field(ge=0, le=1, description="ALPHA composite (0-1)")
    confidence_low: float = Field(ge=0, le=1)
    confidence_high: float = Field(ge=0, le=1)
    components: AlphaComponents
    weights: Dict[str, float] = Field(
        default_factory=lambda: {"AT": 0.35, "MS": 0.25, "TH": 0.25, "CS": 0.15, "XS": 0.0},
        description="Weight vector actually applied to this score.",
    )
    profile: ScorerProfile = Field(
        default=ScorerProfile.CORE,
        description="Scorer profile: 'core' (no external signals) or 'aggregator'.",
    )
    observation_count: int = Field(ge=0)
    cold_start: bool = False
    tier: TrustTier = TrustTier.MODERATE
    counterparty_id: Optional[str] = None
    sector: Optional[str] = None
    xs_coverage: List[str] = Field(
        default_factory=list,
        description="Categories that contributed to XS (aggregator profile only).",
    )
    signals_count: int = Field(
        default=0, ge=0, description="Count of valid, non-stale signals consumed."
    )
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spec_version: str = "tatf-v1.0.0"

    @property
    def confidence(self) -> Tuple[float, float]:
        """Convenience property returning (ci_low, ci_high)."""
        return (self.confidence_low, self.confidence_high)

    @property
    def routing(self) -> RoutingDecision:
        """Derive routing from the AT component's underlying anomaly."""
        at = self.components.agent_trust
        anomaly = (1.0 - at) * 200.0
        if anomaly < 50:
            return RoutingDecision.AUTO_PASS
        elif anomaly < 120:
            return RoutingDecision.SOFT_HOLD
        return RoutingDecision.HARD_BLOCK


# ── AVX (market stress) ─────────────────────────────────────────


class AVXDimensions(BaseModel):
    """Four AVX sub-scores (spec §06)."""

    pd_score: float = Field(ge=0, le=100, description="Panic Diversification")
    pv_score: float = Field(ge=0, le=100, description="Price Volatility")
    da_score: float = Field(ge=0, le=100, description="Demand Acceleration")
    cr_score: float = Field(ge=0, le=100, description="Cancellation Rate")


class AVXScore(BaseModel):
    """AVX market stress indicator (spec §06)."""

    sector: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avx_score: float = Field(ge=0, le=100)
    dimensions: AVXDimensions
    unique_firms: int
    event_count: int
    lookback_hours: float = 2.0
    k_anonymity_satisfied: bool
    spec_version: str = "tatf-v1.0.0"


# ── Baseline ─────────────────────────────────────────────────────


class AgentBaseline(BaseModel):
    """Per-agent behavioral baseline maintained via EMA (spec §02)."""

    agent_id: str
    observation_days: int = 0
    transaction_count: int = 0
    time_mean: float = 12.0
    time_std: float = 4.0
    concurrent_mean: float = 1.0
    concurrent_std: float = 0.5
    price_mean: float = 0.0
    price_std: float = 1.0
    rounds_p95: float = 5.0
    known_categories: List[str] = Field(default_factory=list)
    counterparty_counts: Dict[str, int] = Field(default_factory=dict)
    settled_count: int = 0
    total_count: int = 0
    first_seen: Optional[datetime] = None
    last_updated: Optional[datetime] = None


# ── Transaction input ────────────────────────────────────────────


class Transaction(BaseModel):
    """A single agent transaction for ingestion."""

    timestamp: datetime
    price: float
    quantity: float = 1.0
    product_code: str = ""
    category: str = ""
    counterparty_id: str = ""
    concurrent_sessions: int = 1
    negotiation_rounds: int = 1
    cancelled: bool = False
    settled: bool = True
    currency: str = "USD"
