# TATF Benchmarks v0.1

Synthetic benchmark dataset and evaluation tools for testing TATF implementations.

## Quick Start

```bash
# Generate the benchmark dataset (100 agents, ~10K transactions)
python generate_benchmark.py --agents 100 --output datasets/benchmark_v0.1.jsonl

# Evaluate a TATF implementation against the benchmark
python evaluate.py --dataset datasets/benchmark_v0.1.jsonl --output evaluation/results_v0.1.json --verbose
```

## Dataset Format

Each line in the JSONL file contains one agent record:

```json
{
  "agent_id": "AGT-0001",
  "firm_id": "FIRM-012",
  "sector": "commodities",
  "archetype": "reliable",
  "expected_routing": "AUTO_PASS",
  "features": {
    "price_mean": 1234.56,
    "price_std": 89.12,
    "hour_mean": 13.45,
    "hour_std": 1.82,
    "concurrent_mean": 1.3,
    "concurrent_std": 0.5,
    "cancel_rate": 0.032,
    "unique_categories": 2,
    "unique_counterparties": 45,
    "total_transactions": 120
  },
  "transactions": [...]
}
```

## Agent Archetypes

| Archetype | Distribution | Expected Routing | Description |
|-----------|-------------|------------------|-------------|
| reliable | 55% | AUTO_PASS | Consistent, predictable behavior |
| volatile | 20% | AUTO_PASS or SOFT_HOLD | High variance but not malicious; routing derived from features |
| newcomer | 10% | AUTO_PASS | Few transactions (cold start) |
| anomalous | 10% | SOFT_HOLD or HARD_BLOCK | Behavioral anomalies detected; routing derived from features |
| adversarial | 5% | HARD_BLOCK | Actively gaming the system |

## Evaluation Metrics

The evaluator measures:
- **Overall accuracy**: Fraction of correct ATBF routing predictions
- **Confusion matrix**: Predicted vs expected routing decisions
- **Per-archetype accuracy**: How well each archetype is classified
- **Score distribution**: Min/max/mean/median composite scores per archetype

## Submitting Results

To submit your implementation's results to the TATF leaderboard:

1. Run the evaluator with the official benchmark dataset
2. Include your `results_v0.1.json` in a PR to this repository
3. Add your implementation details to the leaderboard table

## License

Apache 2.0
