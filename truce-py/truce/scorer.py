"""TATF Scorer — Local agent trust scoring engine.

Reference implementation of TATF v0.1 spec:
  - Layer 1: Observable Metrics (transaction history)
  - Layer 2: Behavioral Baselines (6-dimension KYA-B scoring)
  - ALPHA composite trust score
  - ATBF zone routing

Usage:
    from truce import TATFScorer

    scorer = TATFScorer()
    scorer.ingest("agent-123", transactions)
    result = scorer.score("agent-123")
    print(result.alpha, result.routing)
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from .models import (
    AgentBaseline,
    AlphaComponents,
    AlphaScore,
    AnomalyDimensions,
    AnomalyScore,
    RoutingDecision,
    Transaction,
    TrustTier,
)

# Spec constants.
_EPSILON: float = 0.5
_EMA_ALPHA: float = 0.15
_COLD_START_DAYS: int = 14
_COLD_START_MIN_OBS: int = 5

# ATBF zone thresholds (spec §03).
_AUTO_PASS_CEIL: float = 50.0
_HARD_BLOCK_FLOOR: float = 120.0

# ALPHA weights (spec §01).
_W_AT: float = 0.35
_W_MS: float = 0.25
_W_TH: float = 0.25
_W_CS: float = 0.15


def _z_score(observed: float, mean: float, std: float) -> float:
    """Z-score with epsilon guard: z = |obs - mean| / (std + ε).

    Per TATF spec §02: epsilon is ADDED to std to prevent division by
    zero and dampen scores when standard deviation is very small.
    """
    return abs(observed - mean) / (std + _EPSILON)


def _ema_update(old: float, new: float, alpha: float = _EMA_ALPHA) -> float:
    """Exponential moving average update: new_val = α * obs + (1-α) * old."""
    return alpha * new + (1 - alpha) * old


def _hhi(counts: Dict[str, int]) -> float:
    """Herfindahl-Hirschman Index from a frequency map."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return sum((c / total) ** 2 for c in counts.values())


