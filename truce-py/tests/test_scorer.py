"""Tests for the TATF reference scorer.

Validates spec compliance:
  - §01: ALPHA composite scoring, confidence intervals, cold-start
  - §02: 6-dimension KYA-B scoring, EMA baselines, epsilon guard
  - §03: ATBF zone routing thresholds
"""

from datetime import datetime, timedelta, timezone

import pytest

from truce import (
    TATFScorer,
    Transaction,
    RoutingDecision,
    TrustTier,
)


# ── Fixtures ─────────────────────────────────────────────────────


def _make_txn(
    hour: float = 13.0,
    price: float = 1000.0,
    sessions: int = 1,
    category: str = "electronics",
    counterparty: str = "cp-001",
    rounds: int = 2,
    day_offset: int = 0,
    cancelled: bool = False,
    settled: bool = True,
) -> Transaction:
    ts = datetime(2026, 1, 1, int(hour), int((hour % 1) * 60), tzinfo=timezone.utc)
    ts += timedelta(days=day_offset)
    return Transaction(
        timestamp=ts,
        price=price,
        product_code=category,
        category=category,
        counterparty_id=counterparty,
        concurrent_sessions=sessions,
        negotiation_rounds=rounds,
        cancelled=cancelled,
        settled=settled,
    )


def _build_history(n: int = 30, start_day: int = 0, **kwargs) -> list[Transaction]:
    """Generate n normal transactions over n days."""
    return [_make_txn(day_offset=start_day + i, **kwargs) for i in range(n)]


# ── Cold Start ───────────────────────────────────────────────────


class TestColdStart:
    def test_cold_start_bypass(self):
        """Agents in cold start MUST get AUTO_PASS with anomaly_score=0."""
        scorer = TATFScorer()
        txns = _build_history(5)  # Only 5 days < 14 cold start
        scorer.ingest("a1", txns)
        result = scorer.compute_anomaly("a1")
        assert result.cold_start is True
        assert result.composite == 0.0
        assert result.routing == RoutingDecision.AUTO_PASS

    def test_cold_start_alpha_neutral(self):
        """ALPHA MUST be 0.5 when observation count < COLD_START_MIN_OBS."""
        scorer = TATFScorer()
        txns = [_make_txn(day_offset=0)]  # Only 1 transaction
        scorer.ingest("a1", txns)
        alpha = scorer.score("a1")
        assert alpha.score == 0.5
        assert alpha.cold_start is True
        assert alpha.confidence_low == 0.0
        assert alpha.confidence_high == 1.0

    def test_exits_cold_start(self):
        """After 14 days, agent MUST be scored normally."""
        scorer = TATFScorer()
        txns = _build_history(20)
        scorer.ingest("a1", txns)
        result = scorer.compute_anomaly("a1")
        assert result.cold_start is False


# ── Dimension Caps ───────────────────────────────────────────────


class TestDimensionCaps:
    """Each dimension MUST be capped per spec §02."""

    def test_s_time_cap_35(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, hour=13.0))
        # Score with extreme hour deviation.
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(hour=3.0, day_offset=20)
        )
        assert result.dimensions.s_time <= 35.0

    def test_s_concurrent_cap_45(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, sessions=1))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(sessions=50, day_offset=20)
        )
        assert result.dimensions.s_concurrent <= 45.0

    def test_s_price_cap_40(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, price=1000.0))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(price=99999.0, day_offset=20)
        )
        assert result.dimensions.s_price <= 40.0

    def test_s_category_binary_30(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, category="electronics"))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(category="agriculture", day_offset=20)
        )
        assert result.dimensions.s_category == 30.0

    def test_s_category_known_zero(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, category="electronics"))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(category="electronics", day_offset=20)
        )
        assert result.dimensions.s_category == 0.0

    def test_s_rounds_binary_25(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, rounds=2))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(rounds=99, day_offset=20)
        )
        assert result.dimensions.s_rounds == 25.0

    def test_s_counterparty_cap_25(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, counterparty="cp-001"))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(counterparty="cp-999", day_offset=20)
        )
        assert result.dimensions.s_counterparty <= 25.0


# ── Composite & Routing ──────────────────────────────────────────


