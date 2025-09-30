#!/usr/bin/env python3
"""Script para ejecutar specs del bench localmente.

Ejemplos:
    python -m professor_tools.run_bench --list
    python -m professor_tools.run_bench run add_basic simple_funcs:add

Esto carga la spec JSON y ejecuta grade() con un estudiante ficticio S1.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from ub_grader import grade, init_students, load_spec

BENCH_DIR = Path(__file__).parent / "spec_bench"


def list_specs():
    """Imprimir la lista de specs disponibles (nombres sin extensión)."""
    for p in sorted(BENCH_DIR.glob("*.json")):
        print(p.stem)


def _import_callable(dotted: str):
    """Importar y devolver una función referenciada como ``modulo:func``."""
    mod_name, _, func_name = dotted.partition(":")
    if not func_name:
        raise ValueError("Usar formato modulo:funcion")
    mod = importlib.import_module(
        f"professor_tools.{mod_name}" if not mod_name.startswith("professor_tools") else mod_name
    )
    func = getattr(mod, func_name)
    return func


def run_spec(spec_name: str, func_ref: str):
    """Ejecutar una spec de bench contra la función indicada."""
    spec_path = BENCH_DIR / f"{spec_name}.json"
    if not spec_path.exists():
        raise SystemExit(f"Spec no encontrada: {spec_name}")
    load_spec(spec_path.as_uri())
    init_students([{"niub": "S1", "nombre": "Demo", "apellidos": "User"}])
    func = _import_callable(func_ref)
    result = grade(
        func,
        student_id="S1",
        public_key_path=None,
        signing_key_path=None,
        output_path=f"bench_report_{spec_name}.enc",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main(argv=None):  # pragma: no cover
    p = argparse.ArgumentParser()
    p.add_argument(
        "action",
        nargs="?",
        choices=["--list", "run"],
        default="--list",
    )
    p.add_argument("spec", nargs="?")
    p.add_argument("callable", nargs="?")
    args = p.parse_args(argv)

    if args.action == "--list":
        list_specs()
    elif args.action == "run":
        if not args.spec or not args.callable:
            p.error("run requiere spec y callable")
        run_spec(args.spec, args.callable)
    else:
        p.error("Acción desconocida")


if __name__ == "__main__":  # pragma: no cover
    main()
