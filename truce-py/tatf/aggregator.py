"""TATF Signal Aggregator — External signal fusion (spec §07).

The aggregator combines :class:`Signal` objects from multiple providers
(Lakera, Collibra, CrowdStrike-tier, etc.) into the XS (External Signals)
composite component of the ALPHA score.

Reference implementation of TATF v1.0 spec §07:
  - §07.3 Normalisation
  - §07.4 Fusion algorithm
  - §07.4.3 Missing-signal handling
  - §07.4.4 Stale-signal detection

Typical usage::

    from tatf import SignalAggregator, Signal

    aggregator = SignalAggregator()
    result = aggregator.fuse(signals)
    print(result.xs_composite)      # 0.83
    print(result.xs_coverage)       # ['prompt_injection', 'governance']
    print(result.signals_count)     # 2

The aggregator never raises on partial failure; missing categories
fall back to neutral (0.5) and stale signals are silently excluded.
All exclusion events are surfaced in ``result.excluded`` for logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from .models import Signal, SignalCategory


# ── Defaults from spec §07.4.2 and §07.4.4 ──────────────────────

DEFAULT_CATEGORY_WEIGHTS: Dict[SignalCategory, float] = {
    SignalCategory.PROMPT_INJECTION: 0.25,
    SignalCategory.RUNTIME_THREAT: 0.25,
    SignalCategory.GOVERNANCE: 0.15,
    SignalCategory.SUPPLY_CHAIN: 0.15,
    SignalCategory.REGULATORY_FLAG: 0.10,
    SignalCategory.NETWORK_REPUTATION: 0.10,
}

# Per-category default maximum age in seconds (spec §07.4.4).
DEFAULT_MAX_AGE_SECONDS: Dict[SignalCategory, int] = {
    SignalCategory.RUNTIME_THREAT: 3600,           # 1 hour
    SignalCategory.PROMPT_INJECTION: 86_400,       # 24 hours
    SignalCategory.GOVERNANCE: 604_800,            # 7 days
    SignalCategory.SUPPLY_CHAIN: 604_800,          # 7 days
    SignalCategory.REGULATORY_FLAG: 604_800,       # 7 days
    SignalCategory.NETWORK_REPUTATION: 604_800,    # 7 days
}

# Neutral default when no signals are available (spec §07.4.3).
NEUTRAL_XS: float = 0.5


# ── Result objects ──────────────────────────────────────────────


@dataclass
class FusionEntry:
    """One signal's contribution to the XS composite."""

    signal_id: str
    category: SignalCategory
    provider_id: str
    normalized_score: float
    weight_applied: float
    computed_at: str
    included: bool = True
    reason: str = ""


@dataclass
class FusionResult:
    """Output of :meth:`SignalAggregator.fuse`.

    Attributes
    ----------
    xs_composite : float
        The XS value in [0, 1]; 0.5 when no signals available.
    xs_coverage : list[str]
        Categories that contributed non-zero weight to xs_composite.
    signals_count : int
        Count of signals included in fusion (valid + non-stale).
    included : list[FusionEntry]
        Entries for signals that contributed to the composite.
    excluded : list[FusionEntry]
        Entries for signals excluded (stale, invalid, wrong category).
    category_scores : dict[str, float]
        Per-category scores (within-category weighted means).
    neutral_fallback : bool
        True when no signals were available and xs_composite == 0.5.
    """

    xs_composite: float
    xs_coverage: List[str]
    signals_count: int
    included: List[FusionEntry] = field(default_factory=list)
    excluded: List[FusionEntry] = field(default_factory=list)
    category_scores: Dict[str, float] = field(default_factory=dict)
    neutral_fallback: bool = False


# ── Aggregator ──────────────────────────────────────────────────


