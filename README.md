# ub-grader

Library enabling students to self-grade assignments locally and generate an encrypted (AES-256-GCM + RSA) and optionally signed (Ed25519) report to send to instructors.

## Table of Contents

1. Goals / Features
2. Quick Installation
3. Student Usage (summary)
4. Instructor Usage (summary)
5. End-to-End Flow
6. Spec Format (summary)
7. Encrypted Report & Signing
8. Test Design Best Practices
9. Development (lint, tests, pre-commit)
10. Publishing to PyPI
11. Roadmap
12. Recent Changes
13. License

## 1. Goals / Features

- Student registry (alphanumeric NIUB / student id)
- Load test specifications from URL (`http(s)` or `file://`)
- Per-test time and memory limits
- Configurable penalties (time, memory) in scoring
- Optional hiding of expected values (`expected_hidden`)
- Hybrid encryption for report confidentiality
- Optional Ed25519 signing for authenticity
- Optional spec integrity hash (`integrity.hash`)

## 2. Quick Installation

```bash
pip install ub-grader
```

Requires Python 3.10+.

## 3. Student Usage (summary)

Full guide: see `QUICKSTART_STUDENTS.md`.

```python
from ub_grader import init_students, load_spec, grade
from solution import solve  # your target function

init_students([
  {"niub": "A123", "first_name": "Alice", "last_name": "Doe"},
])

load_spec("https://server/assignments/p1.json")  # or file:///abs/path/p1.json

result = grade(
  solve,
  student_id="A123",
  signing_key_path=None,  # Path to Ed25519 private key if signing
)

print("Final score:", result["final_score"], "/", result["max_score"])
```

File generated: `report_A123_<assignment_id>.enc` (do not open or modify).

## 4. Instructor Usage (summary)

Full guide: see `QUICKSTART_PROFESSORS.md`.

Typical steps:

1. Copy a spec from `professor_tools/spec_bench/` (e.g. `add_basic.json`).
2. Adjust `assignment_id`, tests, weights, limits, and embed `public_key` (recommended).
3. (Optional) Compute `integrity.hash` after final edit.
4. Host the spec (HTTPS or LMS).
5. Receive `report_<niub>_<assignment_id>.enc` files from students.
6. Decrypt:

```bash
python professor_tools/decrypt_report.py \
  --rsa-private RSA_PRIVATE.pem \
  report_A123_p1.enc > report_A123.json
```

7. (Optional) Verify Ed25519 signature adding `--ed25519-public ED25519_PUB.pem`.

Quick local bench:

```bash
PYTHONPATH=. python -m professor_tools.run_bench --list
PYTHONPATH=. python -m professor_tools.run_bench run add_basic simple_funcs:add
```

## 5. End-to-End Flow

1. Instructor designs and publishes spec.
2. Student registers and loads the spec.
3. Student runs `grade()` producing encrypted report.
4. Student submits the `.enc` file.
5. Instructor decrypts and optionally verifies signature.
6. Final score consolidated.

## 6. Spec Format (minimal summary)

```json
{
  "version": "1.0.0",
  "assignment_id": "p1",
  "tests": [
    {
      "id": "t1",
      "input": { "args": [1, 2], "kwargs": {} },
      "expected": 3,
      "weight": 1,
      "expected_hidden": false,
      "time_limit_ms": 500,
      "memory_limit_kb": 10000,
      "comparison": "equal"
    }
  ],
  "scoring": {
    "mode": "weighted_sum_with_penalties",
    "rounding": 2,
    "penalties": {},
    "max_score": 10
  },
  "integrity": {},
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
}
```

Notes:

- `expected_hidden: true` hides expected value in student report.
- Optional penalties (`penalties.time_over_ms`, `penalties.memory_over_kb`).
- If `public_key` missing student must pass one (embed recommended).
- `integrity.hash` can be added as `sha256:HEX`.

## 7. Encrypted Report & Signing

Output file: `report_<niub>_<assignment_id>.enc`.

Decrypted content includes:

- Spec metadata (id, version)
- Test list (pass/fail, time, memory)
- Partial & final score (`final_score`, `max_score`)
- Student info
- (Optional) Ed25519 signature of canonical JSON prior to encryption

Decrypt (instructor):

```bash
python professor_tools/decrypt_report.py --rsa-private RSA_PRIVATE.pem report_A123_p1.enc > report.json
```

Verify signature (if student signed): add `--ed25519-public ED25519_PUB.pem`.

