# TATF Governance

---

## Philosophy

TATF is an open standard maintained by practitioners, not committees. The governance model is designed to be lightweight, transparent, and resistant to capture. Decisions are made based on technical merit, evidence, and benchmark results — not credentials, affiliations, or politics.

---

## Roles

### Core Maintainers

Core Maintainers have final approval authority on specification changes and release decisions. They are responsible for the long-term coherence and quality of the standard.

**Current Core Maintainers:**

| Name | Role | Since |
|------|------|-------|
| Ferhat von Kaplan | Founder | 2026-03 |

### Reviewers

Reviewers are trusted contributors who review pull requests and RFCs. They provide technical feedback and approve non-spec code changes (benchmarks, reference implementation, documentation).

Reviewers are nominated by Core Maintainers after demonstrating consistent quality in at least 3 merged PRs.

### Contributors

Anyone who submits a merged pull request is a Contributor. There are no prerequisites — the work speaks for itself.

---

## Decision Process

### Non-Breaking Changes

Documentation fixes, benchmark improvements, reference implementation updates, and clarifications to existing spec language follow **lazy consensus**:

1. Open a pull request
2. At least one Reviewer approval required
3. 7-day objection window for non-trivial changes
4. If no objections, merge

### Specification Changes

Changes to the TATF specification — new dimensions, modified thresholds, additional layers, format changes — follow the **RFC process**:

1. Open a GitHub issue describing the proposed change
2. Write an RFC document in `spec/rfcs/` using the [RFC template](CONTRIBUTING.md#rfc-format)
3. 14-day community review period (minimum)
4. Core Maintainer approval required
5. Implementation in reference code must accompany spec changes

### Breaking Changes

Changes that would break backward compatibility with existing TATF implementations require:

1. RFC with explicit migration path
2. 30-day review period
3. Unanimous Core Maintainer approval
4. Major version increment

---

## Versioning

TATF follows [Semantic Versioning](https://semver.org/):

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Breaking spec change | Major (1.0 → 2.0) | New required dimension, changed scoring formula |
| New optional feature | Minor (0.1 → 0.2) | New attestation format, optional Layer 3 spec |
| Clarification or fix | Patch (0.1.0 → 0.1.1) | Typo fix, edge case clarification |

---

## Conflict Resolution

Technical disputes are resolved by:

1. **Evidence.** Show benchmark results, formal analysis, or real-world data.
2. **Discussion.** Open a GitHub issue. Make your case. Respond to counterarguments.
3. **Vote.** If consensus cannot be reached after good-faith discussion, Core Maintainers vote. Majority wins.

Personal attacks, appeals to authority, and "because I said so" are not valid arguments.

---

## Licensing

The TATF specification is licensed under **Apache 2.0**. This will not change.

Relicensing requires **unanimous** approval from all Core Maintainers. This threshold is intentionally high — trust infrastructure must remain a public good.

Documentation is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

---

## Amendments

This governance document can be amended through the standard RFC process. Changes to governance require Core Maintainer approval and a 14-day review period.
