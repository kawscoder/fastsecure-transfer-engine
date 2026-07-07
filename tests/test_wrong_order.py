import sys
from pathlib import Path
import json
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from main import clean_runtime_storage, encrypt_file, decrypt_latest_or_path


def test_manifest_tamper_detected_when_order_changed(tmp_path):
    clean_runtime_storage()
    sample = tmp_path / "sample.wav"
    sample.write_bytes(b"RIFF" + b"A" * 10000)
    manifest_path = encrypt_file(sample, chunk_size=1024)
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    manifest["chunks"][0]["sequence_number"], manifest["chunks"][1]["sequence_number"] = manifest["chunks"][1]["sequence_number"], manifest["chunks"][0]["sequence_number"]
    Path(manifest_path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with pytest.raises(ValueError):
        decrypt_latest_or_path(manifest_path)