## 8. Test Design Best Practices

- Few high-weight tests + several light ones for granularity.
- Use `expected_hidden` for logic-revealing cases.
- Set time limits from real measurements (+ ~2x margin).
- Penalize only significant excess.
- Consider a hidden stress test of moderate weight.

## 9. Development (lint, tests, pre-commit)

Install dev environment:

```bash
pip install -e .[dev]
```

Lint & format (Ruff):

```bash
ruff check . --fix
ruff format .
```

Run tests:

```bash
pytest -q
```

Pre-commit hooks:

```bash
pre-commit install
pre-commit run --all-files
```

## 10. Publishing to PyPI

Steps for a new release (semver pre-1.0: be cautious with breaking changes):

1. Bump version in `pyproject.toml` (`[project].version`).
2. Update "Recent Changes" here and quickstarts if needed.
3. Clean previous artifacts:

```bash
rm -rf dist/ build/ *.egg-info
```

4. Install build tools:

```bash
python -m pip install --upgrade build twine
```

5. Build artifacts (wheel + sdist):

```bash
python -m build
```

6. Validate metadata:

```bash
twine check dist/*
```

7. (Optional) Upload to TestPyPI first:

```bash
twine upload --repository testpypi dist/*
# Test installation:
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps ub-grader==X.Y.Z
```

8. Upload to PyPI:

```bash
twine upload dist/*
```

9. Create and push git tag (recommended):

```bash
git tag -a vX.Y.Z -m "ub-grader X.Y.Z"
git push origin vX.Y.Z
```

10. Verify clean install:

```bash
python -m venv /tmp/ubg-test
source /tmp/ubg-test/bin/activate
pip install ub-grader==X.Y.Z
python -c "import ub_grader, sys; print('OK', ub_grader.__version__)"
```

Release checklist:

- [ ] Tests green
- [ ] Lint/format clean
- [ ] Version bumped
- [ ] README & quickstarts updated
- [ ] Git tag created

## 11. Roadmap

- Strict validation with JSON Schema
- `ub-grader` CLI
- Spec signature verification mode
- Tool to generate and sign specs (CLI)
- Additional metrics (e.g., operation count estimate)

## 12. Recent Changes

- 0.2.0: Required key in `init_students` changed from `id` to `niub` (pre-1.0 breaking change).
- 0.2.2: Added Trusted Publisher GitHub Actions workflow (TestPyPI + PyPI) and exposed `__version__` attribute.
- 0.3.0: Required key in `grader` changed from `student_id` to `students_id`, now a List of strings is required rather than a single string with student id. Updated tests. (0.2.2 breaking change)

### 10.1 Automated Publishing with PyPI Trusted Publisher (OIDC)

You can publish without storing API tokens using PyPI's Trusted Publishers + GitHub Actions OIDC:

1. Ensure the GitHub repo is public (or you have set the proper visibility) and the workflow file exists at `.github/workflows/publish.yml` (already included). The workflow now:
  - Publishes first to TestPyPI (`testpypi` job)
  - Then to PyPI (`pypi` job) after TestPyPI succeeds
  - Triggers on pushing a version tag `v*.*.*` OR on a published GitHub Release
2. Go to https://pypi.org/project/ub-grader/settings/publishing/ (if project not created yet, create a *pending* publisher first):
  - Click "Add trusted publisher" → Choose GitHub
  - Organization / Owner: `pablomartinezm`
  - Repository: `ub-grader`
  - Workflow name: `publish.yml` (must match file name)
  - Environment (optional): leave blank unless you add `environment:` in the workflow
  - Permissions: accept defaults, save
3. (If project name not yet existing) Use the *pending* publisher form with the above details, then push a tag to create + publish in one go.
4. Cut a release by tagging: `git tag -a v0.2.1 -m "ub-grader 0.2.1" && git push origin v0.2.1`.
5. The workflow builds and publishes automatically via OIDC (no secrets needed). Check Actions tab for confirmation.

Notes:
- Only tags matching `v*.*.*` or publishing a GitHub Release trigger the workflow.
- TestPyPI publish may skip existing versions (`skip-existing: true`).
- Failed upload (e.g. version reuse) will fail the job; bump version and retag.
- To test first against TestPyPI with OIDC, add a second job using `repository-url: https://test.pypi.org/legacy/` and register another trusted publisher for TestPyPI.

Minimal manual override: you can still do a local `twine upload` if needed; both methods coexist.

## 13. License

MIT
