"""TATF Benchmark Dataset Generator v0.1

Generates synthetic agent behavior traces for testing TATF implementations.

Each agent trace includes:
  - Transaction history (timestamps, amounts, counterparties)
  - Behavioral features (time patterns, price patterns, category diversity)
  - Ground-truth labels (trustworthy, anomalous, adversarial)

Output: JSON-lines file with one agent record per line.

Usage:
    python generate_benchmark.py --agents 100 --output datasets/benchmark_v0.1.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

# Reproducible datasets.
SEED = 42

SECTORS = ["electronics", "commodities", "logistics", "insurance", "legal-tech"]
CURRENCIES = ["USD", "EUR", "GBP"]
PRODUCT_CODES = {
    "electronics": ["CHIP01", "DISP02", "BATT03", "SENS04"],
    "commodities": ["WHEAT", "STEEL01", "COPP02", "OIL03"],
    "logistics": ["FTL01", "LTL02", "AIR03", "SEA04"],
    "insurance": ["CYBI01", "PROP02", "LIAB03"],
    "legal-tech": ["CONT01", "DISC02", "COMP03"],
}
INCOTERMS = ["FOB", "CIF", "DDP", "EXW", "FCA"]

# Agent archetypes (ground truth labels).
ARCHETYPES = [
    ("reliable", 0.55),       # Normal, consistent behavior
    ("volatile", 0.20),       # High variance but not malicious
    ("newcomer", 0.10),       # Cold-start, few transactions
    ("anomalous", 0.10),      # Behavioral anomalies (should trigger SOFT_HOLD)
    ("adversarial", 0.05),    # Actively gaming the system (should trigger HARD_BLOCK)
]


def _pick_archetype(rng: random.Random) -> str:
    """Weighted archetype selection."""
    r = rng.random()
    cumulative = 0.0
    for name, weight in ARCHETYPES:
        cumulative += weight
        if r <= cumulative:
            return name
    return ARCHETYPES[0][0]


def _generate_agent(agent_idx: int, rng: random.Random) -> dict[str, Any]:
    """Generate a single agent's behavioral trace."""
    archetype = _pick_archetype(rng)
    firm_id = f"FIRM-{rng.randint(1, 30):03d}"
    agent_id = f"AGT-{agent_idx:04d}"
    sector = rng.choice(SECTORS)

    # Base parameters vary by archetype.
    if archetype == "reliable":
        n_transactions = rng.randint(50, 200)
        price_mean = rng.uniform(100, 5000)
        price_std = price_mean * rng.uniform(0.02, 0.08)
        hour_mean = rng.uniform(9, 17)
        hour_std = rng.uniform(0.5, 2.0)
        cancel_rate = rng.uniform(0.01, 0.05)
        category_count = rng.randint(1, 3)
        concurrent_mean = rng.uniform(1.0, 2.0)

    elif archetype == "volatile":
        n_transactions = rng.randint(30, 150)
        price_mean = rng.uniform(100, 5000)
        price_std = price_mean * rng.uniform(0.15, 0.35)
        hour_mean = rng.uniform(6, 22)
        hour_std = rng.uniform(3.0, 6.0)
        cancel_rate = rng.uniform(0.08, 0.20)
        category_count = rng.randint(2, 5)
        concurrent_mean = rng.uniform(1.5, 4.0)

    elif archetype == "newcomer":
        n_transactions = rng.randint(1, 10)
        price_mean = rng.uniform(100, 3000)
        price_std = price_mean * rng.uniform(0.05, 0.15)
        hour_mean = rng.uniform(8, 18)
        hour_std = rng.uniform(1.0, 3.0)
        cancel_rate = rng.uniform(0.0, 0.10)
        category_count = 1
        concurrent_mean = 1.0

    elif archetype == "anomalous":
        n_transactions = rng.randint(20, 100)
        price_mean = rng.uniform(100, 5000)
        price_std = price_mean * rng.uniform(0.25, 0.50)
        hour_mean = rng.uniform(1, 5)   # Unusual hours
        hour_std = rng.uniform(1.0, 2.0)
        cancel_rate = rng.uniform(0.15, 0.40)
        category_count = rng.randint(3, 5)
        concurrent_mean = rng.uniform(3.0, 8.0)

    else:  # adversarial
        n_transactions = rng.randint(40, 120)
        price_mean = rng.uniform(500, 10000)
        price_std = price_mean * rng.uniform(0.40, 0.80)
        hour_mean = rng.uniform(0, 4)
        hour_std = rng.uniform(0.5, 1.0)
        cancel_rate = rng.uniform(0.30, 0.60)
        category_count = rng.randint(4, 5)
        concurrent_mean = rng.uniform(5.0, 15.0)

    # Generate transactions.
    products = rng.sample(PRODUCT_CODES[sector], min(category_count, len(PRODUCT_CODES[sector])))
    base_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    transactions = []

    for i in range(n_transactions):
        # Time with archetype-driven distribution.
        day_offset = rng.randint(0, 90)
        hour = max(0, min(23, rng.gauss(hour_mean, hour_std)))
        minute = rng.randint(0, 59)
        ts = base_time + timedelta(days=day_offset, hours=hour, minutes=minute)

        price = max(1.0, rng.gauss(price_mean, price_std))
        quantity = rng.uniform(10, 1000)
        product = rng.choice(products)
        counterparty = f"AGT-{rng.randint(0, 999):04d}"
        concurrent = max(1, int(rng.gauss(concurrent_mean, concurrent_mean * 0.3)))
        cancelled = rng.random() < cancel_rate
        side = rng.choice(["buy", "sell"])

        transactions.append({
            "timestamp": ts.isoformat(),
            "product_code": product,
            "side": side,
            "price": round(price, 2),
            "quantity": round(quantity, 2),
            "currency": rng.choice(CURRENCIES),
            "counterparty_id": counterparty,
            "concurrent_sessions": concurrent,
            "cancelled": cancelled,
            "delivery_days": rng.randint(5, 60),
            "incoterm": rng.choice(INCOTERMS),
        })

    # Sort by timestamp.
    transactions.sort(key=lambda t: t["timestamp"])

    # Compute ground-truth KYA-B features.
    prices = [t["price"] for t in transactions]
    hours_list = [
        datetime.fromisoformat(t["timestamp"]).hour + datetime.fromisoformat(t["timestamp"]).minute / 60
        for t in transactions
    ]
    concurrent_list = [t["concurrent_sessions"] for t in transactions]
    cancel_count = sum(1 for t in transactions if t["cancelled"])
    unique_counterparties = len(set(t["counterparty_id"] for t in transactions))

    def _mean(xs):
        return sum(xs) / len(xs) if xs else 0

    def _std(xs):
        if len(xs) < 2:
            return 0.0
        m = _mean(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    features = {
        "price_mean": round(_mean(prices), 2),
        "price_std": round(_std(prices), 2),
        "hour_mean": round(_mean(hours_list), 2),
        "hour_std": round(_std(hours_list), 2),
        "concurrent_mean": round(_mean(concurrent_list), 2),
        "concurrent_std": round(_std(concurrent_list), 2),
        "cancel_rate": round(cancel_count / max(1, len(transactions)), 4),
        "unique_categories": len(products),
        "unique_counterparties": unique_counterparties,
        "total_transactions": len(transactions),
    }

    # Expected ATBF routing (ground truth).
    # For volatile agents, derive expected routing from generated features
    # rather than random assignment — this ensures benchmark labels are
    # consistent with the scoring algorithm.
    if archetype in ("reliable", "newcomer"):
        expected_routing = "AUTO_PASS"
    elif archetype == "volatile":
        # Compute approximate composite from features to determine routing.
        _cv = features["price_std"] / max(features["price_mean"], 1.0)
        _s_price_est = min(40, _cv * 12 * 10)
        _s_time_est = min(35, abs(features["hour_mean"] - 13.0) / (features["hour_std"] + 0.5) * 10)
        _s_conc_est = min(45, abs(features["concurrent_mean"] - 1.5) / (0.5 + 0.5) * 15)
        _s_cat_est = 30 if features["unique_categories"] > 3 else 0
        _s_round_est = 25 if features["cancel_rate"] > 0.20 else 0
        _approx = _s_price_est + _s_time_est + _s_conc_est + _s_cat_est + _s_round_est
        expected_routing = "SOFT_HOLD" if _approx >= 50 else "AUTO_PASS"
    elif archetype == "anomalous":
        # Anomalous agents may land in SOFT_HOLD or HARD_BLOCK depending
        # on severity. Derive from features like volatile.
        _cv = features["price_std"] / max(features["price_mean"], 1.0)
        _s_price_est = min(40, _cv * 12 * 10)
        _s_time_est = min(35, abs(features["hour_mean"] - 13.0) / (features["hour_std"] + 0.5) * 10)
        _s_conc_est = min(45, abs(features["concurrent_mean"] - 1.5) / (0.5 + 0.5) * 15)
        _s_cat_est = 30 if features["unique_categories"] > 3 else 0
        _s_round_est = 25 if features["cancel_rate"] > 0.20 else 0
        _approx = _s_price_est + _s_time_est + _s_conc_est + _s_cat_est + _s_round_est
        if _approx >= 120:
            expected_routing = "HARD_BLOCK"
        else:
            expected_routing = "SOFT_HOLD"
    else:
        expected_routing = "HARD_BLOCK"

    return {
        "agent_id": agent_id,
        "firm_id": firm_id,
        "sector": sector,
        "archetype": archetype,
        "expected_routing": expected_routing,
        "features": features,
        "transactions": transactions,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate TATF benchmark dataset")
    parser.add_argument("--agents", type=int, default=100, help="Number of agents")
    parser.add_argument("--output", type=str, default="datasets/benchmark_v0.1.jsonl", help="Output file")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed)

    with open(args.output, "w") as f:
        for i in range(args.agents):
            agent = _generate_agent(i, rng)
            f.write(json.dumps(agent) + "\n")

    # Print summary.
    archetype_counts: dict[str, int] = {}
    with open(args.output) as f:
        for line in f:
            rec = json.loads(line)
            a = rec["archetype"]
            archetype_counts[a] = archetype_counts.get(a, 0) + 1

    total_txns = 0
    with open(args.output) as f:
        for line in f:
            rec = json.loads(line)
            total_txns += len(rec["transactions"])

    print(f"Generated {args.agents} agents with {total_txns} total transactions")
    print(f"Output: {args.output}")
    print(f"Archetype distribution: {json.dumps(archetype_counts, indent=2)}")


if __name__ == "__main__":
    main()
