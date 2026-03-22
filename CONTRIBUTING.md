# Contributing to TATF

Thank you for your interest in contributing to the TRUCE Agent Trust Framework.

## Ways to Contribute

### Specification Improvements
- Open an issue describing the change
- Write an RFC in `spec/rfcs/` with the format `RFC-NNNN-title.md`
- Allow 14 days for community review
- Core maintainers approve or request changes

### Benchmark Datasets
- Generate datasets with diverse agent archetypes
- Submit results from your TATF implementation
- Contribute evaluation metrics and analysis

### Reference Implementations
- Submit implementations in any language
- Include benchmark evaluation results
- Document any deviations from the spec

## Development Setup

```bash
# Clone the repository
git clone https://github.com/truceprotocol/tatf.git
cd tatf

# Generate benchmark data
cd benchmarks
python generate_benchmark.py --agents 1000 --output datasets/my_dataset.jsonl

# Run evaluation
python evaluate.py --dataset datasets/my_dataset.jsonl --verbose
```

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- No ad hominem arguments
- Assume good faith

## RFC Format

```markdown
# RFC-NNNN: Title

**Status:** Draft | Review | Accepted | Rejected
**Author:** Name <email>
**Date:** YYYY-MM-DD

## Summary
One paragraph summary.

## Motivation
Why this change is needed.

## Specification
Detailed technical specification.

## Backward Compatibility
Impact on existing implementations.

## Security Considerations
Any security implications.
```

## License

By contributing, you agree that your contributions will be licensed under Apache 2.0.
