"""Specification loading and integrity verification.

This module loads assignment specification JSON documents (local files via
``Path.as_uri()`` or remote HTTP/HTTPS). It validates required fields, builds
strongly‑typed dataclass instances, and verifies an optional integrity hash
of the canonical JSON (excluding any embedded signature).

The loader stores the last loaded spec in a private module state so other
parts of the package (notably :mod:`ub_grader.grader`) can access it without
plumbing the object around explicitly.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class TestSpec:
    """Single test specification entry.

    Attributes mirror the JSON structure. ``expected_hidden`` controls whether
    the expected value (and the student's actual result when failing) are
    hidden in reports to avoid leaking secret tests.
    """

    id: str
    description: str
    input_args: list
    input_kwargs: dict
    expected: Any
    expected_hidden: bool
    time_limit_ms: int
    memory_limit_kb: int
    weight: float
    comparison: str


@dataclass
class ScoringSpec:
    """Scoring configuration for an assignment.

    ``mode`` currently supports ``weighted_sum_with_penalties``; rounding is
    the number of decimal places for final values; ``penalties`` is a mapping
    of configurable penalty coefficients and ``max_score`` caps the final
    achievable score.
    """

    mode: str
    rounding: int
    penalties: dict
    max_score: float


@dataclass
class Spec:
    """Top‑level loaded specification container."""

    version: str
    assignment_id: str
    tests: list[TestSpec]
    scoring: ScoringSpec
    integrity: dict
    # Optional embedded RSA public key (PEM)
    public_key: str | None = None


_SPEC_STATE: list[Spec | None] = [None]


def _validate_basic(data: dict) -> None:
    """Perform minimal structural validation of raw spec data.

    Raises ``ValueError`` on missing required top‑level fields or malformed
    ``tests`` list.
    """
    required_top = ["version", "assignment_id", "tests", "scoring"]
    for k in required_top:
        if k not in data:
            raise ValueError(f"Missing required field: {k}")
    if not isinstance(data["tests"], list) or not data["tests"]:
        raise ValueError("'tests' must be a non-empty list")


def _hash_ok(data: dict) -> bool:
    """Return ``True`` if the integrity hash (if any) matches.

    The hash field format is ``<algo>:<hex>`` where *algo* is any hashlib
    supported algorithm. The hash is computed over a canonical JSON rendering
    of the spec with any signature removed.
    """
    integ = data.get("integrity") or {}
    # ref = integ.get("hash")
    # if not ref:
    #    return True
    for algo_name in integ:
        if algo_name != "signature":
            h = hashlib.new(algo_name)
            hexval = integ[algo_name]
            # Hash of canonical JSON without integrity.signature if present
            clone = dict(data)
            if "integrity" in clone and isinstance(clone["integrity"], dict):
                clone["integrity"] = {}
            canonical = json.dumps(
                clone,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()

            h.update(canonical)
            if h.hexdigest() != hexval:
                return False
    return True


def load_spec(url: str) -> Spec:
    """Load a specification from a URL or file URI and cache it.

    Parameters
    ----------
    url: str
        HTTP(S) URL or ``file://`` URI pointing to the JSON spec.
    """
    with urllib.request.urlopen(url) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    _validate_basic(data)
    if not _hash_ok(data):
        raise ValueError("Integrity hash does not match")

    tests: list[TestSpec] = []
    for t in data["tests"]:
        tests.append(
            TestSpec(
                id=t["id"],
                description=t.get("description", ""),
                input_args=(t.get("input", {}).get("args") or []),
                input_kwargs=(t.get("input", {}).get("kwargs") or {}),
                expected=t.get("expected"),
                expected_hidden=bool(t.get("expected_hidden", False)),
                time_limit_ms=int(t.get("time_limit_ms", 500)),
                memory_limit_kb=int(t.get("memory_limit_kb", 10_000)),
                weight=float(t.get("weight", 1.0)),
                comparison=t.get("comparison", "equal"),
            )
        )

    scoring_raw = data["scoring"]
    scoring = ScoringSpec(
        mode=scoring_raw.get("mode", "weighted_sum_with_penalties"),
        rounding=int(scoring_raw.get("rounding", 2)),
        penalties=scoring_raw.get("penalties", {}),
        max_score=float(scoring_raw.get("max_score", 10.0)),
    )

    spec_obj = Spec(
        version=data["version"],
        assignment_id=data["assignment_id"],
        tests=tests,
        scoring=scoring,
        integrity=data.get("integrity", {}),
        public_key=data.get("public_key"),
    )
    _SPEC_STATE[0] = spec_obj
    return spec_obj


def get_loaded_spec() -> Spec:
    """Return the last loaded spec or raise ``RuntimeError`` if absent."""
    spec_obj = _SPEC_STATE[0]
    if spec_obj is None:
        raise RuntimeError("No spec loaded")
    return spec_obj
