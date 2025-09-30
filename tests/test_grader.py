import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa

from ub_grader import grade, init_students, load_spec


def simple_add(a, b):
    return a + b


def test_grade_basic(tmp_path):
    # Spec local mediante file:// URL
    spec = {
        "version": "1.0.0",
        "assignment_id": "padd",
        "tests": [
            {
                "id": "t1",
                "input": {"args": [1, 2], "kwargs": {}},
                "expected": 3,
                "weight": 1,
            },
            {
                "id": "t2",
                "input": {"args": [2, 5], "kwargs": {}},
                "expected": 7,
                "weight": 1,
            },
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

    init_students([{"niub": "S1", "nombre": "Stu", "apellidos": "Dent"}])

    # Crear claves temporales (RSA pública y Ed25519 privada)

    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub = rsa_priv.public_key()
    rsa_pub_pem = rsa_pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    rsa_pub_path = tmp_path / "rsa_pub.pem"
    rsa_pub_path.write_bytes(rsa_pub_pem)

    ed_priv = ed25519.Ed25519PrivateKey.generate()
    ed_priv_pem = ed_priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    ed_priv_path = tmp_path / "ed_priv.pem"
    ed_priv_path.write_bytes(ed_priv_pem)

    out_path = tmp_path / "report.enc"
    result = grade(
        simple_add,
        students_id=["S1"],
        public_key_path=str(rsa_pub_path),
        signing_key_path=str(ed_priv_path),
        output_path=str(out_path),
    )

    # Esperado 10: todos los tests pesan 1 y max_score=10
    assert result["final_score"] == 10  # noqa: PLR2004
    assert out_path.exists()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "ciphertext" in data
    assert data.get("alg") == "RSA-OAEP+AES-256-GCM"
