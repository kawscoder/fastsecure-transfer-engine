import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from main import clean_runtime_storage, encrypt_file, decrypt_latest_or_path
from manifest_manager import load_manifest
from config import ENCRYPTED_DIR


def test_tampered_chunk_detected(tmp_path):
    clean_runtime_storage()
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"RIFF" + b"A" * 10000)
    manifest_path = encrypt_file(sample, chunk_size=1024)
    manifest = load_manifest(manifest_path)
    first = manifest["chunks"][0]
    target = ENCRYPTED_DIR / manifest["transfer_id"] / first["encrypted_file"]
    with target.open("r+b") as f:
        f.seek(0)
        f.write(b"Z")
    with pytest.raises(ValueError):
        decrypt_latest_or_path(manifest_path)
