# Contributing to TATF

Thank you for your interest in contributing to the TRUCE Agent Trust Framework.

TATF is an open standard. We believe the best trust infrastructure gets built by the people who need it most. Whether you're a protocol designer, security researcher, or ML engineer — there's meaningful work here.

## Path to Maintainer

We follow a meritocratic contribution model. Your work speaks for itself.

| Level | What it means | How you get there |
|-------|--------------|-------------------|
| **Contributor** | You've shipped merged code | 1 merged PR |
| **Reviewer** | You review others' PRs | 3+ merged PRs + consistent review quality |
| **Maintainer** | You shape the spec direction | Merged RFC + sustained contribution track record |
| **Core** | You define the standard | Invitation from existing Core members |

There are no shortcuts. No LinkedIn clout, no credentials — just the work.

## Ways to Contribute

### 🏷️ Good First Issues

Look for issues labeled `good first issue` — these are scoped, well-defined tasks designed for new contributors. They're real work, not busywork.

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
- The Python reference implementation lives at [truce-py](https://github.com/truceprotocol/truce-py)
- Submit implementations in any language
- Include benchmark evaluation results
- Document any deviations from the spec

### Security Research
- Adversarial testing of the scoring model (Layer 4)
- Game-theoretic analysis of trust score manipulation
- Privacy analysis of k-anonymity guarantees in AVX
- Formal verification of ATBF routing thresholds

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

### Reference Implementation Setup

```bash
pip install tatf

# Or from source
git clone https://github.com/truceprotocol/truce-py.git
cd truce-py
pip install -e ".[dev,crypto]"
pytest tests/ -v
```

## PR Guidelines

- One logical change per PR
- Include tests for new functionality
- Spec changes require an RFC
- Benchmark changes must include before/after results
- Security-sensitive changes require review from a Core maintainer

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- No ad hominem arguments
- Assume good faith
- Disagree with ideas, not people

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
