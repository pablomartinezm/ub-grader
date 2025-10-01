# ub-grader

Python library for students to self-grade assignments locally and generate encrypted reports to submit to instructors.

## Table of Contents

1. Quick Installation
2. Student Usage
3. Spec Format
4. Encrypted Reports & Signing
5. Troubleshooting
6. License

## 1. Quick Installation

```bash
pip install ub-grader
```

Requires Python 3.10+.

## 2. Student Usage

### Basic Usage

```python
from ub_grader import init_students, load_spec, grade
from solution import solve  # your target function

# Register students (single student or multiple for group work)
init_students([
  {"niub": "A123", "first_name": "Alice", "last_name": "Doe"},
])

# Load assignment specification
load_spec("https://server/assignments/p1.json")  # or file:///abs/path/p1.json

# Grade your solution
result = grade(
  solve,
  student_id="A123",
  signing_key_path=None,  # Path to Ed25519 private key if signing required
)

print("Final score:", result["final_score"], "/", result["max_score"])
```

After running, a file `report_A123_<assignment_id>.enc` will be generated. Submit this encrypted file to your instructor (do not open or modify it).

### Step-by-Step Guide

1. **Install the library**: `pip install ub-grader`
2. **Create your solution**: Write your solution function in a Python file
3. **Register**: Use `init_students()` with your student ID and name (supports single or multiple students)
4. **Load spec**: Use `load_spec()` with the assignment specification URL provided by your instructor
5. **Grade**: Use `grade()` with your solution function
6. **Submit**: Send the generated `.enc` file to your instructor

### Optional: Digital Signing

If your instructor requires signed reports:

1. Generate an Ed25519 key pair:
   ```bash
   openssl genpkey -algorithm ED25519 -out ed25519_priv.pem
   openssl pkey -in ed25519_priv.pem -pubout -out ed25519_pub.pem
   ```

2. Use the private key when grading:
   ```python
   result = grade(solve, student_id="A123", signing_key_path="ed25519_priv.pem")
   ```

3. Submit both the `.enc` report and your public key (`ed25519_pub.pem`) if requested.

### Multiple Students (Group Work)

You can register multiple students at once, which is useful for group assignments or when managing multiple student accounts:

```python
init_students([
    {"niub": "A123", "first_name": "Alice", "last_name": "Doe"},
    {"niub": "B456", "first_name": "Bob", "last_name": "Smith"},
    {"niub": "C789", "first_name": "Charlie", "last_name": "Brown"},
])

# Each student can then generate their own report
result_alice = grade(solve, student_id="A123")
result_bob = grade(solve, student_id="B456")
```

## 3. Spec Format

Assignment specifications are provided by your instructor as JSON files. A typical spec includes:

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
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
}
```

**Key points for students:**
- Tests may have `expected_hidden: true`, which means you won't see the expected output, only pass/fail
- Each test has time and memory limits
- Exceeding limits may result in penalties applied to your score
- The `public_key` is used to encrypt your report

## 4. Encrypted Reports & Signing

When you run `grade()`, an encrypted report file is generated: `report_<niub>_<assignment_id>.enc`.

**What's in the report:**
- Your test results (pass/fail, execution time, memory usage)  
- Your final score and the maximum possible score
- Assignment metadata
- Your student information
- Optional digital signature (if you provided a signing key)

**Important:**
- **Do not** open, edit, or modify the `.enc` file
- The file uses AES-256-GCM encryption with RSA key exchange
- Only your instructor can decrypt and read the contents
- File size is typically a few kilobytes

## 5. Troubleshooting

### Common Issues

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| `RuntimeError: No spec loaded` | Forgot to call `load_spec()` | Call `load_spec()` before `grade()` |
| `ValueError: Missing required field` | Malformed spec JSON | Contact your instructor for a valid spec |
| `ValueError: Integrity hash does not match` | Spec was modified | Re-download the original spec |
| Public key related error | Missing public key in spec | Ensure spec includes `public_key` or contact instructor |
| Very low score | Tests failing or penalties applied | Review your logic and check time/memory limits |

### Best Practices

- Use a dedicated virtual environment: `python -m venv myenv && source myenv/bin/activate`
- Keep your Ed25519 private key secure and never share it
- Don't modify the assignment spec file
- Test your solution thoroughly before final grading
- Keep backups of your solution code

### Getting Help

- Check that your Python version is 3.10 or higher
- Ensure you have the latest version: `pip install -U ub-grader`
- Review the error messages carefully - they usually indicate the specific issue
- Contact your instructor if you suspect issues with the assignment specification

<<<<<<< Updated upstream
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
- 0.3.1: Changed hashing methods
- 0.3.2: Added integrity to final report for professor side checking

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
=======
## 6. License
>>>>>>> Stashed changes

MIT