class TATFScorer:
    """Local TATF scoring engine.

    Maintains per-agent baselines in memory and scores each transaction
    against the agent's own behavioral history.

    Parameters
    ----------
    cold_start_days : int
        Calendar days before KYA-B scoring activates. Default 14.
    cold_start_min_obs : int
        Minimum observations before ALPHA scoring activates. Default 5.
    ema_alpha : float
        EMA smoothing factor. Default 0.15.
    auto_pass_ceil : float
        ATBF AUTO_PASS ceiling. Default 50.
    hard_block_floor : float
        ATBF HARD_BLOCK floor. Default 120.
    """

    def __init__(
        self,
        cold_start_days: int = _COLD_START_DAYS,
        cold_start_min_obs: int = _COLD_START_MIN_OBS,
        ema_alpha: float = _EMA_ALPHA,
        auto_pass_ceil: float = _AUTO_PASS_CEIL,
        hard_block_floor: float = _HARD_BLOCK_FLOOR,
    ) -> None:
        self._cold_start_days = cold_start_days
        self._cold_start_min_obs = cold_start_min_obs
        self._ema_alpha = ema_alpha
        self._auto_pass_ceil = auto_pass_ceil
        self._hard_block_floor = hard_block_floor
        self._baselines: Dict[str, AgentBaseline] = {}

    # ── Public API ───────────────────────────────────────────────

    def ingest(
        self,
        agent_id: str,
        transactions: Sequence[Transaction | dict],
    ) -> AgentBaseline:
        """Ingest transaction history and build/update the agent baseline.

        Transactions should be in chronological order. Each transaction
        updates the EMA baseline incrementally.

        Returns the updated baseline.
        """
        baseline = self._get_or_create_baseline(agent_id)

        for txn in transactions:
            if isinstance(txn, dict):
                txn = Transaction(**txn)
            self._update_baseline(baseline, txn)

        return baseline

    def score(
        self,
        agent_id: str,
        *,
        transaction: Optional[Transaction | dict] = None,
        market_stability: Optional[float] = None,
        counterparty_score: Optional[float] = None,
    ) -> AlphaScore:
        """Compute the ALPHA trust score for an agent.

        Parameters
        ----------
        agent_id : str
            The agent to score.
        transaction : Transaction | dict, optional
            A new transaction to score against baseline. If None, scores
            based on current baseline state.
        market_stability : float, optional
            MS component (0-1). Derived from AVX. Default 0.5 (neutral).
        counterparty_score : float, optional
            CS component (0-1). Counterparty's AT score. Default 0.5.

        Returns
        -------
        AlphaScore
            Complete TATF trust score with confidence interval.
        """
        baseline = self._baselines.get(agent_id)
        if baseline is None:
            baseline = self._get_or_create_baseline(agent_id)

        # If a new transaction is provided, ingest it first.
        if transaction is not None:
            if isinstance(transaction, dict):
                transaction = Transaction(**transaction)
            self._update_baseline(baseline, transaction)

        # Compute anomaly score (Layer 2).
        anomaly = self.compute_anomaly(agent_id, transaction=transaction)

        # Derive ALPHA components.
        at = max(0.0, min(1.0, (200.0 - anomaly.composite) / 200.0))
        ms = market_stability if market_stability is not None else 0.5
        th = self._compute_th(baseline)
        cs = counterparty_score if counterparty_score is not None else 0.5

        # ALPHA composite (spec §01).
        alpha = _W_AT * at + _W_MS * ms + _W_TH * th + _W_CS * cs
        alpha = max(0.0, min(1.0, alpha))

        # Confidence interval — Wald binomial (spec §01).
        n = baseline.transaction_count
        cold_start_alpha = n < self._cold_start_min_obs

        if cold_start_alpha:
            ci_low, ci_high = 0.0, 1.0
            alpha = 0.5
        else:
            margin = 1.96 * math.sqrt(alpha * (1 - alpha) / max(n, 1))
            ci_low = max(0.0, alpha - margin)
            ci_high = min(1.0, alpha + margin)

        # Trust tier (spec §01).
        if alpha >= 0.80:
            tier = TrustTier.HIGH
        elif alpha >= 0.50:
            tier = TrustTier.MODERATE
        elif alpha >= 0.30:
            tier = TrustTier.LOW
        else:
            tier = TrustTier.CRITICAL

        return AlphaScore(
            agent_id=agent_id,
            score=round(alpha, 4),
            confidence_low=round(ci_low, 4),
            confidence_high=round(ci_high, 4),
            components=AlphaComponents(
                agent_trust=round(at, 4),
                market_stability=round(ms, 4),
                transaction_history=round(th, 4),
                counterparty_score=round(cs, 4),
            ),
            observation_count=n,
            cold_start=cold_start_alpha or anomaly.cold_start,
            tier=tier,
        )

    def compute_anomaly(
        self,
        agent_id: str,
        *,
        transaction: Optional[Transaction | dict] = None,
    ) -> AnomalyScore:
        """Compute the 6-dimension anomaly score (Layer 2 only).

        Returns AnomalyScore with composite, dimensions, and routing.
        """
        baseline = self._baselines.get(agent_id)
        if baseline is None:
            baseline = self._get_or_create_baseline(agent_id)

        # Cold-start bypass (spec §02-03).
        if baseline.observation_days < self._cold_start_days:
            return AnomalyScore(
                agent_id=agent_id,
                composite=0.0,
                dimensions=AnomalyDimensions(
                    s_time=0, s_concurrent=0, s_price=0,
                    s_category=0, s_rounds=0, s_counterparty=0,
                ),
                routing=RoutingDecision.AUTO_PASS,
                cold_start=True,
            )

        # Extract features from the transaction or use baseline averages.
        if transaction is not None:
            if isinstance(transaction, dict):
                transaction = Transaction(**transaction)
            hour = transaction.timestamp.hour + transaction.timestamp.minute / 60.0
            sessions = transaction.concurrent_sessions
            price = transaction.price
            category = transaction.category or transaction.product_code
            rounds = transaction.negotiation_rounds
            counterparty = transaction.counterparty_id
        else:
            # Score based on baseline state (aggregate assessment).
            hour = baseline.time_mean
            sessions = baseline.concurrent_mean
            price = baseline.price_mean
            category = ""
            rounds = 0
            counterparty = ""

        # ── Dimension 1: Time anomaly (cap 35) ──
        z_time = _z_score(hour, baseline.time_mean, baseline.time_std)
        s_time = min(35.0, math.floor(z_time * 10))

        # ── Dimension 2: Concurrent sessions (cap 45) ──
        z_conc = (sessions - baseline.concurrent_mean) / (baseline.concurrent_std + _EPSILON)
        s_concurrent = min(45.0, max(0.0, math.floor(z_conc * 15)))

        # ── Dimension 3: Price deviation (cap 40) ──
        z_price = _z_score(price, baseline.price_mean, baseline.price_std)
        s_price = min(40.0, math.floor(z_price * 12))

        # ── Dimension 4: Category anomaly (0 or 30) ──
        s_category = 0.0
        if category and category not in baseline.known_categories:
            s_category = 30.0

        # ── Dimension 5: Negotiation rounds (0 or 25) ──
        s_rounds = 25.0 if rounds > baseline.rounds_p95 else 0.0

        # ── Dimension 6: Counterparty concentration (cap 25) ──
        s_counterparty = 0.0
        if counterparty and baseline.counterparty_counts:
            hhi_before = _hhi(baseline.counterparty_counts)
            counts_after = dict(baseline.counterparty_counts)
            counts_after[counterparty] = counts_after.get(counterparty, 0) + 1
            hhi_after = _hhi(counts_after)
            delta = abs(hhi_after - hhi_before)
            s_counterparty = min(25.0, math.floor(delta * 50))

        # Composite (spec §02).
        composite = min(
            200.0,
            s_time + s_concurrent + s_price + s_category + s_rounds + s_counterparty,
        )

        # ATBF routing (spec §03).
        if composite < self._auto_pass_ceil:
            routing = RoutingDecision.AUTO_PASS
        elif composite < self._hard_block_floor:
            routing = RoutingDecision.SOFT_HOLD
        else:
            routing = RoutingDecision.HARD_BLOCK

        return AnomalyScore(
            agent_id=agent_id,
            composite=round(composite, 2),
            dimensions=AnomalyDimensions(
                s_time=round(s_time, 2),
                s_concurrent=round(s_concurrent, 2),
                s_price=round(s_price, 2),
                s_category=round(s_category, 2),
                s_rounds=round(s_rounds, 2),
                s_counterparty=round(s_counterparty, 2),
            ),
            routing=routing,
            cold_start=False,
        )

    def get_baseline(self, agent_id: str) -> Optional[AgentBaseline]:
        """Return the current baseline for an agent, or None."""
        return self._baselines.get(agent_id)

    def reset(self, agent_id: Optional[str] = None) -> None:
        """Reset baselines. If agent_id given, reset that agent only."""
        if agent_id:
            self._baselines.pop(agent_id, None)
        else:
            self._baselines.clear()

    # ── Internal ─────────────────────────────────────────────────

    def _get_or_create_baseline(self, agent_id: str) -> AgentBaseline:
        if agent_id not in self._baselines:
            self._baselines[agent_id] = AgentBaseline(agent_id=agent_id)
        return self._baselines[agent_id]

    def _update_baseline(self, b: AgentBaseline, txn: Transaction) -> None:
        """Update baseline with a new transaction via EMA."""
        now = txn.timestamp
        hour = now.hour + now.minute / 60.0
        alpha = self._ema_alpha

        if b.first_seen is None:
            b.first_seen = now

        # Track observation days.
        if b.last_updated is None or now.date() != b.last_updated.date():
            b.observation_days += 1

        b.transaction_count += 1

        # EMA updates for continuous dimensions.
        if b.transaction_count == 1:
            b.time_mean = hour
            b.time_std = 0.0
            b.price_mean = txn.price
            b.price_std = 0.0
            b.concurrent_mean = float(txn.concurrent_sessions)
            b.concurrent_std = 0.0
        else:
            # Time.
            old_time_mean = b.time_mean
            b.time_mean = _ema_update(b.time_mean, hour, alpha)
            b.time_std = _ema_update(
                b.time_std, abs(hour - old_time_mean), alpha
            )
            # Price.
            old_price_mean = b.price_mean
            b.price_mean = _ema_update(b.price_mean, txn.price, alpha)
            b.price_std = _ema_update(
                b.price_std, abs(txn.price - old_price_mean), alpha
            )
            # Concurrent sessions.
            old_conc_mean = b.concurrent_mean
            b.concurrent_mean = _ema_update(
                b.concurrent_mean, float(txn.concurrent_sessions), alpha
            )
            b.concurrent_std = _ema_update(
                b.concurrent_std,
                abs(float(txn.concurrent_sessions) - old_conc_mean),
                alpha,
            )

        # Negotiation rounds p95 (simplified: EMA-based max tracking).
        if txn.negotiation_rounds > b.rounds_p95:
            b.rounds_p95 = _ema_update(
                b.rounds_p95, float(txn.negotiation_rounds), alpha
            )

        # Categories.
        cat = txn.category or txn.product_code
        if cat and cat not in b.known_categories:
            b.known_categories.append(cat)

        # Counterparty counts.
        if txn.counterparty_id:
            b.counterparty_counts[txn.counterparty_id] = (
                b.counterparty_counts.get(txn.counterparty_id, 0) + 1
            )

        # Settlement tracking.
        b.total_count += 1
        if txn.settled and not txn.cancelled:
            b.settled_count += 1

        b.last_updated = now

    def _compute_th(self, b: AgentBaseline) -> float:
        """Transaction History component: settled / total."""
        if b.total_count == 0:
            return 0.5  # Neutral default (spec §01).
        return b.settled_count / b.total_count
