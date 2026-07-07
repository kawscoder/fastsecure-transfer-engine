from pathlib import Path
from hash_utils import sha256_file
from config import ENCRYPTED_DIR


def validate_chunk_sequence(manifest: dict) -> None:
    chunks = manifest.get("chunks", [])
    expected_total = manifest.get("total_chunks")
    if len(chunks) != expected_total:
        raise ValueError(f"Manifest chunk count mismatch: expected {expected_total}, got {len(chunks)}")

    expected_sequence = list(range(1, expected_total + 1))
    actual_sequence = [chunk["sequence_number"] for chunk in chunks]
    if actual_sequence != expected_sequence:
        raise ValueError(f"Invalid chunk order. Expected {expected_sequence}, got {actual_sequence}")


def validate_manifest_format_consistency(manifest: dict, output_extension_override: str | None = None) -> None:
    """Validate file format metadata and optional output extension.

    This supports the required "wrong format" test. For a correct rebuild, the
    requested output extension must match the manifest's original format.
    """
    expected_format = str(manifest.get("format") or manifest.get("file_extension") or "").lower().lstrip(".")
    file_extension = str(manifest.get("file_extension") or "").lower().lstrip(".")
    if expected_format and file_extension and expected_format != file_extension:
        raise ValueError(f"Manifest format mismatch: format={expected_format}, file_extension={file_extension}")

    if output_extension_override:
        requested = output_extension_override.lower().lstrip(".")
        if expected_format and requested != expected_format:
            raise ValueError(f"Output format mismatch: manifest requires .{expected_format}, requested .{requested}")

    for chunk in manifest.get("chunks", []):
        chunk_format = str(chunk.get("format") or "").lower().lstrip(".")
        if expected_format and chunk_format and chunk_format != expected_format:
            raise ValueError(f"Chunk format mismatch: {chunk.get('chunk_id')} has format={chunk_format}, expected={expected_format}")


def validate_encrypted_chunks_exist_and_hash(manifest: dict) -> None:
    transfer_id = manifest["transfer_id"]
    chunk_dir = ENCRYPTED_DIR / transfer_id
    if not chunk_dir.exists():
        raise FileNotFoundError(f"Encrypted chunk folder not found: {chunk_dir}")

    for chunk in manifest["chunks"]:
        chunk_path = chunk_dir / chunk["encrypted_file"]
        if not chunk_path.exists():
            raise FileNotFoundError(f"Missing encrypted chunk: {chunk_path.name}")
        actual_hash = sha256_file(chunk_path)
        expected_hash = chunk["encrypted_sha256"]
        if actual_hash != expected_hash:
            raise ValueError(f"Encrypted chunk hash mismatch: {chunk_path.name}")


def validate_recovered_hash(manifest: dict, recovered_file: str | Path) -> bool:
    recovered_hash = sha256_file(recovered_file)
    return recovered_hash == manifest["original_sha256"]


def verify_before_decrypt(manifest: dict) -> None:
    validate_chunk_sequence(manifest)
    validate_encrypted_chunks_exist_and_hash(manifest)
