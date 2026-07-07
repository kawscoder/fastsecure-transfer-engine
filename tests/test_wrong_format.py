import pytest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from main import clean_runtime_storage, encrypt_file, decrypt_latest_or_path
from config import INPUT_DIR
from manifest_manager import load_manifest


def test_wrong_format_output_rejected():
    clean_runtime_storage()
    sample = INPUT_DIR / "sample.wav"
    manifest_path = encrypt_file(sample, chunk_size=1024)
    manifest = load_manifest(manifest_path)
    wrong_ext = "mp3" if manifest["format"] != "mp3" else "wav"
    with pytest.raises(ValueError, match="Output format mismatch"):
        decrypt_latest_or_path(manifest_path, output_extension_override=wrong_ext)
