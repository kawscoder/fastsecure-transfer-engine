import json
from datetime import datetime
from pathlib import Path
from typing import Any
from config import MANIFEST_DIR, SYSTEM_NAME, ALGORITHM, HASH_ALGORITHM
from crypto_engine import manifest_hmac_hex, verify_manifest_hmac


def save_manifest(manifest: dict, output_path: str | Path) -> Path:
    clone = dict(manifest)
    clone.pop("manifest_hmac", None)
    clone["manifest_hmac"] = manifest_hmac_hex(clone)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clone, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if not verify_manifest_hmac(manifest):
        raise ValueError("Manifest integrity verification failed. Manifest may have been modified.")
    return manifest


def latest_manifest() -> Path:
    manifests = sorted(MANIFEST_DIR.glob("MANIFEST_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not manifests:
        raise FileNotFoundError("No manifest found in storage/manifests.")
    return manifests[0]


def build_base_manifest(
    transfer_id: str,
    file_name: str,
    file_extension: str,
    file_category: str,
    delivery_type: str,
    file_size_bytes: int,
    chunk_size_bytes: int,
    total_chunks: int,
    original_sha256: str,
    duration_seconds: float | None,
) -> dict:
    return {
        "system_name": SYSTEM_NAME,
        "transfer_id": transfer_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "file_name": file_name,
        "file_extension": file_extension.replace(".", ""),
        "format": file_extension.replace(".", ""),
        "file_category": file_category,
        "delivery_type": delivery_type,
        "algorithm": ALGORITHM,
        "hash_algorithm": HASH_ALGORITHM,
        "file_size_bytes": file_size_bytes,
        "chunk_size_bytes": chunk_size_bytes,
        "total_chunks": total_chunks,
        "original_sha256": original_sha256,
        "duration_seconds": duration_seconds,
        "chunks": [],
    }


def manifest_file_name(transfer_id: str, file_name: str) -> Path:
    safe_name = file_name.replace(" ", "_").replace(".", "_")
    return MANIFEST_DIR / f"MANIFEST_{transfer_id}_{safe_name}.json"