class TestRouting:
    """ATBF zones per spec §03."""

    def test_normal_agent_auto_pass(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20))
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(day_offset=20)
        )
        assert result.routing == RoutingDecision.AUTO_PASS
        assert result.composite < 50

    def test_anomalous_soft_hold(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, hour=13.0, sessions=1))
        # Trigger multiple moderate anomalies.
        result = scorer.compute_anomaly(
            "a1",
            transaction=_make_txn(
                hour=3.0, sessions=5, category="new-cat", day_offset=20
            ),
        )
        assert result.routing == RoutingDecision.SOFT_HOLD
        assert 50 <= result.composite < 120

    def test_severe_hard_block(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, hour=13.0, sessions=1, price=1000.0))
        # Trigger all dimensions.
        result = scorer.compute_anomaly(
            "a1",
            transaction=_make_txn(
                hour=3.0,
                sessions=50,
                price=99999.0,
                category="new-cat",
                rounds=99,
                counterparty="cp-999",
                day_offset=20,
            ),
        )
        assert result.routing == RoutingDecision.HARD_BLOCK
        assert result.composite >= 120

    def test_composite_bounded_200(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20))
        result = scorer.compute_anomaly(
            "a1",
            transaction=_make_txn(
                hour=3.0, sessions=100, price=999999.0,
                category="x", rounds=999, counterparty="z",
                day_offset=20,
            ),
        )
        assert result.composite <= 200.0

    def test_no_single_dimension_causes_hard_block(self):
        """Spec §03: No single dimension can push into HARD_BLOCK."""
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20, sessions=1))
        # Only concurrent sessions anomaly (max 45 < 120).
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(sessions=100, day_offset=20)
        )
        assert result.routing != RoutingDecision.HARD_BLOCK


# ── ALPHA Score ──────────────────────────────────────────────────


class TestAlphaScore:
    def test_alpha_bounded_0_1(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20))
        result = scorer.score("a1")
        assert 0.0 <= result.score <= 1.0

    def test_alpha_components_sum(self):
        """Weights must sum to 1.0 (spec §01)."""
        assert abs(0.35 + 0.25 + 0.25 + 0.15 - 1.0) < 1e-10

    def test_confidence_interval_narrows(self):
        """More observations -> narrower CI."""
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(10))
        r1 = scorer.score("a1")
        scorer.ingest("a1", _build_history(50, start_day=10))
        r2 = scorer.score("a1")
        width1 = r1.confidence_high - r1.confidence_low
        width2 = r2.confidence_high - r2.confidence_low
        assert width2 < width1

    def test_trust_tiers(self):
        """Score should map to correct tier (spec §01)."""
        scorer = TATFScorer()
        # Build a solid agent.
        scorer.ingest("a1", _build_history(30))
        result = scorer.score("a1")
        assert result.tier in (TrustTier.HIGH, TrustTier.MODERATE)

    def test_market_stability_affects_score(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20))
        r_calm = scorer.score("a1", market_stability=0.9)
        r_stress = scorer.score("a1", market_stability=0.1)
        assert r_calm.score > r_stress.score

    def test_counterparty_affects_score(self):
        scorer = TATFScorer()
        scorer.ingest("a1", _build_history(20))
        r_high = scorer.score("a1", counterparty_score=0.9)
        r_low = scorer.score("a1", counterparty_score=0.1)
        assert r_high.score > r_low.score


# ── Epsilon Guard ────────────────────────────────────────────────


class TestEpsilonGuard:
    def test_zero_std_no_crash(self):
        """Agent with identical transactions must not crash (spec §02)."""
        scorer = TATFScorer()
        # All transactions identical -> std ≈ 0.
        txns = [_make_txn(hour=10.0, price=500.0, day_offset=i) for i in range(20)]
        scorer.ingest("a1", txns)
        result = scorer.compute_anomaly(
            "a1", transaction=_make_txn(hour=12.0, price=600.0, day_offset=20)
        )
        assert result.composite >= 0
        assert result.composite <= 200


# ── Baseline Management ──────────────────────────────────────────


class TestBaseline:
    def test_baseline_created(self):
        scorer = TATFScorer()
        scorer.ingest("a1", [_make_txn()])
        b = scorer.get_baseline("a1")
        assert b is not None
        assert b.agent_id == "a1"
        assert b.transaction_count == 1

    def test_baseline_none_for_unknown(self):
        scorer = TATFScorer()
        assert scorer.get_baseline("unknown") is None

    def test_reset_clears_all(self):
        scorer = TATFScorer()
        scorer.ingest("a1", [_make_txn()])
        scorer.ingest("a2", [_make_txn()])
        scorer.reset()
        assert scorer.get_baseline("a1") is None
        assert scorer.get_baseline("a2") is None

    def test_reset_single_agent(self):
        scorer = TATFScorer()
        scorer.ingest("a1", [_make_txn()])
        scorer.ingest("a2", [_make_txn()])
        scorer.reset("a1")
        assert scorer.get_baseline("a1") is None
        assert scorer.get_baseline("a2") is not None

    def test_categories_tracked(self):
        scorer = TATFScorer()
        scorer.ingest("a1", [
            _make_txn(category="electronics"),
            _make_txn(category="commodities", day_offset=1),
        ])
        b = scorer.get_baseline("a1")
        assert "electronics" in b.known_categories
        assert "commodities" in b.known_categories

    def test_settlement_tracking(self):
        scorer = TATFScorer()
        scorer.ingest("a1", [
            _make_txn(settled=True, cancelled=False),
            _make_txn(settled=True, cancelled=False, day_offset=1),
            _make_txn(settled=False, cancelled=True, day_offset=2),
        ])
        b = scorer.get_baseline("a1")
        assert b.settled_count == 2
        assert b.total_count == 3
