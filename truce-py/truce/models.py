"""TATF data models — Pydantic models for scoring inputs and outputs.

Implements the output formats defined in TATF spec v0.1:
  - §01 Score Output Format
  - §02 Anomaly Score Output Format
  - §04 Trust Attestation Format
  - §06 AVX Output Format
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


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
    spec_version: str = "tatf-v0.1"


# ── ALPHA Score (composite trust score) ─────────────────────────


class AlphaComponents(BaseModel):
    """Four ALPHA components (spec §01)."""

    agent_trust: float = Field(ge=0, le=1, description="AT — inverted anomaly score")
    market_stability: float = Field(ge=0, le=1, description="MS — inverted AVX")
    transaction_history: float = Field(ge=0, le=1, description="TH — settlement rate")
    counterparty_score: float = Field(ge=0, le=1, description="CS — counterparty AT")


class AlphaScore(BaseModel):
    """TATF ALPHA composite trust score (spec §01)."""

    agent_id: str
    score: float = Field(ge=0, le=1, description="ALPHA composite (0-1)")
    confidence_low: float = Field(ge=0, le=1)
    confidence_high: float = Field(ge=0, le=1)
    components: AlphaComponents
    observation_count: int = Field(ge=0)
    cold_start: bool = False
    tier: TrustTier = TrustTier.MODERATE
    counterparty_id: Optional[str] = None
    sector: Optional[str] = None
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spec_version: str = "tatf-v0.1"

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
    spec_version: str = "tatf-v0.1"


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
