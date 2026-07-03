"""TRUCE — TATF reference implementation for local agent trust scoring.

Usage:
    from tatf import TATFScorer

    scorer = TATFScorer()
    scorer.ingest("agent-123", transactions)
    result = scorer.score("agent-123")

    print(result.score)        # 0.72
    print(result.routing)      # AUTO_PASS
    print(result.confidence)   # (0.65, 0.79)
"""

__version__ = "0.1.0"

from .aggregator import FusionEntry, FusionResult, SignalAggregator
from .attestation import TATFAttestor
from .avx import AVXCalculator, AVXEvent
from .models import (
    AgentBaseline,
    AlphaComponents,
    AlphaScore,
    AnomalyDimensions,
    AnomalyScore,
    AVXDimensions,
    AVXScore,
    RoutingDecision,
    ScorerProfile,
    Signal,
    SignalCategory,
    SignalDirection,
    Transaction,
    TrustTier,
)
from .scorer import TATFScorer

__all__ = [
    # Core
    "TATFScorer",
    "TATFAttestor",
    "AVXCalculator",
    "AVXEvent",
    "SignalAggregator",
    # Models
    "AlphaScore",
    "AlphaComponents",
    "AnomalyScore",
    "AnomalyDimensions",
    "AgentBaseline",
    "AVXScore",
    "AVXDimensions",
    "Transaction",
    "RoutingDecision",
    "TrustTier",
    # External signals (v1.0)
    "Signal",
    "SignalCategory",
    "SignalDirection",
    "ScorerProfile",
    "FusionResult",
    "FusionEntry",
]
