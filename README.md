# ub-grader

Python library for students to self-grade assignments locally and generate reports to submit to instructors.

## Table of Contents

1. Quick Installation
2. Student Usage
3. Spec Format
4. Troubleshooting
5. License

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
)

print("Final score:", result["final_score"], "/", result["max_score"])
```

After running, a report file will be generated. Submit this file to your instructor.

### Step-by-Step Guide

1. **Install the library**: `pip install ub-grader`
2. **Create your solution**: Write your solution function in a Python file
3. **Register**: Use `init_students()` with your student ID and name (supports single or multiple students)
4. **Load spec**: Use `load_spec()` with the assignment specification URL provided by your instructor
5. **Grade**: Use `grade()` with your solution function
6. **Submit**: Send the generated report file to your instructor



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
  }
}
```

**Key points for students:**
- Tests may have `expected_hidden: true`, which means you won't see the expected output, only pass/fail
- Each test has time and memory limits
- Exceeding limits may result in penalties applied to your score

## 4. Troubleshooting

### Common Issues

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| `RuntimeError: No spec loaded` | Forgot to call `load_spec()` | Call `load_spec()` before `grade()` |
| `ValueError: Missing required field` | Malformed spec JSON | Contact your instructor for a valid spec |
| Very low score | Tests failing or penalties applied | Review your logic and check time/memory limits |

### Best Practices

- Use a dedicated virtual environment: `python -m venv myenv && source myenv/bin/activate`
- Don't modify the assignment spec file
- Test your solution thoroughly before final grading
- Keep backups of your solution code

### Getting Help

- Check that your Python version is 3.10 or higher
- Ensure you have the latest version: `pip install -U ub-grader`
- Review the error messages carefully - they usually indicate the specific issue
- Contact your instructor if you suspect issues with the assignment specification

## 5. License

MIT
