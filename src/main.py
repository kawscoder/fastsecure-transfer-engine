import argparse
import json
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Callable, Any

# Allow running both as "python src/main.py" and from tests.
sys.path.append(str(Path(__file__).resolve().parent))

from config import DEFAULT_CHUNK_SIZE, ENCRYPTED_DIR, DECRYPTED_DIR, RECOVERED_DIR, MANIFEST_DIR
from logger_config import get_logger
from file_detector import detect_file_category, get_delivery_type
from audio_utils import get_audio_duration_seconds
from hash_utils import sha256_file
from chunker import iter_file_chunks, count_chunks
from crypto_engine import encrypt_bytes, decrypt_bytes
from manifest_manager import build_base_manifest, save_manifest, load_manifest, latest_manifest, manifest_file_name
from verifier import verify_before_decrypt, validate_recovered_hash, validate_manifest_format_consistency

logger = get_logger()
ProgressCallback = Callable[[dict[str, Any]], None]


def transfer_id() -> str:
    return "TRF-" + time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6].upper()


def choose_optimal_chunk_size(file_size_bytes: int) -> int:
    """Return a safe chunk size for demo + practical use.

    Small files still get multiple chunks for classroom visualization.
    Large files get bigger chunks to avoid creating thousands of files.
    """
    kb = 1024
    mb = 1024 * kb
    gb = 1024 * mb
    if file_size_bytes <= 128 * kb:
        return 1 * kb
    if file_size_bytes <= 5 * mb:
        return 64 * kb
    if file_size_bytes <= 50 * mb:
        return 1 * mb
    if file_size_bytes <= 500 * mb:
        return 4 * mb
    if file_size_bytes <= 2 * gb:
        return 8 * mb
    return 16 * mb


def clean_runtime_storage() -> None:
    for folder in [ENCRYPTED_DIR, DECRYPTED_DIR, RECOVERED_DIR, MANIFEST_DIR]:
        for item in folder.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def _emit(callback: ProgressCallback | None, **payload: Any) -> None:
    if callback is not None:
        callback(payload)


