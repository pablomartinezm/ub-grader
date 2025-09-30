"""Grading and encrypted report generation utilities.

The grading workflow assumes that:

1. A spec has already been loaded via :func:`ub_grader.load_spec`.
2. Students have been initialised with :func:`ub_grader.init_students`.
3. A callable (student submission) is provided to :func:`grade`.

Timing and peak memory usage (via ``tracemalloc``) are measured per test and
fed into a scoring routine that can apply penalties for exceeding limits.
Reports are encrypted (and optionally signed) to avoid tampering while still
being easily verifiable by instructors.

Support for an embedded default RSA public key was removed; a key must now
be provided either inline in the spec (``public_key``) or via the
``public_key_path`` argument to :func:`grade`.
"""

from __future__ import annotations

import json
import time
import tracemalloc
from collections.abc import Callable
from typing import Any

from .crypto_utils import encrypt_and_sign
from .spec_loader import Spec, TestSpec, get_loaded_spec
from .students import get_student

# (No public symbols defined at module level besides grade())


class TestResultDict(dict[str, Any]):
    """Single test execution result."""

    def __repr__(self) -> str:  # helpful for debugging
        return f"TestResultDict({dict(self)})"


def _compare(expected, got, comparison: str) -> bool:
    """Compare expected vs. actual according to the selected strategy.

    Supported strategies:
    * ``equal``  – direct equality.
    * ``approx`` – numeric tolerance (absolute difference <= 1e-6).
    """
    tolerance = 1e-6
    if comparison == "equal":
        return expected == got
    if comparison == "approx":
        # Simple approximate comparison for numeric values
        if isinstance(expected, int | float) and isinstance(got, int | float):
            return abs(expected - got) <= tolerance
        return False
    return False


def _run_single(func: Callable, spec: TestSpec) -> TestResultDict:
    """Execute one test spec against the provided callable.

    Captures execution time and peak memory usage (in KB). Hidden tests omit
    expected (and sometimes actual) values to avoid leaking secret cases.
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    error = None
    passed = False
    got = None
    try:
        got = func(*spec.input_args, **spec.input_kwargs)
        passed = _compare(spec.expected, got, spec.comparison)
    except (AssertionError, ValueError, TypeError, RuntimeError) as err:
        error = f"{type(err).__name__}: {err}"
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    _current_bytes, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mem_kb = peak / 1024.0

    if elapsed_ms > spec.time_limit_ms:
        passed = False
    if mem_kb > spec.memory_limit_kb:
        passed = False

    return TestResultDict(
        id=spec.id,
        passed=passed,
        time_ms=round(elapsed_ms, 3),
        memory_kb=round(mem_kb, 1),
        error=error,
        # Do not reveal expected value nor student's output if hidden
        expected=None if spec.expected_hidden else spec.expected,
        got=got if passed or not spec.expected_hidden else None,
    )


def _score(spec: Spec, test_results: list[TestResultDict]) -> dict[str, Any]:
    """Aggregate per‑test results into a scoring summary.

    Applies weighting and optional penalties for time / memory overages as
    configured in the spec's ``scoring.penalties`` mapping.
    """
    penalties_cfg = spec.scoring.penalties or {}
    max_score = spec.scoring.max_score
    total_weight = sum(t.weight for t in spec.tests)
    acc = 0.0
    penalty_total = 0.0

    for t_spec, res in zip(spec.tests, test_results, strict=False):
        if t_spec.weight <= 0:
            continue
        if res["passed"]:
            acc += t_spec.weight
        # Penalties for time/memory overages
        if res["time_ms"] > t_spec.time_limit_ms:
            over = res["time_ms"] - t_spec.time_limit_ms
            penalty_total += over * float(penalties_cfg.get("time_over_ms", 0))
        if res["memory_kb"] > t_spec.memory_limit_kb:
            overm = res["memory_kb"] - t_spec.memory_limit_kb
            penalty_total += overm * float(penalties_cfg.get("memory_over_kb", 0))

    ratio = acc / total_weight if total_weight > 0 else 0.0
    raw_score = ratio * max_score
    final_score = max(0.0, raw_score - penalty_total)
    final_score = round(final_score, spec.scoring.rounding)
    return {
        "ratio_passed": round(ratio, 4),
        "raw_score": round(raw_score, spec.scoring.rounding),
        "penalties": round(penalty_total, spec.scoring.rounding),
        "final_score": final_score,
        "max_score": max_score,
    }


def grade(
    func: Callable,
    students_id: list[str],
    public_key_path: str | None = None,
    signing_key_path: str | None = None,
    output_path: str | None = None,
) -> Any:
    """Run all loaded spec tests against ``func`` for ``student_id``.

    Parameters
    ----------
    func:
        Callable implementing the student's solution.
    students_id:
        List of identifiers (one or more) of previously registered students via :func:`init_students`.
    public_key_path:
        Path to RSA public key PEM (overrides any embedded ``public_key`` in
        the spec). One of this or the embedded key must be present.
    signing_key_path:
        Optional Ed25519 private key (PEM) to sign the canonical JSON report
        prior to encryption.
    output_path:
        Optional filename for the encrypted report. Defaults to
        ``report_<student>_<assignment>.enc``.

    Returns
    -------
    dict
        Scoring summary (also printed). The encrypted report is written to
        disk as a side effect.
    """
    students = []
    for s_id in students_id:
        students.append(get_student(s_id))
    spec = get_loaded_spec()

    test_results: list[TestResultDict] = []
    for t in spec.tests:
        test_results.append(_run_single(func, t))

    scoring = _score(spec, test_results)

    report_payload = {
        "student": [student.to_public() for student in students],
        "assignment_id": spec.assignment_id,
        "spec_version": spec.version,
        "tests": test_results,
        "scoring": scoring,
    }

    # Priority: explicit argument > spec.public_key
    rsa_path: str | None = None
    rsa_pem: str | None = None
    if public_key_path:
        rsa_path = public_key_path
    elif getattr(spec, "public_key", None):  # per-spec PEM
        rsa_pem = spec.public_key  # type: ignore[assignment]
    else:
        raise ValueError(
            "A public RSA key must be supplied via spec.public_key or the "
            "public_key_path argument; the embedded fallback was removed."
        )

    encrypted = encrypt_and_sign(
        report_payload,
        rsa_public_key_path=rsa_path,
        rsa_public_key_pem=rsa_pem,
        ed25519_signing_key_path=signing_key_path,
    )
    filename = output_path or f"report_{'_'.join([student.id for student in students])}_{spec.assignment_id}.enc"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(encrypted, f, ensure_ascii=False)

    # Display grade to user
    print(f"Grade: {scoring['final_score']} / {scoring['max_score']}")
    return scoring
