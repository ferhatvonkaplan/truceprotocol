"""TATF AVX Calculator — Agent Volatility Index.

Reference implementation of TATF spec v0.1 §06.

Computes sector-level market stress from four dimensions:
  PD (Panic Diversification)  weight 0.40
  PV (Price Volatility)       weight 0.30
  DA (Demand Acceleration)    weight 0.20
  CR (Cancellation Rate)      weight 0.10

K-anonymity: AVX is suppressed when fewer than K unique firms
contribute events.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .models import AVXDimensions, AVXScore

# Dimension weights (spec §06).
_W_PD: float = 0.40
_W_PV: float = 0.30
_W_DA: float = 0.20
_W_CR: float = 0.10

# Defaults.
_K_ANONYMITY_MIN: int = 5
_LOOKBACK_HOURS: float = 2.0
_BASELINE_CANCEL_RATE: float = 0.05


class AVXEvent:
    """A single event for AVX calculation."""

    __slots__ = ("firm_id", "price", "quantity", "cancelled", "timestamp")

    def __init__(
        self,
        firm_id: str,
        price: float,
        quantity: float = 1.0,
        cancelled: bool = False,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.firm_id = firm_id
        self.price = price
        self.quantity = quantity
        self.cancelled = cancelled
        self.timestamp = timestamp or datetime.now(timezone.utc)


class AVXCalculator:
    """Sector-level AVX market stress calculator.

    Parameters
    ----------
    k_anonymity_min : int
        Minimum unique firms for AVX publication. Default 5.
    lookback_hours : float
        Window size for current/prior period. Default 2.0.
    baseline_cancel_rate : float
        Sector baseline cancellation rate. Default 0.05.
    """

    def __init__(
        self,
        k_anonymity_min: int = _K_ANONYMITY_MIN,
        lookback_hours: float = _LOOKBACK_HOURS,
        baseline_cancel_rate: float = _BASELINE_CANCEL_RATE,
    ) -> None:
        self._k_min = k_anonymity_min
        self._lookback = lookback_hours
        self._baseline_cr = baseline_cancel_rate
        # sector -> list of events
        self._events: Dict[str, List[AVXEvent]] = {}

    def ingest(self, sector: str, events: List[AVXEvent | dict]) -> int:
        """Ingest events for a sector. Returns count of events ingested."""
        if sector not in self._events:
            self._events[sector] = []

        count = 0
        for ev in events:
            if isinstance(ev, dict):
                ev = AVXEvent(**ev)
            self._events[sector].append(ev)
            count += 1
        return count

    def compute(
        self,
        sector: str,
        *,
        as_of: Optional[datetime] = None,
    ) -> Optional[AVXScore]:
        """Compute AVX for a sector.

        Returns None if k-anonymity is not satisfied.
        """
        events = self._events.get(sector, [])
        if not events:
            return None

        now = as_of or datetime.now(timezone.utc)
        lookback = timedelta(hours=self._lookback)

        # Split into current and prior windows.
        current_start = now - lookback
        prior_start = current_start - lookback

        current = [e for e in events if current_start <= e.timestamp <= now]
        prior = [e for e in events if prior_start <= e.timestamp < current_start]

        if not current:
            return None

        # K-anonymity check.
        unique_firms = len(set(e.firm_id for e in current))
        k_satisfied = unique_firms >= self._k_min

        if not k_satisfied:
            return None

        # ── PD: Panic Diversification (HHI-based) ──
        firm_counts: Dict[str, int] = {}
        for e in current:
            firm_counts[e.firm_id] = firm_counts.get(e.firm_id, 0) + 1

        n_firms = len(firm_counts)
        total = sum(firm_counts.values())
        hhi = sum((c / total) ** 2 for c in firm_counts.values())

        if n_firms <= 1:
            pd = 100.0
        else:
            hhi_min = 1.0 / n_firms
            hhi_norm = (hhi - hhi_min) / (1.0 - hhi_min) if hhi_min < 1.0 else 0.0
            pd = min(100.0, max(0.0, hhi_norm * 100.0))

        # ── PV: Price Volatility (CV-based) ──
        prices = [e.price for e in current if e.price > 0]
        if len(prices) >= 2:
            mean_p = statistics.mean(prices)
            std_p = statistics.stdev(prices)
            cv = std_p / mean_p if mean_p > 0 else 0
            pv = min(100.0, cv * 200.0)
        else:
            pv = 0.0

        # ── DA: Demand Acceleration ──
        current_demand = sum(e.quantity for e in current)
        prior_demand = sum(e.quantity for e in prior)

        if prior_demand <= 0:
            da = 100.0 if current_demand > 0 else 0.0
        else:
            ratio = current_demand / prior_demand
            da = min(100.0, max(0.0, (ratio - 1.0) * 100.0))

        # ── CR: Cancellation Rate ──
        cancel_count = sum(1 for e in current if e.cancelled)
        current_rate = cancel_count / len(current) if current else 0
        safe_baseline = max(self._baseline_cr, 0.01)
        cr_ratio = current_rate / safe_baseline
        cr = min(100.0, max(0.0, (cr_ratio - 1.0) * 100.0))

        # Composite AVX.
        avx = min(100.0, _W_PD * pd + _W_PV * pv + _W_DA * da + _W_CR * cr)

        return AVXScore(
            sector=sector,
            avx_score=round(avx, 2),
            dimensions=AVXDimensions(
                pd_score=round(pd, 2),
                pv_score=round(pv, 2),
                da_score=round(da, 2),
                cr_score=round(cr, 2),
            ),
            unique_firms=unique_firms,
            event_count=len(current),
            lookback_hours=self._lookback,
            k_anonymity_satisfied=k_satisfied,
        )

    def reset(self, sector: Optional[str] = None) -> None:
        """Clear events. If sector given, clear that sector only."""
        if sector:
            self._events.pop(sector, None)
        else:
            self._events.clear()
