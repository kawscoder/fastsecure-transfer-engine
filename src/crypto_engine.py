import base64
import json
import os
import hmac
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config import SECRET_KEY_FILE


def _b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("utf-8"))


def load_or_create_keys() -> dict:
    """Create AES-GCM and HMAC keys on first run. Do not commit secret.key to GitHub."""
    if SECRET_KEY_FILE.exists():
        return json.loads(SECRET_KEY_FILE.read_text(encoding="utf-8"))

    keys = {
        "aes_key": _b64e(AESGCM.generate_key(bit_length=256)),
        "hmac_key": _b64e(os.urandom(32)),
    }
    SECRET_KEY_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")
    return keys


def get_aesgcm() -> AESGCM:
    keys = load_or_create_keys()
    return AESGCM(_b64d(keys["aes_key"]))


def generate_nonce() -> bytes:
    # 96-bit nonce is recommended for AES-GCM.
    return os.urandom(12)


def encrypt_bytes(plain_data: bytes, aad: bytes | None = None) -> tuple[bytes, str]:
    aesgcm = get_aesgcm()
    nonce = generate_nonce()
    ciphertext = aesgcm.encrypt(nonce, plain_data, aad)
    return ciphertext, _b64e(nonce)


def decrypt_bytes(ciphertext: bytes, nonce_b64: str, aad: bytes | None = None) -> bytes:
    aesgcm = get_aesgcm()
    return aesgcm.decrypt(_b64d(nonce_b64), ciphertext, aad)


def manifest_hmac_hex(manifest_without_hmac: dict) -> str:
    keys = load_or_create_keys()
    key = _b64d(keys["hmac_key"])
    canonical = json.dumps(manifest_without_hmac, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(key, canonical, hashlib.sha256).hexdigest()


def verify_manifest_hmac(manifest: dict) -> bool:
    expected = manifest.get("manifest_hmac")
    if not expected:
        return False
    clone = dict(manifest)
    clone.pop("manifest_hmac", None)
    actual = manifest_hmac_hex(clone)
    return hmac.compare_digest(expected, actual)
