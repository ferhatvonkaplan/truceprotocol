"""TATF Trust Attestation — Cryptographic attestation generation.

Reference implementation of TATF spec v0.1 §04.

Supports TATF Native format. W3C VC format is a TODO for v0.2.

Signing requires PyNaCl (optional dependency):
    pip install truce[crypto]
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .models import AlphaScore, AnomalyScore


def _canonical_json(obj: Any) -> bytes:
    """Deterministic JSON serialization (sorted keys, no whitespace).

    Per TATF spec §04: canonical form uses sorted keys and compact
    separators for byte-identical output across implementations.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    """SHA-256 hash, returned as hex string."""
    return hashlib.sha256(data).hexdigest()


class TATFAttestor:
    """Generates cryptographically signed TATF trust attestations.

    Parameters
    ----------
    issuer_id : str
        Unique identifier for this scorer/issuer.
    issuer_name : str
        Human-readable issuer name.
    private_key_seed : bytes, optional
        32-byte Ed25519 seed. If None, a random keypair is generated.
        Requires PyNaCl: ``pip install truce[crypto]``
    validity_hours : float
        How long attestations remain valid. Default 1.0.
    """

    def __init__(
        self,
        issuer_id: str = "local-scorer",
        issuer_name: str = "TATF Local Scorer",
        private_key_seed: Optional[bytes] = None,
        validity_hours: float = 1.0,
    ) -> None:
        self._issuer_id = issuer_id
        self._issuer_name = issuer_name
        self._validity = timedelta(hours=validity_hours)
        self._signing_key = None
        self._verify_key_hex: Optional[str] = None

        try:
            from nacl.signing import SigningKey

            if private_key_seed:
                self._signing_key = SigningKey(private_key_seed)
            else:
                self._signing_key = SigningKey.generate()
            self._verify_key_hex = self._signing_key.verify_key.encode().hex()
        except ImportError:
            # PyNaCl not installed — attestations won't be signed.
            pass

    @property
    def public_key_hex(self) -> Optional[str]:
        """Hex-encoded Ed25519 public key, or None if crypto unavailable."""
        return self._verify_key_hex

    def attest(
        self,
        alpha: AlphaScore,
        anomaly: Optional[AnomalyScore] = None,
    ) -> Dict[str, Any]:
        """Generate a TATF Native attestation for an ALPHA score.

        Returns the attestation dict (spec §04 format). If PyNaCl is
        installed, includes cryptographic proof. Otherwise, proof
        contains the hash but signature is "unsigned".
        """
        now = datetime.now(timezone.utc)
        att_id = f"ATT-{secrets.token_hex(8)}"

        # Build payload.
        payload: Dict[str, Any] = {
            "spec_version": "tatf-v0.1",
            "attestation_id": att_id,
            "issuer": {
                "id": self._issuer_id,
                "name": self._issuer_name,
                "public_key": f"ed25519:{self._verify_key_hex or 'none'}",
            },
            "subject": {
                "agent_id": alpha.agent_id,
            },
            "score": {
                "alpha": alpha.score,
                "confidence_low": alpha.confidence_low,
                "confidence_high": alpha.confidence_high,
                "observation_count": alpha.observation_count,
                "cold_start": alpha.cold_start,
            },
            "components": {
                "agent_trust": alpha.components.agent_trust,
                "market_stability": alpha.components.market_stability,
                "transaction_history": alpha.components.transaction_history,
                "counterparty_score": alpha.components.counterparty_score,
            },
        }

        # Anomaly breakdown (optional but SHOULD include).
        if anomaly:
            payload["anomaly"] = {
                "composite": anomaly.composite,
                "routing": anomaly.routing.value,
                "dimensions": {
                    "s_time": anomaly.dimensions.s_time,
                    "s_concurrent": anomaly.dimensions.s_concurrent,
                    "s_price": anomaly.dimensions.s_price,
                    "s_category": anomaly.dimensions.s_category,
                    "s_rounds": anomaly.dimensions.s_rounds,
                    "s_counterparty": anomaly.dimensions.s_counterparty,
                },
            }

        payload["metadata"] = {
            "computed_at": now.isoformat(),
            "valid_until": (now + self._validity).isoformat(),
            "sector": alpha.sector,
            "counterparty_id": alpha.counterparty_id,
        }

        # Cryptographic proof.
        canonical = _canonical_json(payload)
        hash_hex = _sha256_hex(canonical)
        timestamp_iso = now.isoformat()

        # Signing input: hash_hex|timestamp (spec §04).
        sign_input = f"{hash_hex}|{timestamp_iso}".encode("utf-8")

        if self._signing_key:
            signed = self._signing_key.sign(sign_input)
            sig_hex = signed.signature.hex()
        else:
            sig_hex = "unsigned"

        payload["proof"] = {
            "type": "Ed25519Signature",
            "hash": f"sha256:{hash_hex}",
            "signature": sig_hex,
            "signed_at": timestamp_iso,
        }

        return payload

    def verify(self, attestation: Dict[str, Any], public_key_hex: Optional[str] = None) -> bool:
        """Verify a TATF attestation's cryptographic proof.

        Parameters
        ----------
        attestation : dict
            The full attestation object.
        public_key_hex : str, optional
            Issuer's Ed25519 public key (hex). If None, uses self.

        Returns True if valid, False otherwise.
        """
        try:
            from nacl.signing import VerifyKey
        except ImportError:
            raise ImportError("PyNaCl required for verification: pip install truce[crypto]")

        proof = attestation.get("proof", {})
        sig_hex = proof.get("signature", "")
        hash_str = proof.get("hash", "")
        signed_at = proof.get("signed_at", "")

        if sig_hex == "unsigned":
            return False

        # Reconstruct canonical payload (everything except proof).
        payload = {k: v for k, v in attestation.items() if k != "proof"}
        canonical = _canonical_json(payload)
        expected_hash = f"sha256:{_sha256_hex(canonical)}"

        if hash_str != expected_hash:
            return False

        # Verify signature.
        key_hex = public_key_hex or self._verify_key_hex
        if not key_hex:
            return False

        sign_input = f"{_sha256_hex(canonical)}|{signed_at}".encode("utf-8")
        try:
            vk = VerifyKey(bytes.fromhex(key_hex))
            vk.verify(sign_input, bytes.fromhex(sig_hex))
            return True
        except Exception:
            return False
