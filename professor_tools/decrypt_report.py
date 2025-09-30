#!/usr/bin/env python3
"""Herramienta local (no PyPI) para descifrar y verificar un reporte.

Uso:
    python professor_tools/decrypt_report.py --rsa-private rsa_priv.pem \
        [--ed25519-public ed_pub.pem] report_<id>_<assignment>.enc

Salida: JSON identado en stdout.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key


def _b64(x: str) -> bytes:
    """Decode a base64 string (wrapper for readability)."""
    return base64.b64decode(x.encode())


def decrypt_report(
    path: Path,
    rsa_priv_path: Path,
    ed25519_pub_path: Path | None,
):
    """Decrypt and optionally verify a grading report.

    Parameters
    ----------
    path: Path to the ``*.enc`` JSON container.
    rsa_priv_path: Matching RSA private key (PEM) to unwrap the AES key.
    ed25519_pub_path: Optional Ed25519 public key (PEM) to verify signature.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    # Campos requeridos
    for field in ["alg", "iv", "key", "tag", "ciphertext"]:
        if field not in data:
            raise ValueError(f"Campo faltante en contenedor: {field}")
    if data["alg"] != "RSA-OAEP+AES-256-GCM":
        raise ValueError("Algoritmo no soportado")

    # Descifrar clave simétrica
    with open(rsa_priv_path, "rb") as f:
        priv = load_pem_private_key(f.read(), password=None)
    sym_key = priv.decrypt(
        _b64(data["key"]),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    aesgcm = AESGCM(sym_key)
    iv = _b64(data["iv"])
    tag = _b64(data["tag"])
    ciphertext = _b64(data["ciphertext"])
    combined = ciphertext + tag
    plaintext = aesgcm.decrypt(iv, combined, None)

    if data.get("signature") and ed25519_pub_path:
        with open(ed25519_pub_path, "rb") as f:
            pub = load_pem_public_key(f.read())
        if not isinstance(pub, ed25519.Ed25519PublicKey):
            raise ValueError("Clave pública Ed25519 inválida")
        try:
            pub.verify(_b64(data["signature"]), plaintext)
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Firma inválida: {e}") from e
    elif data.get("signature") and not ed25519_pub_path:
        print(
            "ADVERTENCIA: firma presente pero sin clave pública",
            file=sys.stderr,
        )

    payload = json.loads(plaintext.decode("utf-8"))
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("report", type=Path)
    p.add_argument(
        "--rsa-private",
        required=True,
        type=Path,
        help="Clave privada RSA correspondiente a la pública usada",
    )
    p.add_argument(
        "--ed25519-public",
        type=Path,
        help="Clave pública Ed25519 para verificar firma (opcional)",
    )
    args = p.parse_args()

    payload = decrypt_report(
        args.report,
        args.rsa_private,
        args.ed25519_public,
    )
    json.dump(
        payload,
        sys.stdout,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    print()


if __name__ == "__main__":  # pragma: no cover
    main()
