"""Funciones simples de ejemplo para el bench de specs."""

from __future__ import annotations


def add(a, b):
    """Return ``a + b`` (función de ejemplo)."""
    return a + b


def factorial(n: int) -> int:
    """Compute factorial iterativamente; ``n`` debe ser >= 0."""
    if n < 0:
        raise ValueError("n negativo")
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


def fibonacci(n: int) -> int:
    """Return el n‑ésimo número de Fibonacci (0-indexado)."""
    if n < 0:
        raise ValueError("n negativo")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def sort_list(xs):
    """Devolver una nueva lista ordenada ascendentemente."""
    return sorted(xs)
