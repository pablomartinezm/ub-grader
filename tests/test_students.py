import pytest

from ub_grader import get_student, init_students


def test_init_and_get_student():
    init_students(
        [
            {"niub": "A1", "nombre": "Ana", "apellidos": "Lopez"},
            {"niub": "B2", "nombre": "Beto", "apellidos": "Ruiz"},
        ]
    )
    s = get_student("A1")
    assert s.nombre == "Ana"
    with pytest.raises(KeyError):
        get_student("NOPE")


def test_duplicate_id():
    with pytest.raises(ValueError):
        init_students(
            [
                {"niub": "X1"},
                {"niub": "X1"},
            ]
        )


def test_invalid_id():
    with pytest.raises(ValueError):
        init_students(
            [
                {"niub": "ID-1"},
            ]
        )
