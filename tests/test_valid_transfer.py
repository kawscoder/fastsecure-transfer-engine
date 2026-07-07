import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from main import clean_runtime_storage, encrypt_file, decrypt_latest_or_path
from hash_utils import sha256_file


def test_valid_transfer(tmp_path):
    clean_runtime_storage()
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"RIFF" + b"A" * 10000)
    manifest = encrypt_file(sample, chunk_size=1024)
    recovered = decrypt_latest_or_path(manifest)
    assert sha256_file(sample) == sha256_file(recovered)
