"""Public package interface for ub_grader.

This package exposes a minimal surface intended for student / script usage:

Functions
---------
init_students(students)
    Initialize the in‑memory student registry with iterable entries.
get_student(student_id)
    Retrieve a previously registered student (primarily for internal use).
load_spec(url)
    Load and validate an assignment specification JSON (local path or HTTP).
grade(func, student_id, public_key_path=None, signing_key_path=None,
            output_path=None)
        Execute all tests in the loaded spec against the provided callable
        and emit an encrypted grading report.

Only these names are exported via ``__all__`` to keep the public API small.
"""

from .grader import grade
from .spec_loader import load_spec
from .students import get_student, init_students

# Expose a runtime package version (PEP 621 metadata) for tooling / debugging.
try:  # pragma: no cover
    from importlib.metadata import (
        PackageNotFoundError,
    )
    from importlib.metadata import (  # type: ignore
        version as _pkg_version,
    )
except ImportError:  # pragma: no cover
    from importlib_metadata import (
        PackageNotFoundError,  # type: ignore
    )
    from importlib_metadata import (  # type: ignore
        version as _pkg_version,
    )

try:  # pragma: no cover - normal path
    __version__ = _pkg_version("ub-grader")
except PackageNotFoundError:  # pragma: no cover - editable/no install context
    __version__ = "0.0.0+unknown"

__all__ = [
    "init_students",
    "get_student",
    "load_spec",
    "grade",
    "__version__",
]
