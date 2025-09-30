import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ub_grader import grade, init_students, load_spec


def _func(a, b):
    return a + b


def test_per_spec_public_key(tmp_path):
    # Generate RSA key pair and embed public part in spec
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    spec = {
        "version": "1.0.0",
        "assignment_id": "pkembed",
        "public_key": pub_pem,  # new field
        "tests": [
            {
                "id": "t1",
                "input": {"args": [2, 3], "kwargs": {}},
                "expected": 5,
                "weight": 1,
            }
        ],
        "scoring": {
            "mode": "weighted_sum_with_penalties",
            "rounding": 2,
            "penalties": {},
            "max_score": 10,
        },
        "integrity": {},
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")

    load_spec(spec_file.as_uri())
    init_students([{"niub": "S1"}])
    out_path = tmp_path / "r.enc"
    result = grade(
        _func,
        students_id=["S1"],
        public_key_path=None,  # should use embedded spec public_key
        signing_key_path=None,
        output_path=str(out_path),
    )
    expected_final_score = 10
    assert result["final_score"] == expected_final_score
    data = json.loads(out_path.read_text(encoding="utf-8"))
    # basic container fields
    assert {"ciphertext", "key", "iv", "tag"}.issubset(data.keys())