def encrypt_file(file_path: str | Path, chunk_size: int | None = None, progress_callback: ProgressCallback | None = None) -> Path:
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"Input file not found: {source}")
    if not source.is_file():
        raise ValueError(f"Input path is not a file: {source}")

    file_size = source.stat().st_size
    if chunk_size is None or chunk_size <= 0:
        chunk_size = choose_optimal_chunk_size(file_size)

    tid = transfer_id()
    ext = source.suffix.lower()
    file_name = source.name
    total_chunks = count_chunks(file_size, chunk_size)
    file_category = detect_file_category(source)
    delivery_type = get_delivery_type(source)
    duration = get_audio_duration_seconds(source)

    logger.info(f"Start encrypt file: {source} | transfer_id={tid}")
    _emit(progress_callback, stage="start", message=f"Nhận file đầu vào: {file_name}", percent=3)
    _emit(progress_callback, stage="detect", message=f"Nhận diện định dạng: {ext} | loại: {file_category}", percent=8)
    _emit(progress_callback, stage="plan", message=f"Tự chọn chunk size: {chunk_size} bytes | tổng chunk dự kiến: {total_chunks}", percent=12)

    original_hash = sha256_file(source)
    _emit(progress_callback, stage="hash", message="Đã tính SHA-256 của file gốc", percent=18)

    out_dir = ENCRYPTED_DIR / tid
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_base_manifest(
        transfer_id=tid,
        file_name=file_name,
        file_extension=ext,
        file_category=file_category,
        delivery_type=delivery_type,
        file_size_bytes=file_size,
        chunk_size_bytes=chunk_size,
        total_chunks=total_chunks,
        original_sha256=original_hash,
        duration_seconds=duration,
    )

    for chunk in iter_file_chunks(source, chunk_size):
        chunk_id = f"CHK-{chunk.sequence_number:06d}"
        encrypted_file = f"{chunk_id}_OF-{total_chunks:06d}_{file_name}.enc"
        aad_dict = {
            "transfer_id": tid,
            "chunk_id": chunk_id,
            "sequence_number": chunk.sequence_number,
            "offset": chunk.offset,
            "plain_size": chunk.plain_size,
            "file_name": file_name,
        }
        aad = json.dumps(aad_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ciphertext, nonce_b64 = encrypt_bytes(chunk.data, aad=aad)
        chunk_path = out_dir / encrypted_file
        chunk_path.write_bytes(ciphertext)
        encrypted_hash = sha256_file(chunk_path)

        segment_record = {
            # Required by the topic, while generalized as chunk metadata.
            "audio_id": tid,
            "segment_id": chunk_id,
            "chunk_id": chunk_id,
            "sequence_number": chunk.sequence_number,
            "offset": chunk.offset,
            "plain_size": chunk.plain_size,
            "encrypted_size": len(ciphertext),
            "duration": duration,
            "format": ext.replace(".", ""),
            "encrypted_file": encrypted_file,
            "nonce": nonce_b64,
            "encrypted_sha256": encrypted_hash,
            "aad": aad_dict,
        }
        manifest["chunks"].append(segment_record)
        logger.info(f"Encrypted chunk: {chunk_id} -> {encrypted_file}")
        progress = 18 + int((chunk.sequence_number / max(total_chunks, 1)) * 70)
        _emit(
            progress_callback,
            stage="encrypt_chunk",
            message=f"Mã hóa {chunk_id}/{total_chunks:06d}: {encrypted_file}",
            percent=min(progress, 88),
            chunk=segment_record,
        )

    manifest_path = save_manifest(manifest, manifest_file_name(tid, file_name))
    logger.info(f"Manifest created: {manifest_path}")
    _emit(progress_callback, stage="manifest", message=f"Đã tạo manifest và HMAC: {manifest_path.name}", percent=96)
    _emit(progress_callback, stage="done", message="Mã hóa hoàn tất", percent=100)
    print(f"[OK] Encrypted file: {file_name}")
    print(f"[OK] Transfer ID: {tid}")
    print(f"[OK] Manifest: {manifest_path}")
    return manifest_path


def decrypt_latest_or_path(
    manifest_path: str | Path | None = None,
    output_extension_override: str | None = None,
    progress_callback: ProgressCallback | None = None,
) -> Path:
    path = Path(manifest_path) if manifest_path else latest_manifest()
    _emit(progress_callback, stage="load_manifest", message=f"Đọc manifest: {path.name}", percent=5)
    manifest = load_manifest(path)
    _emit(progress_callback, stage="verify_manifest", message="Manifest HMAC hợp lệ", percent=12)
    validate_manifest_format_consistency(manifest, output_extension_override=output_extension_override)
    _emit(progress_callback, stage="verify_format", message="Định dạng file và format chunk hợp lệ", percent=18)
    verify_before_decrypt(manifest)
    _emit(progress_callback, stage="verify_chunks", message="Đã kiểm tra đủ chunk, đúng thứ tự và đúng SHA-256", percent=28)

    tid = manifest["transfer_id"]
    file_name = manifest["file_name"]
    encrypted_dir = ENCRYPTED_DIR / tid
    decrypted_dir = DECRYPTED_DIR / tid
    decrypted_dir.mkdir(parents=True, exist_ok=True)

    output_ext = (output_extension_override or manifest.get("file_extension") or Path(file_name).suffix).lstrip(".")
    base_name = Path(file_name).stem
    recovered_path = RECOVERED_DIR / f"RECOVERED_{tid}_{base_name}.{output_ext}"

    logger.info(f"Start decrypt transfer: {tid}")
    chunks = sorted(manifest["chunks"], key=lambda x: x["sequence_number"])
    with recovered_path.open("wb") as recovered:
        for index, chunk in enumerate(chunks, start=1):
            encrypted_path = encrypted_dir / chunk["encrypted_file"]
            ciphertext = encrypted_path.read_bytes()
            aad = json.dumps(chunk["aad"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            plain = decrypt_bytes(ciphertext, chunk["nonce"], aad=aad)

            part_path = decrypted_dir / f"{chunk['chunk_id']}_{file_name}.part"
            part_path.write_bytes(plain)
            recovered.write(plain)
            logger.info(f"Decrypted chunk: {chunk['chunk_id']}")
            progress = 28 + int((index / max(len(chunks), 1)) * 62)
            _emit(
                progress_callback,
                stage="decrypt_chunk",
                message=f"Giải mã {chunk['chunk_id']}/{manifest['total_chunks']:06d}",
                percent=min(progress, 90),
                chunk=chunk,
            )

    _emit(progress_callback, stage="hash_recovered", message="Đã ghép file, đang so sánh SHA-256", percent=95)
    if not validate_recovered_hash(manifest, recovered_path):
        logger.error("Recovered file hash does not match original file hash")
        raise ValueError("Recovered file hash does not match original file hash")

    logger.info(f"Recovered file successfully: {recovered_path}")
    _emit(progress_callback, stage="done", message="Khôi phục thành công. SHA-256 khớp file gốc", percent=100)
    print(f"[OK] Recovered file: {recovered_path}")
    print("[OK] SHA-256 matched original file")
    return recovered_path


def simulate_missing_chunk() -> None:
    manifest_path = latest_manifest()
    manifest = load_manifest(manifest_path)
    first = manifest["chunks"][0]
    target = ENCRYPTED_DIR / manifest["transfer_id"] / first["encrypted_file"]
    target.unlink()
    logger.info(f"Simulated missing chunk: {target.name}")
    print(f"[OK] Deleted chunk for test: {target.name}")
    decrypt_latest_or_path(manifest_path)


def simulate_tamper_chunk() -> None:
    manifest_path = latest_manifest()
    manifest = load_manifest(manifest_path)
    first = manifest["chunks"][0]
    target = ENCRYPTED_DIR / manifest["transfer_id"] / first["encrypted_file"]
    with target.open("r+b") as f:
        f.seek(0)
        original = f.read(1)
        f.seek(0)
        f.write(b"X" if original != b"X" else b"Y")
    logger.info(f"Simulated tampered chunk: {target.name}")
    print(f"[OK] Tampered chunk for test: {target.name}")
    decrypt_latest_or_path(manifest_path)


def simulate_wrong_order() -> None:
    manifest_path = latest_manifest()
    manifest = load_manifest(manifest_path)
    if len(manifest.get("chunks", [])) < 2:
        raise ValueError("Need at least 2 chunks to simulate wrong order. Use a larger file or smaller chunk size.")
    # Re-sign manifest so verifier can reach the sequence-order check.
    manifest["chunks"][0]["sequence_number"], manifest["chunks"][1]["sequence_number"] = manifest["chunks"][1]["sequence_number"], manifest["chunks"][0]["sequence_number"]
    save_manifest(manifest, manifest_path)
    logger.info("Simulated wrong chunk order by modifying manifest")
    print("[OK] Modified manifest order for test")
    decrypt_latest_or_path(manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="FSTE - FastSecure Transfer Engine")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encrypt", help="Encrypt and split an input file")
    enc.add_argument("file", help="Input file path, for example input_files/sample.wav")
    enc.add_argument("--chunk-size", type=int, default=None, help="Chunk size in bytes. Omit to auto-optimize.")

    dec = sub.add_parser("decrypt", help="Decrypt latest manifest or a provided manifest")
    dec.add_argument("--manifest", default=None, help="Manifest JSON path")
    dec.add_argument("--output-extension", default=None, help="Optional output extension. Must match manifest format.")

    sub.add_parser("clean", help="Clean generated storage files")
    sub.add_parser("test-missing", help="Delete one encrypted chunk then run decrypt")
    sub.add_parser("test-tamper", help="Modify one encrypted chunk then run decrypt")
    sub.add_parser("test-wrong-order", help="Modify manifest sequence order then run decrypt")
    sub.add_parser("benchmark", help="Run benchmark for files in input_files")

    args = parser.parse_args()

    try:
        if args.command == "encrypt":
            encrypt_file(args.file, chunk_size=args.chunk_size)
        elif args.command == "decrypt":
            decrypt_latest_or_path(args.manifest, output_extension_override=args.output_extension)
        elif args.command == "clean":
            clean_runtime_storage()
            print("[OK] Runtime storage cleaned")
        elif args.command == "test-missing":
            simulate_missing_chunk()
        elif args.command == "test-tamper":
            simulate_tamper_chunk()
        elif args.command == "test-wrong-order":
            simulate_wrong_order()
        elif args.command == "benchmark":
            from benchmark import run_benchmark
            run_benchmark()
    except Exception as exc:
        logger.error(str(exc))
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
