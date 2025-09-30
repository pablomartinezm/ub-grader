"""Low‑level cryptographic helper utilities.

Currently only provides :func:`encrypt_and_sign` which performs a hybrid
encryption (AES‑256‑GCM for the payload + RSA‑OAEP wrapping of the symmetric
key) and optional Ed25519 signing of the canonical JSON payload.

The resulting dictionary is JSON serialisable and intentionally simple so it
can be later decrypted with the companion ``professor_tools/decrypt_report``
script.
"""

from __future__ import annotations

import base64
import json
import os
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key


def encrypt_and_sign(
    payload: dict,
    rsa_public_key_path: str | None = None,
    rsa_public_key_pem: str | None = None,
    ed25519_signing_key_path: str | None = None,
) -> dict:
    """Encrypt a JSON‑serialisable payload and optionally sign it.

    The function performs the following steps:

    1. Serialises the payload as canonical JSON (sorted keys, no whitespace).
    2. Generates a fresh 256‑bit AES key and encrypts the bytes with AES‑GCM.
    3. Encrypts (wraps) the symmetric key with the provided RSA public key
       using OAEP + SHA‑256.
    4. Optionally signs the canonical JSON with an Ed25519 private key.

    Parameters
    ----------
    payload:
        Dictionary to be serialised (must be JSON serialisable).
    rsa_public_key_path / rsa_public_key_pem:
        One of these must supply the RSA public key (PEM). ``*_pem`` takes
        precedence if both are provided.
    ed25519_signing_key_path:
        Optional path to an Ed25519 private key in PEM format; when supplied
        a detached base64 signature is added under ``signature``.

    Returns
    -------
    dict
        Container with algorithm identifiers, base64 encoded components and
        optional signature ready to be JSON dumped.
    """
    # Serialize canonical JSON
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()

    # AES-GCM
    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    iv = os.urandom(12)
    ct = aesgcm.encrypt(iv, canonical, None)  # ciphertext + tag implicit
    ciphertext, tag = ct[:-16], ct[-16:]

    # Load RSA public key (path or direct PEM content)
    if rsa_public_key_pem:
        pub = load_pem_public_key(rsa_public_key_pem.encode())
    elif rsa_public_key_path:
        with open(rsa_public_key_path, "rb") as f:
            pub = load_pem_public_key(f.read())
    else:
        raise ValueError("Either rsa_public_key_path or rsa_public_key_pem must be provided")
    if not isinstance(pub, rsa.RSAPublicKey):
        raise ValueError("Clave pública RSA inválida")
    enc_key = pub.encrypt(
        key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    signature_b64 = None
    if ed25519_signing_key_path:
        with open(ed25519_signing_key_path, "rb") as f:
            priv = load_pem_private_key(f.read(), password=None)
        if not isinstance(priv, ed25519.Ed25519PrivateKey):
            raise ValueError("Signing key is not Ed25519")
        signature = priv.sign(canonical)
        signature_b64 = base64.b64encode(signature).decode()

    return {
        "alg": "RSA-OAEP+AES-256-GCM",
        "sig_alg": "Ed25519" if signature_b64 else None,
        "iv": base64.b64encode(iv).decode(),
        "key": base64.b64encode(enc_key).decode(),
        "tag": base64.b64encode(tag).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "signature": signature_b64,
        "ts": int(time.time()),
    }