class SignalAggregator:
    """Aggregates external signals into an XS composite (spec §07.4).

    Parameters
    ----------
    category_weights : dict, optional
        Per-category weights used when fusing across categories.
        Defaults to :data:`DEFAULT_CATEGORY_WEIGHTS`.
    max_age_seconds : dict, optional
        Per-category maximum signal age in seconds. Defaults to
        :data:`DEFAULT_MAX_AGE_SECONDS`.
    """

    def __init__(
        self,
        category_weights: Optional[Dict[SignalCategory, float]] = None,
        max_age_seconds: Optional[Dict[SignalCategory, int]] = None,
    ) -> None:
        self._category_weights = dict(category_weights or DEFAULT_CATEGORY_WEIGHTS)
        self._max_age = dict(max_age_seconds or DEFAULT_MAX_AGE_SECONDS)

        # Validate weights; they don't need to sum to 1.0 because we
        # renormalise over available categories at fusion time (spec §07.4.3).
        for cat, w in self._category_weights.items():
            if w < 0:
                raise ValueError(f"category weight for {cat} must be >= 0 (got {w})")

    # ── Public API ───────────────────────────────────────────

    def fuse(self, signals: Sequence[Signal]) -> FusionResult:
        """Fuse a sequence of signals into an XS composite (spec §07.4).

        Steps:
          1. Filter out stale signals (spec §07.4.4).
          2. Group valid signals by category.
          3. Within each category: weighted mean by confidence.
          4. Across categories: weighted mean by category weights,
             renormalised over present categories.
          5. Return composite + coverage + audit trail.
        """
        included: List[FusionEntry] = []
        excluded: List[FusionEntry] = []
        by_category: Dict[SignalCategory, List[Signal]] = {}

        # ── Step 1-2: filter + group ──
        for sig in signals:
            entry_base = FusionEntry(
                signal_id=sig.signal_id,
                category=sig.category,
                provider_id=sig.provider.id,
                normalized_score=sig.normalized_score(),
                weight_applied=0.0,
                computed_at=sig.metadata.computed_at.isoformat(),
            )

            max_age = self._max_age.get(sig.category, 86_400)
            if sig.is_stale(max_age_seconds=max_age):
                entry_base.included = False
                entry_base.reason = "stale"
                excluded.append(entry_base)
                continue

            if sig.category not in self._category_weights:
                entry_base.included = False
                entry_base.reason = "unknown_category"
                excluded.append(entry_base)
                continue

            by_category.setdefault(sig.category, []).append(sig)

        # ── Step 3: within-category means ──
        category_scores: Dict[SignalCategory, float] = {}
        for cat, cat_signals in by_category.items():
            total_conf = sum(s.score.confidence for s in cat_signals)
            if total_conf <= 0:
                # All-zero confidence: treat as unweighted arithmetic mean.
                mean = sum(s.normalized_score() for s in cat_signals) / len(cat_signals)
            else:
                mean = sum(
                    s.normalized_score() * s.score.confidence for s in cat_signals
                ) / total_conf
            category_scores[cat] = mean

        # ── Step 4: across-category weighted mean ──
        if not category_scores:
            return FusionResult(
                xs_composite=NEUTRAL_XS,
                xs_coverage=[],
                signals_count=0,
                included=[],
                excluded=excluded,
                category_scores={},
                neutral_fallback=True,
            )

        total_cat_weight = sum(
            self._category_weights[cat] for cat in category_scores
        )

        if total_cat_weight <= 0:
            # Shouldn't happen with validated weights, but defensive.
            xs = NEUTRAL_XS
        else:
            xs = sum(
                category_scores[cat]
                * (self._category_weights[cat] / total_cat_weight)
                for cat in category_scores
            )

        xs = max(0.0, min(1.0, xs))

        # ── Audit trail: record per-signal weight_applied ──
        for cat, cat_signals in by_category.items():
            cat_weight_fraction = self._category_weights[cat] / total_cat_weight
            total_conf = sum(s.score.confidence for s in cat_signals)
            for s in cat_signals:
                if total_conf > 0:
                    within_fraction = s.score.confidence / total_conf
                else:
                    within_fraction = 1.0 / len(cat_signals)
                effective_weight = cat_weight_fraction * within_fraction
                included.append(
                    FusionEntry(
                        signal_id=s.signal_id,
                        category=s.category,
                        provider_id=s.provider.id,
                        normalized_score=s.normalized_score(),
                        weight_applied=effective_weight,
                        computed_at=s.metadata.computed_at.isoformat(),
                        included=True,
                    )
                )

        return FusionResult(
            xs_composite=round(xs, 6),
            xs_coverage=sorted(c.value for c in category_scores.keys()),
            signals_count=len(included),
            included=included,
            excluded=excluded,
            category_scores={c.value: round(v, 6) for c, v in category_scores.items()},
            neutral_fallback=False,
        )

    # ── Introspection helpers ────────────────────────────────

    @property
    def category_weights(self) -> Dict[SignalCategory, float]:
        """Return a copy of the active category weights."""
        return dict(self._category_weights)

    @property
    def max_age_seconds(self) -> Dict[SignalCategory, int]:
        """Return a copy of the active per-category max ages."""
        return dict(self._max_age)

    def describe(self) -> Dict[str, object]:
        """Return a machine-readable description for the aggregator
        metadata endpoint (spec §07.3 well-known format)."""
        return {
            "spec_version": "tatf-v1.0.0",
            "profile": "aggregator",
            "category_weights": {
                c.value: w for c, w in self._category_weights.items()
            },
            "max_age_seconds": {c.value: s for c, s in self._max_age.items()},
        }
