Bench de especificaciones de ejemplo para pruebas locales del grader.

Contenido:

- add_basic.json: suma de dos enteros, dos casos.
- factorial.json: factorial iterativo con límites de tiempo.
- fibonacci_hidden.json: incluye caso oculto (expected_hidden true) y clave pública incrustada.
- sorting.json: prueba función sort_list con comparación de igualdad.

Uso rápido:
python -m professor_tools.run_bench --list
python -m professor_tools.run_bench run add_basic simple_funcs:add

Las specs usan el formato soportado por ub_grader.spec_loader.load_spec.
