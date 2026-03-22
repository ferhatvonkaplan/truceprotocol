"""Tests for AVX market stress calculator.

Validates spec §06 compliance:
  - 4-dimension weighted scoring
  - K-anonymity enforcement
  - Edge cases (zero events, single firm, etc.)
"""

from datetime import datetime, timedelta, timezone

import pytest

from truce import AVXCalculator, AVXEvent


def _now():
    return datetime.now(timezone.utc)


def _make_events(
    n_firms: int = 5,
    n_events_per_firm: int = 10,
    base_price: float = 100.0,
    price_std: float = 5.0,
    cancel_rate: float = 0.05,
) -> list[AVXEvent]:
    """Generate events from multiple firms."""
    import random
    rng = random.Random(42)
    now = _now()
    events = []
    for f in range(n_firms):
        for i in range(n_events_per_firm):
            events.append(AVXEvent(
                firm_id=f"FIRM-{f:03d}",
                price=max(1, rng.gauss(base_price, price_std)),
                quantity=rng.uniform(10, 100),
                cancelled=rng.random() < cancel_rate,
                timestamp=now - timedelta(minutes=rng.randint(0, 119)),
            ))
    return events


class TestKAnonymity:
    def test_suppressed_below_k(self):
        """AVX MUST be None when unique_firms < k_min."""
        calc = AVXCalculator(k_anonymity_min=5)
        events = [AVXEvent(firm_id="FIRM-001", price=100, timestamp=_now())]
        calc.ingest("electronics", events)
        result = calc.compute("electronics")
        assert result is None

    def test_published_at_k(self):
        """AVX MUST be published when unique_firms >= k_min."""
        calc = AVXCalculator(k_anonymity_min=5)
        events = _make_events(n_firms=5)
        calc.ingest("electronics", events)
        result = calc.compute("electronics")
        assert result is not None
        assert result.k_anonymity_satisfied is True
        assert result.unique_firms >= 5

    def test_custom_k(self):
        calc = AVXCalculator(k_anonymity_min=3)
        events = _make_events(n_firms=3)
        calc.ingest("test", events)
        result = calc.compute("test")
        assert result is not None


class TestDimensions:
    def test_score_bounded_0_100(self):
        calc = AVXCalculator(k_anonymity_min=5)
        events = _make_events(n_firms=10)
        calc.ingest("electronics", events)
        result = calc.compute("electronics")
        assert 0 <= result.avx_score <= 100
        assert 0 <= result.dimensions.pd_score <= 100
        assert 0 <= result.dimensions.pv_score <= 100
        assert 0 <= result.dimensions.da_score <= 100
        assert 0 <= result.dimensions.cr_score <= 100

    def test_low_stress_market(self):
        """Diversified firms, stable prices, normal demand."""
        calc = AVXCalculator(k_anonymity_min=5)
        now = _now()
        # Also need prior window events for DA calculation.
        events = []
        for f in range(10):
            for i in range(10):
                events.append(AVXEvent(
                    firm_id=f"FIRM-{f:03d}",
                    price=100.0,
                    quantity=50,
                    cancelled=False,
                    timestamp=now - timedelta(minutes=i * 10),
                ))
                # Prior window.
                events.append(AVXEvent(
                    firm_id=f"FIRM-{f:03d}",
                    price=100.0,
                    quantity=50,
                    cancelled=False,
                    timestamp=now - timedelta(hours=2, minutes=i * 10),
                ))
        calc.ingest("stable", events)
        result = calc.compute("stable")
        assert result is not None
        assert result.avx_score < 30  # Low stress

    def test_high_concentration_high_pd(self):
        """Single firm dominates -> high PD score."""
        calc = AVXCalculator(k_anonymity_min=5)
        now = _now()
        events = []
        # 1 firm has 90% of events.
        for i in range(90):
            events.append(AVXEvent(
                firm_id="FIRM-DOMINANT",
                price=100.0,
                timestamp=now - timedelta(minutes=i),
            ))
        for f in range(5):
            events.append(AVXEvent(
                firm_id=f"FIRM-{f:03d}",
                price=100.0,
                timestamp=now - timedelta(minutes=f),
            ))
        calc.ingest("concentrated", events)
        result = calc.compute("concentrated")
        assert result is not None
        assert result.dimensions.pd_score > 50


class TestEdgeCases:
    def test_empty_sector(self):
        calc = AVXCalculator()
        assert calc.compute("nonexistent") is None

    def test_reset_sector(self):
        calc = AVXCalculator(k_anonymity_min=5)
        calc.ingest("test", _make_events(n_firms=5))
        calc.reset("test")
        assert calc.compute("test") is None

    def test_reset_all(self):
        calc = AVXCalculator(k_anonymity_min=5)
        calc.ingest("a", _make_events(n_firms=5))
        calc.ingest("b", _make_events(n_firms=5))
        calc.reset()
        assert calc.compute("a") is None
        assert calc.compute("b") is None

    def test_spec_version(self):
        calc = AVXCalculator(k_anonymity_min=5)
        calc.ingest("test", _make_events(n_firms=5))
        result = calc.compute("test")
        assert result.spec_version == "tatf-v0.1"
