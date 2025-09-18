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

__all__ = [
    "init_students",
    "get_student",
    "load_spec",
    "grade",
]
