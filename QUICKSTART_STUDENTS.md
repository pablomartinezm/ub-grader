# Student Quickstart

Quick guide to self-grade your assignment and produce the encrypted report to submit.

## 1. Requirements

- Python 3.10+
- Assignment spec JSON accessible via URL (http(s) or file://)

## 2. Install the library

```bash
pip install ub-grader
```

## 3. Prepare your solution function

Create (or reuse) a file `solution.py` with the function to evaluate. Minimal example:

```python
def solve(a: int, b: int) -> int:
    return a + b
```

## 4. Register with your NIUB (student id)

```python
from ub_grader import init_students

init_students([
    {"niub": "A123", "first_name": "YourName", "last_name": "YourSurname"},
])
```

## 5. Load the spec and run grading

```python
from ub_grader import load_spec, grade
from solution import solve

load_spec("file:///absolute/path/spec_assignment1.json")
# Remote example: load_spec("https://server/assignments/a1.json")

result = grade(
    solve,
    student_id="A123",
    signing_key_path=None,  # Or path to your Ed25519 private key if signing
)

print("Final score:", result["final_score"], "/", result["max_score"])
```

After execution a file will be created:

```
report_A123_<assignment_id>.enc
```

That's the file you must send. Do not open or edit it (AES-256-GCM + RSA, optionally signed).

## 6. How to confirm everything worked

- Console prints: `Grade: X / Y`
- The file `report_...enc` exists in your working directory
- File size usually a few KB

## 7. Common errors

| Issue                                  | Likely cause                       | Fix                                                   |
| -------------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| `RuntimeError: No spec loaded`         | Forgot to call `load_spec()`       | Call `load_spec()` before `grade()`                   |
| `ValueError: Missing required field`   | Malformed spec JSON                | Ensure all required fields exist                     |
| `ValueError: Integrity hash does not match` | Spec altered after hashing     | Re-download official spec                            |
| Public key related error               | Missing public key in spec         | Ensure spec includes `public_key` or pass one        |
| Very low result                        | Tests failing / penalties applied  | Review logic and time/memory limits                  |

## 8. Sign the report (optional)

If the course flow requires Ed25519 signing:

1. Generate key pair (once):
   ```bash
   openssl genpkey -algorithm ED25519 -out ed25519_priv.pem
   openssl pkey -in ed25519_priv.pem -pubout -out ed25519_pub.pem
   ```
2. Pass `signing_key_path="ed25519_priv.pem"` when calling `grade()`.
3. Submit the encrypted report and, if requested, your `ed25519_pub.pem`.

## 9. Update to a new version

```bash
pip install -U ub-grader
```

## 10. Best practices

- Use a dedicated virtual environment.
- Keep your Ed25519 private key secret.
- Do not modify the spec; you could break the integrity hash.
- Version control your solution, but usually ignore `report_*.enc`.

## 11. Quick FAQ

**Can I run multiple times?** Yes, the report is overwritten (or a new one if assignment_id changes).

**Can I see expected values?** Some tests hide them to prevent reverse engineering; you only see pass/fail.

**What does the report include?** Each test result (pass/fail, time, memory), your score and spec metadata.

---

Guide version: 1.0.0
