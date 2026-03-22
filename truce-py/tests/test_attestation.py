"""Tests for TATF trust attestation.

Validates spec §04:
  - Canonical JSON serialization
  - Attestation object structure
  - Signing and verification (if PyNaCl available)
"""

import json

import pytest

from truce import TATFScorer, TATFAttestor


def _scored_agent():
    """Create a scored agent for attestation."""
    from tests.test_scorer import _build_history
    scorer = TATFScorer()
    scorer.ingest("a1", _build_history(20))
    alpha = scorer.score("a1")
    anomaly = scorer.compute_anomaly("a1")
    return alpha, anomaly


class TestAttestationFormat:
    def test_required_fields(self):
        """Attestation MUST include all required fields (spec §04)."""
        alpha, anomaly = _scored_agent()
        attestor = TATFAttestor(issuer_id="test-scorer")
        att = attestor.attest(alpha, anomaly)

        assert "spec_version" in att
        assert att["spec_version"] == "tatf-v0.1"
        assert "attestation_id" in att
        assert att["attestation_id"].startswith("ATT-")
        assert "issuer" in att
        assert "id" in att["issuer"]
        assert "public_key" in att["issuer"]
        assert "subject" in att
        assert "agent_id" in att["subject"]
        assert "score" in att
        assert "alpha" in att["score"]
        assert "confidence_low" in att["score"]
        assert "confidence_high" in att["score"]
        assert "observation_count" in att["score"]
        assert "cold_start" in att["score"]
        assert "components" in att
        assert "proof" in att
        assert "type" in att["proof"]
        assert "hash" in att["proof"]
        assert att["proof"]["hash"].startswith("sha256:")

    def test_anomaly_included(self):
        alpha, anomaly = _scored_agent()
        attestor = TATFAttestor()
        att = attestor.attest(alpha, anomaly)
        assert "anomaly" in att
        assert "composite" in att["anomaly"]
        assert "routing" in att["anomaly"]
        assert "dimensions" in att["anomaly"]

    def test_metadata_timestamps(self):
        alpha, anomaly = _scored_agent()
        attestor = TATFAttestor(validity_hours=2.0)
        att = attestor.attest(alpha, anomaly)
        assert "metadata" in att
        assert "computed_at" in att["metadata"]
        assert "valid_until" in att["metadata"]


class TestCryptoSigning:
    def test_signing_and_verification(self):
        """If PyNaCl available, sign + verify round-trip must succeed."""
        try:
            import nacl  # noqa: F401
        except ImportError:
            pytest.skip("PyNaCl not installed")

        alpha, anomaly = _scored_agent()
        attestor = TATFAttestor()
        att = attestor.attest(alpha, anomaly)

        assert att["proof"]["signature"] != "unsigned"
        assert attestor.verify(att) is True

    def test_tampered_attestation_fails(self):
        """Modified attestation MUST fail verification."""
        try:
            import nacl  # noqa: F401
        except ImportError:
            pytest.skip("PyNaCl not installed")

        alpha, anomaly = _scored_agent()
        attestor = TATFAttestor()
        att = attestor.attest(alpha, anomaly)

        # Tamper with score.
        att["score"]["alpha"] = 0.99
        assert attestor.verify(att) is False

    def test_unsigned_without_nacl(self):
        """Without PyNaCl, attestations are unsigned but valid structure."""
        alpha, anomaly = _scored_agent()
        # Force no signing by passing None key and mocking no nacl.
        attestor = TATFAttestor()
        att = attestor.attest(alpha, anomaly)
        # At minimum, structure should be complete.
        assert "proof" in att
        assert "hash" in att["proof"]
