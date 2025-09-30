"""In‑memory student registry utilities.

The registry stores ``Student`` entries keyed by an alphanumeric ID. It
accepts legacy Spanish field names (``niub``, ``nombre``, ``apellidos``) as
well as modern English equivalents (``id``, ``first_name``, ``last_name``).

Only two helper functions are exported publicly: :func:`init_students` and
:func:`get_student` – the rest is considered internal implementation detail.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(slots=True)
class Student:
    """Student registry entry.

    Internal attribute names keep Spanish field names (nombre/apellidos)
    for backward compatibility with earlier versions. English accessor
    properties (first_name / last_name) and public serialization now
    use English keys.
    """

    id: str
    nombre: str
    apellidos: str

    # English property aliases (read-only) ---------------------------------
    @property
    def first_name(self) -> str:  # pragma: no cover - simple alias
        return self.nombre

    @property
    def last_name(self) -> str:  # pragma: no cover - simple alias
        return self.apellidos

    def to_public(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.nombre,
            "last_name": self.apellidos,
        }


class _StudentRegistry:
    def __init__(self) -> None:
        self._students: dict[str, Student] = {}

    def init(self, students: Iterable[dict | Student]) -> None:
        """Populate the registry from an iterable of dicts or ``Student``.

        Validation performed:
        * Accept legacy keys (``niub`` / ``student_id``) or modern ``id``.
        * Require unique alphanumeric IDs.
        * Map Spanish or English name keys to internal attributes.
        """
        tmp: dict[str, Student] = {}
        for s in students:
            if isinstance(s, dict):
                # Accept legacy and new keys: niub | student_id | id
                sid = s.get("niub") or s.get("student_id") or s.get("id")
                if not sid:
                    raise ValueError("Missing 'niub'/'student_id' in student entry")
                student = Student(
                    id=str(sid),
                    # Prefer English keys if present
                    nombre=s.get("first_name") or s.get("nombre", ""),
                    apellidos=s.get("last_name") or s.get("apellidos", ""),
                )
            elif isinstance(s, Student):
                student = s
            else:
                raise TypeError("Unsupported student entry type")
            if not student.id.isalnum():
                raise ValueError(f"Non-alphanumeric ID: {student.id}")
            if student.id in tmp:
                raise ValueError(f"Duplicate ID: {student.id}")
            tmp[student.id] = student
        self._students = tmp

    def get(self, student_id: str) -> Student:
        """Return the student with ``student_id`` or raise ``KeyError``."""
        try:
            return self._students[student_id]
        except KeyError as exc:
            # Re-raise with clearer message
            raise KeyError(f"Student not found: {student_id}") from exc

    def all(self) -> list[Student]:
        """Return a list of all registered students."""
        return list(self._students.values())


_registry = _StudentRegistry()


def init_students(students: Iterable[dict | Student]) -> None:
    """Public wrapper to initialise the global student registry."""
    _registry.init(students)


def get_student(student_id: str) -> Student:
    """Lookup a student by ID from the global registry."""
    return _registry.get(student_id)
