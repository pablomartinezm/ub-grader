# Quickstart for Professors

Quick guide to:

- Create / validate an assignment spec
- Distribute it to students
- Test it locally with the included bench
- Decrypt and (optionally) verify received reports

## 1. Key components

| Component               | Location                           | Description                                             |
| ----------------------- | ---------------------------------- | ------------------------------------------------------- |
| Spec loader             | `ub_grader.spec_loader.load_spec`  | Loads and validates basic structure of JSON spec        |
| Grader / scoring        | `ub_grader.grader.grade`           | Executes tests and produces encrypted + signed report   |
| Decrypt tool            | `professor_tools/decrypt_report.py`| Decrypts and verifies student reports                   |
| Spec bench examples     | `professor_tools/spec_bench/`      | Ready-to-use example specs                              |

## 2. Minimal spec format

```json
{
  "version": "1.0.0",
  "assignment_id": "p1",
  "tests": [
    {
      "id": "t1",
      "input": { "args": [1, 2], "kwargs": {} },
      "expected": 3,
      "weight": 1
    }
  ],
  "scoring": {
    "mode": "weighted_sum_with_penalties",
    "rounding": 2,
    "penalties": {},
    "max_score": 10
  },
  "integrity": {}
}
```

Relevant fields per test:

- `input.args` / `input.kwargs` (list + dict)
- `expected` (value used for comparison)
- `expected_hidden` (if true not revealed to students)
- `time_limit_ms` (per test; default 500)
- `memory_limit_kb` (default 10000)
- `weight` (float; sum defines scaling)
- `comparison` ("equal" | "approx")

## 3. Embedded public key (recommended)

Embedding the RSA public key directly avoids separate distribution:

```json
"public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
```

If `public_key` is absent students must supply one (recommended: embed).

## 4. Generate integrity hash (optional strictness)

The loader checks `integrity.hash` if present (`sha256:HEX`). To generate it over canonical JSON (without `integrity.signature`):

```python
import json, hashlib
raw = json.loads(open('spec.json').read())
# Asegurarse de no tener integrity.hash temporal antes de calcular
h = hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
raw.setdefault('integrity', {})['hash'] = f'sha256:{h}'
open('spec.json','w').write(json.dumps(raw, indent=2, ensure_ascii=False))
```

## 5. Local bench included

To test specs without student solutions:

List specs:

```bash
PYTHONPATH=. python -m professor_tools.run_bench --list
```

Run a spec against sample function:

```bash
PYTHONPATH=. python -m professor_tools.run_bench run add_basic simple_funcs:add
```

Generates `bench_report_add_basic.enc` and prints scoring.

Bench structure (`professor_tools/spec_bench`):

- `add_basic.json` (addition)
- `factorial.json` (factorial + possible time penalties)
- `fibonacci_hidden.json` (hidden case + embedded `public_key`)
- `sorting.json` (lists)

Helper functions: `professor_tools/simple_funcs.py`.

Duplicate and adapt one JSON: change `assignment_id`, add tests, adjust weights/limits.

## 6. Typical process for a new assignment

1. Copy `add_basic.json` -> `a2.json` and edit.
2. Embed `public_key` (PEM) for independence.
3. (Optional) Compute and add `integrity.hash`.
4. Host the spec (HTTPS recommended) or share via LMS.
5. Publish instructions: students call `load_spec("https://.../a2.json")`.
6. Receive `report_<niub>_a2.enc` files.
7. Decrypt / verify (next section).

## 7. Decrypt and verify reports

You need:

- RSA private key matching the public key used to encrypt.
- (Optional) Ed25519 public key if students sign.

Example:

```bash
python professor_tools/decrypt_report.py \
  --rsa-private RSA_PRIVADA.pem \
  --ed25519-public ED25519_PUB.pem \
  report_A123_p2.enc > reporte_A123.json
```

Output: JSON with fields `tests`, `scoring`, `student`, etc.

If a `signature` is present and you omit `--ed25519-public` a warning is printed.

## 8. Batch decrypt & extract scores (basic idea)

Given a folder with reports:

```bash
for f in report_*_p2.enc; do \
  python professor_tools/decrypt_report.py --rsa-private RSA_PRIVADA.pem "$f" > "${f%.enc}.json"; \
  echo "$f -> $(jq -r '.scoring.final_score' "${f%.enc}.json")"; \
done
```

Then consolidate with `jq` or a Python script.

## 9. Test design best practices

- Few high-weight tests + several light ones for granularity.
- Use `expected_hidden` for cases revealing logic.
- Set realistic time limits (measure locally, add ~2x margin).
- Penalize only meaningful excesses (keep noise low).
- Consider a hidden stress test with moderate weight.

## 10. Troubleshooting

| Symptom                                 | Possible cause                      | Action                                           |
| --------------------------------------- | ----------------------------------- | ------------------------------------------------ |
| `Integrity hash does not match`         | Spec edited after hash generated    | Recompute hash or remove field while editing     |
| Report fails to decrypt                 | Wrong private key                   | Verify key pair and PEM format                   |
| Missing test field                      | JSON authoring error                | Validate with a linter / `python -m json.tool`   |
| Score always 0                          | Zero weights or wrong comparison    | Review `weight` and `comparison`                 |
| Memory > limit                          | Limit too low                       | Increase `memory_limit_kb`                       |

## 11. Publication checklist

- [ ] Unique `assignment_id`
- [ ] All tests with unique `id`
- [ ] Weights reviewed (reasonable sum)
- [ ] Embedded `public_key` (or distribution plan confirmed)
- [ ] (Optional) `integrity.hash` regenerated after last change
- [ ] Local run with reference solution passes 100%
- [ ] Student instructions prepared

## 12. Possible next steps / extensions

- Ed25519 signing of spec itself (`integrity.signature`)
- Metadata fields (author, date, reference version)
- Official JSON Schema + validator
- CLI tool to package and sign specs

---

Guide version: 1.0.0
