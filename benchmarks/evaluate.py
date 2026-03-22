"""TATF Benchmark Evaluator v0.1

Evaluates a TATF implementation against the benchmark dataset.
Measures accuracy of ATBF routing decisions (AUTO_PASS / SOFT_HOLD / HARD_BLOCK).

Usage:
    python evaluate.py --dataset datasets/benchmark_v0.1.jsonl --output evaluation/results_v0.1.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from typing import Any


# ── Reference TATF Implementation (Layer 1 + 2) ─────────────────


def _z_score(value: float, mean: float, std: float, epsilon: float = 0.5) -> float:
    """Compute z-score with epsilon guard on denominator.

    Per TATF spec §02: z = |observed - mean| / (std + ε)
    The epsilon is ADDED to std (not max), dampening scores when std is small.
    """
    return abs(value - mean) / (std + epsilon)


def score_agent(features: dict[str, Any]) -> dict[str, Any]:
    """Score an agent using the TATF Layer 1+2 reference algorithm.

    Implements the 6-dimension KYA-B scoring from TATF spec §02.

    Returns:
        dict with composite score, sub-scores, and predicted routing.
    """
    # Dimension 1: Time anomaly (cap 35)
    # Agents with unusual hour patterns score high.
    # Baseline "normal" = 9-17 business hours, std ~2.
    business_hour_mean = 13.0
    business_hour_std = 3.0
    s_time = min(35, _z_score(features["hour_mean"], business_hour_mean, business_hour_std) * 10)

    # Dimension 2: Concurrent sessions (cap 45)
    # Normal = 1-2 concurrent, std ~0.5.
    s_concurrent = min(45, _z_score(features["concurrent_mean"], 1.5, 0.5) * 15)

    # Dimension 3: Price deviation (cap 40)
    # High coefficient of variation = volatile pricing.
    cv = features["price_std"] / max(features["price_mean"], 1.0)
    s_price = min(40, cv * 12 * 10)  # Scale CV to score range

    # Dimension 4: New category (0 or 30)
    # More than 3 categories = unusual breadth.
    s_category = 30 if features["unique_categories"] > 3 else 0

    # Dimension 5: Negotiation rounds proxy (0 or 25)
    # High cancel rate as proxy for excessive rounds.
    s_rounds = 25 if features["cancel_rate"] > 0.20 else 0

    # Dimension 6: Counterparty concentration (cap 25)
    # Low unique counterparties relative to transactions = concentration.
    if features["total_transactions"] > 0:
        diversity = features["unique_counterparties"] / features["total_transactions"]
        # Low diversity = high concentration.
        hhi_proxy = max(0, (1 - diversity)) * 50
    else:
        hhi_proxy = 0
    s_counterparty = min(25, hhi_proxy)

    composite = s_time + s_concurrent + s_price + s_category + s_rounds + s_counterparty

    # ATBF routing.
    if composite < 50:
        routing = "AUTO_PASS"
    elif composite < 120:
        routing = "SOFT_HOLD"
    else:
        routing = "HARD_BLOCK"

    return {
        "composite": round(composite, 2),
        "s_time": round(s_time, 2),
        "s_concurrent": round(s_concurrent, 2),
        "s_price": round(s_price, 2),
        "s_category": round(s_category, 2),
        "s_rounds": round(s_rounds, 2),
        "s_counterparty": round(s_counterparty, 2),
        "routing": routing,
    }


def evaluate_dataset(dataset_path: str) -> dict[str, Any]:
    """Evaluate all agents in a benchmark dataset.

    Returns summary metrics:
      - accuracy: fraction of correct routing predictions
      - confusion_matrix: predicted vs expected routing
      - per_archetype: accuracy per agent archetype
      - score_distribution: min/max/mean/median composite scores per archetype
    """
    results = []
    correct = 0
    total = 0
    confusion: dict[str, dict[str, int]] = {
        "AUTO_PASS": {"AUTO_PASS": 0, "SOFT_HOLD": 0, "HARD_BLOCK": 0},
        "SOFT_HOLD": {"AUTO_PASS": 0, "SOFT_HOLD": 0, "HARD_BLOCK": 0},
        "HARD_BLOCK": {"AUTO_PASS": 0, "SOFT_HOLD": 0, "HARD_BLOCK": 0},
    }
    archetype_stats: dict[str, dict[str, int]] = {}
    archetype_scores: dict[str, list[float]] = {}

    with open(dataset_path) as f:
        for line in f:
            rec = json.loads(line)
            features = rec["features"]
            expected = rec["expected_routing"]
            archetype = rec["archetype"]

            result = score_agent(features)
            predicted = result["routing"]

            # Track accuracy.
            is_correct = predicted == expected
            if is_correct:
                correct += 1
            total += 1

            # Confusion matrix.
            if expected in confusion and predicted in confusion[expected]:
                confusion[expected][predicted] += 1

            # Per-archetype stats.
            if archetype not in archetype_stats:
                archetype_stats[archetype] = {"correct": 0, "total": 0}
                archetype_scores[archetype] = []
            archetype_stats[archetype]["total"] += 1
            if is_correct:
                archetype_stats[archetype]["correct"] += 1
            archetype_scores[archetype].append(result["composite"])

            results.append({
                "agent_id": rec["agent_id"],
                "archetype": archetype,
                "expected": expected,
                "predicted": predicted,
                "correct": is_correct,
                "score": result,
            })

    # Compute per-archetype accuracy and score stats.
    per_archetype = {}
    for arch, stats in archetype_stats.items():
        scores = sorted(archetype_scores[arch])
        n = len(scores)
        per_archetype[arch] = {
            "accuracy": round(stats["correct"] / max(1, stats["total"]), 4),
            "count": stats["total"],
            "score_min": round(scores[0], 2) if scores else 0,
            "score_max": round(scores[-1], 2) if scores else 0,
            "score_mean": round(sum(scores) / n, 2) if n else 0,
            "score_median": round(scores[n // 2], 2) if n else 0,
        }

    return {
        "dataset": dataset_path,
        "total_agents": total,
        "accuracy": round(correct / max(1, total), 4),
        "correct": correct,
        "incorrect": total - correct,
        "confusion_matrix": confusion,
        "per_archetype": per_archetype,
        "agent_results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate TATF implementation against benchmark")
    parser.add_argument("--dataset", type=str, default="datasets/benchmark_v0.1.jsonl")
    parser.add_argument("--output", type=str, default="evaluation/results_v0.1.json")
    parser.add_argument("--verbose", action="store_true", help="Print per-agent results")
    args = parser.parse_args()

    results = evaluate_dataset(args.dataset)

    # Write full results.
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary.
    print(f"TATF Benchmark Evaluation")
    print(f"{'=' * 50}")
    print(f"Dataset:  {results['dataset']}")
    print(f"Agents:   {results['total_agents']}")
    print(f"Accuracy: {results['accuracy']:.1%} ({results['correct']}/{results['total_agents']})")
    print()

    print("Confusion Matrix (rows=expected, cols=predicted):")
    print(f"{'':>15} {'AUTO_PASS':>12} {'SOFT_HOLD':>12} {'HARD_BLOCK':>12}")
    for expected, preds in results["confusion_matrix"].items():
        row = f"{expected:>15}"
        for pred in ["AUTO_PASS", "SOFT_HOLD", "HARD_BLOCK"]:
            row += f" {preds[pred]:>12}"
        print(row)
    print()

    print("Per-Archetype Results:")
    print(f"{'Archetype':>15} {'Accuracy':>10} {'Count':>7} {'Score Range':>20} {'Mean':>8}")
    for arch, stats in results["per_archetype"].items():
        score_range = f"[{stats['score_min']:.0f} - {stats['score_max']:.0f}]"
        print(f"{arch:>15} {stats['accuracy']:>10.1%} {stats['count']:>7} {score_range:>20} {stats['score_mean']:>8.1f}")

    print(f"\nResults written to: {args.output}")

    if args.verbose:
        print("\nMisclassified Agents:")
        for r in results["agent_results"]:
            if not r["correct"]:
                print(f"  {r['agent_id']} ({r['archetype']}): "
                      f"expected={r['expected']}, predicted={r['predicted']}, "
                      f"score={r['score']['composite']:.1f}")


if __name__ == "__main__":
    main()
