import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from config import INPUT_DIR, REPORT_DIR, DEFAULT_CHUNK_SIZE
from main import encrypt_file, decrypt_latest_or_path, clean_runtime_storage, choose_optimal_chunk_size


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def run_benchmark() -> Path:
    candidates = []
    for ext in ["*.mp3", "*.wav"]:
        candidates.extend(INPUT_DIR.glob(ext))

    report_lines = [
        "# Benchmark Report",
        "",
        "| File | Format | Size | Chunk size | Encrypt time | Decrypt time | Result |",
        "|---|---|---:|---:|---:|---:|---|",
    ]

    if not candidates:
        report_lines.append("| No .mp3/.wav input files found | - | - | - | - | - | Put sample files into input_files/ |")
    else:
        for file_path in candidates:
            clean_runtime_storage()
            size = file_path.stat().st_size
            t0 = time.perf_counter()
            auto_chunk = choose_optimal_chunk_size(size)
            manifest_path = encrypt_file(file_path, chunk_size=auto_chunk)
            t1 = time.perf_counter()
            decrypt_latest_or_path(manifest_path)
            t2 = time.perf_counter()
            report_lines.append(
                f"| {file_path.name} | {file_path.suffix.lower().replace('.', '')} | {format_bytes(size)} | {format_bytes(auto_chunk)} | {t1 - t0:.4f}s | {t2 - t1:.4f}s | Success |"
            )

    report_path = REPORT_DIR / "benchmark_report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"[OK] Benchmark report written to: {report_path}")
    return report_path


if __name__ == "__main__":
    run_benchmark()
