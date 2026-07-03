"""Tests for the TATF SignalAggregator (spec v1.0 §07 fusion).

Covers normalisation (risk vs trust direction), cross-category fusion,
missing-signal neutral fallback (§07.4.3), stale-signal exclusion (§07.4.4),
unknown-category handling, and category weighting.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tatf import (
    Signal,
    SignalAggregator,
    SignalCategory,
    SignalDirection,
)
from tatf.models import (
    SignalMetadata,
    SignalProvider,
    SignalScore,
    SignalSubject,
)


def _signal(
    *,
    signal_id: str = "SIG-1",
    category: SignalCategory = SignalCategory.PROMPT_INJECTION,
    value: float = 0.0,
    direction: SignalDirection = SignalDirection.RISK,
    confidence: float = 1.0,
    scale: str = "[0,1]",
    age_seconds: float = 0.0,
    valid_until: datetime | None = None,
    provider_id: str = "lakera",
) -> Signal:
    computed_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    return Signal(
        signal_id=signal_id,
        category=category,
        provider=SignalProvider(id=provider_id, name=provider_id),
        subject=SignalSubject(agent_id="AGT-1"),
        score=SignalScore(value=value, direction=direction, scale=scale, confidence=confidence),
        metadata=SignalMetadata(computed_at=computed_at, valid_until=valid_until),
    )


# ── Normalisation ───────────────────────────────────────────────


def test_risk_direction_inverts():
    """A high RISK value normalises to a low trust score."""
    s = _signal(value=1.0, direction=SignalDirection.RISK)
    assert s.normalized_score() == pytest.approx(0.0)


def test_trust_direction_passthrough():
    """A high TRUST value normalises to a high trust score."""
    s = _signal(value=1.0, direction=SignalDirection.TRUST)
    assert s.normalized_score() == pytest.approx(1.0)


def test_normalisation_respects_scale():
    """A [0,100]-scaled value is mapped into [0,1] before inversion."""
    s = _signal(value=100.0, direction=SignalDirection.RISK, scale="[0,100]")
    assert s.normalized_score() == pytest.approx(0.0)
    s2 = _signal(value=0.0, direction=SignalDirection.RISK, scale="[0,100]")
    assert s2.normalized_score() == pytest.approx(1.0)


# ── Missing-signal neutral fallback (§07.4.3) ───────────────────


def test_empty_signals_returns_neutral():
    agg = SignalAggregator()
    result = agg.fuse([])
    assert result.xs_composite == 0.5
    assert result.neutral_fallback is True
    assert result.signals_count == 0
    assert result.xs_coverage == []


# ── Stale-signal exclusion (§07.4.4) ────────────────────────────


def test_stale_signal_excluded():
    """A signal older than its category max-age is excluded from fusion."""
    # PROMPT_INJECTION default max age is 86_400s; make it 2 days old.
    agg = SignalAggregator()
    stale = _signal(age_seconds=2 * 86_400)
    result = agg.fuse([stale])
    assert result.signals_count == 0
    assert result.neutral_fallback is True
    assert any(e.reason == "stale" for e in result.excluded)


def test_valid_until_in_past_is_stale():
    agg = SignalAggregator()
    expired = _signal(valid_until=datetime.now(timezone.utc) - timedelta(hours=1))
    result = agg.fuse([expired])
    assert result.signals_count == 0
    assert any(e.reason == "stale" for e in result.excluded)


# ── Unknown-category handling ───────────────────────────────────


def test_unknown_category_excluded():
    """A signal whose category has no configured weight is excluded."""
    # Restrict weights to a single category; a GOVERNANCE signal is unknown.
    agg = SignalAggregator(category_weights={SignalCategory.PROMPT_INJECTION: 1.0})
    gov = _signal(category=SignalCategory.GOVERNANCE, value=0.0, direction=SignalDirection.RISK)
    result = agg.fuse([gov])
    assert result.signals_count == 0
    assert any(e.reason == "unknown_category" for e in result.excluded)


# ── Fusion + coverage ───────────────────────────────────────────


def test_single_low_risk_signal_high_trust():
    """A low-risk prompt-injection signal yields a high XS composite."""
    agg = SignalAggregator()
    s = _signal(value=0.1, direction=SignalDirection.RISK)  # normalises to 0.9
    result = agg.fuse([s])
    assert result.xs_composite == pytest.approx(0.9)
    assert result.signals_count == 1
    assert result.neutral_fallback is False
    assert "prompt_injection" in result.xs_coverage


def test_two_categories_fused_and_covered():
    agg = SignalAggregator()
    s1 = _signal(signal_id="A", category=SignalCategory.PROMPT_INJECTION,
                 value=0.0, direction=SignalDirection.RISK)  # -> 1.0
    s2 = _signal(signal_id="B", category=SignalCategory.GOVERNANCE,
                 value=1.0, direction=SignalDirection.TRUST)  # -> 1.0
    result = agg.fuse([s1, s2])
    assert result.xs_composite == pytest.approx(1.0)
    assert set(result.xs_coverage) == {"prompt_injection", "governance"}
    assert result.signals_count == 2


def test_within_category_confidence_weighted_mean():
    """Two same-category signals combine as a confidence-weighted mean."""
    agg = SignalAggregator()
    # trust 1.0 @ conf 1.0 and trust 0.0 @ conf 1.0 -> mean 0.5
    hi = _signal(signal_id="A", value=1.0, direction=SignalDirection.TRUST, confidence=1.0)
    lo = _signal(signal_id="B", value=0.0, direction=SignalDirection.TRUST, confidence=1.0)
    result = agg.fuse([hi, lo])
    assert result.xs_composite == pytest.approx(0.5)


def test_category_weight_renormalisation():
    """Composite renormalises over only the present categories."""
    # Weights: PI=0.8, GOV=0.2 (others irrelevant). Present: PI (score 1.0),
    # GOV (score 0.0). Composite = (1.0*0.8 + 0.0*0.2)/(0.8+0.2) = 0.8.
    agg = SignalAggregator(category_weights={
        SignalCategory.PROMPT_INJECTION: 0.8,
        SignalCategory.GOVERNANCE: 0.2,
    })
    pi = _signal(signal_id="A", category=SignalCategory.PROMPT_INJECTION,
                 value=0.0, direction=SignalDirection.RISK)  # -> 1.0
    gov = _signal(signal_id="B", category=SignalCategory.GOVERNANCE,
                  value=0.0, direction=SignalDirection.TRUST)  # -> 0.0
    result = agg.fuse([pi, gov])
    assert result.xs_composite == pytest.approx(0.8)


def test_audit_trail_weights_sum_to_one():
    """Included-entry weights partition the composite (sum ~= 1.0)."""
    agg = SignalAggregator()
    s1 = _signal(signal_id="A", category=SignalCategory.PROMPT_INJECTION, value=0.2, direction=SignalDirection.RISK)
    s2 = _signal(signal_id="B", category=SignalCategory.GOVERNANCE, value=0.9, direction=SignalDirection.TRUST)
    result = agg.fuse([s1, s2])
    total_weight = sum(e.weight_applied for e in result.included)
    assert total_weight == pytest.approx(1.0)


# ── Introspection ───────────────────────────────────────────────


def test_describe_is_machine_readable():
    agg = SignalAggregator()
    desc = agg.describe()
    assert desc["spec_version"] == "tatf-v1.0.0"
    assert desc["profile"] == "aggregator"
    assert "prompt_injection" in desc["category_weights"]


def test_negative_weight_rejected():
    with pytest.raises(ValueError):
        SignalAggregator(category_weights={SignalCategory.GOVERNANCE: -0.1})
