"""TRUCE — TATF reference implementation for local agent trust scoring.

Usage:
    from truce import TATFScorer

    scorer = TATFScorer()
    scorer.ingest("agent-123", transactions)
    result = scorer.score("agent-123")

    print(result.score)        # 0.72
    print(result.routing)      # AUTO_PASS
    print(result.confidence)   # (0.65, 0.79)
"""

__version__ = "0.1.0"

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
]
