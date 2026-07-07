"""Streamlit GUI for FSTE - FastSecure Transfer Engine.

Run:
    streamlit run app.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmark import run_benchmark  # noqa: E402
from config import (  # noqa: E402
    DEFAULT_CHUNK_SIZE,
    ENCRYPTED_DIR,
    INPUT_DIR,
    LOG_FILE,
    MANIFEST_DIR,
    RECOVERED_DIR,
    REPORT_DIR,
)
from main import decrypt_latest_or_path, encrypt_file, choose_optimal_chunk_size  # noqa: E402
from manifest_manager import load_manifest, save_manifest  # noqa: E402


AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".wmv"}


FIELD_EXPLANATIONS = [
    {"Trường": "system_name", "Ý nghĩa": "Tên hệ thống sinh manifest."},
    {"Trường": "transfer_id", "Ý nghĩa": "Mã phiên xử lý. Mỗi lần mã hóa tạo một transfer_id riêng."},
    {"Trường": "created_at", "Ý nghĩa": "Thời điểm tạo manifest."},
    {"Trường": "file_name", "Ý nghĩa": "Tên file âm thanh gốc."},
    {"Trường": "file_extension / format", "Ý nghĩa": "Định dạng gốc của file, ví dụ wav hoặc mp3."},
    {"Trường": "file_category", "Ý nghĩa": "Nhóm file. Bản demo chính là media."},
    {"Trường": "delivery_type", "Ý nghĩa": "Kiểu phân phối file; type_1_media dùng cho audio/video."},
    {"Trường": "algorithm", "Ý nghĩa": "Thuật toán mã hóa từng chunk. Sản phẩm dùng AES-GCM."},
    {"Trường": "hash_algorithm", "Ý nghĩa": "Thuật toán băm kiểm tra toàn vẹn. Sản phẩm dùng SHA-256."},
    {"Trường": "file_size_bytes", "Ý nghĩa": "Kích thước file gốc theo byte."},
    {"Trường": "chunk_size_bytes", "Ý nghĩa": "Kích thước mỗi chunk. Hệ thống tự chọn để tránh quá nhiều chunk khi file lớn."},
    {"Trường": "total_chunks", "Ý nghĩa": "Tổng số chunk sau khi chia file."},
    {"Trường": "original_sha256", "Ý nghĩa": "Dấu vân tay SHA-256 của file gốc, dùng so sánh sau khi khôi phục."},
    {"Trường": "duration_seconds", "Ý nghĩa": "Thời lượng âm thanh nếu hệ thống đọc được, thường rõ nhất với WAV."},
    {"Trường": "chunks", "Ý nghĩa": "Danh sách metadata của từng chunk."},
    {"Trường": "chunk_id / segment_id", "Ý nghĩa": "Mã định danh chunk/đoạn, ví dụ CHK-000001."},
    {"Trường": "sequence_number", "Ý nghĩa": "Thứ tự chunk khi ghép lại. Nếu sai, hệ thống báo đảo thứ tự."},
    {"Trường": "offset", "Ý nghĩa": "Vị trí byte bắt đầu của chunk trong file gốc."},
    {"Trường": "plain_size", "Ý nghĩa": "Kích thước chunk trước mã hóa."},
    {"Trường": "encrypted_size", "Ý nghĩa": "Kích thước chunk sau mã hóa. AES-GCM thường lớn hơn 16 byte do tag xác thực."},
    {"Trường": "nonce", "Ý nghĩa": "Giá trị ngẫu nhiên riêng cho từng chunk khi mã hóa AES-GCM."},
    {"Trường": "encrypted_sha256", "Ý nghĩa": "SHA-256 của chunk đã mã hóa; dùng phát hiện chunk bị sửa."},
    {"Trường": "aad", "Ý nghĩa": "Metadata được AES-GCM xác thực cùng ciphertext."},
    {"Trường": "manifest_hmac", "Ý nghĩa": "Chữ ký HMAC bảo vệ manifest. Nếu manifest bị sửa, hệ thống chặn giải mã."},
]


def list_files(folder: Path, patterns: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(folder.glob(pattern))
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def list_input_media() -> list[Path]:
    return list_files(INPUT_DIR, ["*.mp3", "*.wav", "*.ogg", "*.flac", "*.aac", "*.m4a", "*.mp4", "*.webm"])


def list_manifests() -> list[Path]:
    return list_files(MANIFEST_DIR, ["MANIFEST_*.json"])


def list_recovered_media() -> list[Path]:
    return list_files(RECOVERED_DIR, ["RECOVERED_*.*"])


def display_media(path: Path, label: str) -> None:
    st.caption(label)
    suffix = path.suffix.lower()
    if suffix in AUDIO_EXTENSIONS:
        st.audio(str(path))
    elif suffix in VIDEO_EXTENSIONS:
        st.video(str(path))
    else:
        st.info(f"File {path.name} không phải audio/video phát trực tiếp trong giao diện.")


def read_text_safe(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-limit:]


def format_bytes(size: int | float | None) -> str:
    if size is None:
        return "-"
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


def manifest_to_chunk_rows(manifest: dict, max_rows: int | None = None) -> list[dict[str, Any]]:
    rows = []
    for chunk in manifest.get("chunks", []):
        rows.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "sequence": chunk.get("sequence_number"),
                "offset": chunk.get("offset"),
                "plain_size": chunk.get("plain_size"),
                "encrypted_size": chunk.get("encrypted_size"),
                "format": chunk.get("format"),
                "encrypted_file": chunk.get("encrypted_file"),
                "sha256_short": str(chunk.get("encrypted_sha256", ""))[:16] + "...",
                "nonce": chunk.get("nonce"),
            }
        )
    return rows[:max_rows] if max_rows else rows


def render_manifest_stats(manifest: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transfer ID", manifest.get("transfer_id", "-"))
    col2.metric("File", manifest.get("file_name", "-"))
    col3.metric("Tổng chunk", manifest.get("total_chunks", "-"))
    col4.metric("Thuật toán", manifest.get("algorithm", "-"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("File size", format_bytes(manifest.get("file_size_bytes")))
    c2.metric("Chunk size", format_bytes(manifest.get("chunk_size_bytes")))
    c3.metric("Format", manifest.get("format", "-"))
    c4.metric("Hash", manifest.get("hash_algorithm", "-"))


def render_chunk_table(manifest: dict, title: str = "Danh sách chunk") -> None:
    st.markdown(f"### {title}")
    rows = manifest_to_chunk_rows(manifest)
    if not rows:
        st.warning("Manifest chưa có chunk.")
        return
    st.caption("Bảng này cuộn được; dùng để giảng viên thấy file đã được chia thành các đoạn cụ thể.")
    st.dataframe(rows, use_container_width=True, height=360)


def render_process_events(events: list[str], title: str = "Các bước xử lý") -> None:
    st.markdown(f"### {title}")
    if not events:
        st.info("Chưa có sự kiện xử lý.")
        return
    st.code("\n".join(f"{i + 1:02d}. {event}" for i, event in enumerate(events[-80:])), language="text")


def make_progress_callback(progress_bar, status_box, events_box, events: list[str]):
    def callback(payload: dict[str, Any]) -> None:
        message = str(payload.get("message", ""))
        percent = int(payload.get("percent", 0))
        if message:
            events.append(message)
        progress_bar.progress(max(0, min(percent, 100)))
        status_box.info(message or "Đang xử lý...")
        events_box.code("\n".join(events[-25:]), language="text")
    return callback


def load_manifest_unverified(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_manual_security_test(test_type: str, input_file: Path, chunk_number: int = 1, wrong_extension: str = "mp3") -> dict[str, Any]:
    """Create a fresh transfer, apply one controlled fault, then try decrypting."""
    manifest_path = encrypt_file(input_file, chunk_size=None)
    manifest = load_manifest(manifest_path)
    chunks = manifest.get("chunks", [])
    if not chunks:
        raise ValueError("Manifest không có chunk để test.")
    index = max(0, min(chunk_number - 1, len(chunks) - 1))
    selected_chunk = chunks[index]
    chunk_path = ENCRYPTED_DIR / manifest["transfer_id"] / selected_chunk["encrypted_file"]

    action = ""
    expected = ""
    actual = ""
    passed = False

    try:
        if test_type == "missing":
            action = f"Xóa chunk số {selected_chunk['sequence_number']}: {selected_chunk['encrypted_file']}"
            expected = f"Hệ thống phải báo thiếu đúng chunk: {selected_chunk['encrypted_file']}"
            chunk_path.unlink()
            decrypt_latest_or_path(manifest_path)
        elif test_type == "tamper":
            action = f"Sửa 1 byte trong chunk số {selected_chunk['sequence_number']}: {selected_chunk['encrypted_file']}"
            expected = f"Hệ thống phải báo hash chunk không khớp: {selected_chunk['encrypted_file']}"
            with chunk_path.open("r+b") as f:
                f.seek(0)
                original = f.read(1)
                f.seek(0)
                f.write(b"Z" if original != b"Z" else b"Y")
            decrypt_latest_or_path(manifest_path)
        elif test_type == "wrong_order":
            if len(chunks) < 2:
                raise ValueError("Cần ít nhất 2 chunk để test đảo thứ tự.")
            action = "Đảo sequence_number của CHK-000001 và CHK-000002 trong manifest, sau đó ký lại HMAC để kiểm tra sâu thứ tự."
            expected = "Hệ thống phải báo Invalid chunk order và hiển thị expected/actual sequence."
            manifest["chunks"][0]["sequence_number"], manifest["chunks"][1]["sequence_number"] = manifest["chunks"][1]["sequence_number"], manifest["chunks"][0]["sequence_number"]
            save_manifest(manifest, manifest_path)
            decrypt_latest_or_path(manifest_path)
        elif test_type == "wrong_format":
            real_ext = manifest.get("format", "").lower()
            requested = wrong_extension.lower().lstrip(".")
            if requested == real_ext:
                requested = "mp3" if real_ext != "mp3" else "wav"
            action = f"Yêu cầu ghép/xuất file với định dạng .{requested} trong khi manifest yêu cầu .{real_ext}."
            expected = f"Hệ thống phải báo Output format mismatch: manifest requires .{real_ext}, requested .{requested}."
            decrypt_latest_or_path(manifest_path, output_extension_override=requested)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
        actual = "Không có lỗi. Test này đáng lẽ phải bị chặn."
        passed = False
    except Exception as exc:
        actual = str(exc)
        if test_type == "missing":
            passed = "Missing encrypted chunk" in actual and selected_chunk["encrypted_file"] in actual
        elif test_type == "tamper":
            passed = "Encrypted chunk hash mismatch" in actual and selected_chunk["encrypted_file"] in actual
        elif test_type == "wrong_order":
            passed = "Invalid chunk order" in actual
        elif test_type == "wrong_format":
            passed = "Output format mismatch" in actual

    return {
        "test_type": test_type,
        "transfer_id": manifest.get("transfer_id"),
        "manifest_path": str(manifest_path),
        "selected_chunk": selected_chunk,
        "action": action,
        "expected": expected,
        "actual": actual,
        "passed": passed,
    }


def render_test_result(result: dict[str, Any]) -> None:
    st.markdown("### Kết quả test thủ công")
    c1, c2, c3 = st.columns(3)
    c1.metric("Transfer ID", result.get("transfer_id", "-"))
    c2.metric("Chunk test", result.get("selected_chunk", {}).get("chunk_id", "-"))
    c3.metric("Kết luận", "ĐẠT" if result.get("passed") else "CHƯA ĐẠT")
    st.markdown("**Đầu vào/thao tác cố ý gây lỗi:**")
    st.code(result.get("action", "-"), language="text")
    st.markdown("**Kỳ vọng:**")
    st.code(result.get("expected", "-"), language="text")
    st.markdown("**Thực tế hệ thống trả về:**")
    if result.get("passed"):
        st.success(result.get("actual", "-"))
    else:
        st.error(result.get("actual", "-"))


st.set_page_config(
    page_title="FSTE - FastSecure Transfer Engine",
    page_icon="🔐",
    layout="wide",
)

st.title("🔐 FSTE - FastSecure Transfer Engine")
st.caption("Secure Audio Segment Transfer | Giao diện demo: nghe file, mã hóa từng chunk, xem manifest, test lỗi bảo mật và khôi phục file.")

with st.sidebar:
    st.header("Điều khiển nhanh")
    st.write("**Thư mục dự án:**")
    st.code(str(PROJECT_ROOT), language="text")
    st.info("Chunk size được hệ thống tự tính theo kích thước file để tránh quá tải khi file lớn.")
    st.divider()
    st.write("**Yêu cầu đề tài:**")
    st.markdown(
        """
- Source code
- File âm thanh mẫu
- Manifest mẫu/tự sinh
- Benchmark report
- Video demo
- Test: mất đoạn, sửa đoạn, đảo thứ tự, sai định dạng
        """
    )


tab_overview, tab_encrypt, tab_decrypt, tab_manifest, tab_tests, tab_logs = st.tabs(
    ["Tổng quan", "1. Mã hóa từng bước", "2. Giải mã & ghép", "Manifest & chunk", "Test bảo mật", "Log"]
)

with tab_overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Input media", len(list_input_media()))
    col2.metric("Manifest", len(list_manifests()))
    col3.metric("Recovered files", len(list_recovered_media()))
    col4.metric("Default chunk", format_bytes(DEFAULT_CHUNK_SIZE))

    st.subheader("Sản phẩm làm gì?")
    st.markdown(
        """
FSTE nhận file âm thanh `.mp3` hoặc `.wav`, đọc file dưới dạng byte, tự chọn chunk size tối ưu, chia thành nhiều chunk, mã hóa từng chunk bằng **AES-GCM**, rồi tạo **manifest JSON** chứa metadata, nonce, hash từng chunk và hash toàn file.

Khi giải mã, hệ thống đọc manifest, kiểm tra HMAC, kiểm tra thiếu chunk, kiểm tra hash chunk, kiểm tra thứ tự, kiểm tra định dạng, giải mã từng chunk và ghép lại file âm thanh. Cuối cùng hệ thống so sánh SHA-256 của file khôi phục với file gốc để chứng minh dữ liệu không bị thay đổi.
        """
    )

    st.subheader("File âm thanh mẫu")
    media_files = list_input_media()
    if not media_files:
        st.warning("Chưa có file audio/video trong input_files.")
    else:
        selected = st.selectbox("Chọn file mẫu để nghe", media_files, format_func=lambda p: f"{p.name} ({format_bytes(p.stat().st_size)})")
        display_media(selected, "Nghe/xem file gốc trong input_files")

with tab_encrypt:
    st.subheader("1. Mã hóa và chia file thành chunk")
    media_files = list_input_media()
    uploaded_file = st.file_uploader("Upload thêm file âm thanh/video để demo", type=["mp3", "wav", "ogg", "flac", "aac", "m4a", "mp4", "webm"])
    if uploaded_file is not None:
        target = INPUT_DIR / uploaded_file.name
        target.write_bytes(uploaded_file.getbuffer())
        st.success(f"Đã lưu file vào input_files/{uploaded_file.name}")
        media_files = list_input_media()

    if not media_files:
        st.warning("Chưa có file trong input_files.")
    else:
        selected = st.selectbox("Chọn file cần mã hóa", media_files, format_func=lambda p: f"{p.name} ({format_bytes(p.stat().st_size)})", key="encrypt_select")
        auto_chunk = choose_optimal_chunk_size(selected.stat().st_size)
        total_estimated = (selected.stat().st_size + auto_chunk - 1) // auto_chunk if selected.stat().st_size else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("File size", format_bytes(selected.stat().st_size))
        c2.metric("Chunk size tự động", format_bytes(auto_chunk))
        c3.metric("Số chunk dự kiến", total_estimated)
        st.caption("Giao diện không cho nhập chunk size thủ công để tránh chọn quá nhỏ làm file lớn bị quá tải hoặc sinh hàng nghìn chunk.")
        display_media(selected, "File gốc trước khi mã hóa")

        st.markdown("### Quy trình mã hóa sẽ chạy")
        st.markdown(
            """
1. Nhận file đầu vào và nhận diện định dạng.  
2. Tự tính chunk size tối ưu.  
3. Tính SHA-256 file gốc.  
4. Chia file thành chunk theo byte.  
5. Mã hóa từng chunk bằng AES-GCM, tạo nonce riêng.  
6. Tính SHA-256 từng encrypted chunk.  
7. Tạo manifest JSON và ký HMAC.  
            """
        )

        if st.button("🔐 Mã hóa file", type="primary", use_container_width=True):
            events: list[str] = []
            progress_bar = st.progress(0)
            status_box = st.empty()
            events_box = st.empty()
            callback = make_progress_callback(progress_bar, status_box, events_box, events)
            with st.spinner("Đang chia file và mã hóa từng chunk..."):
                manifest_path = encrypt_file(selected, chunk_size=None, progress_callback=callback)
            manifest = load_manifest(manifest_path)
            st.success("Mã hóa thành công.")
            st.write("Manifest:")
            st.code(str(manifest_path), language="text")
            render_process_events(events, "Quá trình mã hóa đã thực hiện")
            render_manifest_stats(manifest)
            render_chunk_table(manifest, "Danh sách chunk đã mã hóa")
            with st.expander("Xem JSON manifest đầy đủ", expanded=False):
                st.json(manifest, expanded=False)

with tab_decrypt:
    st.subheader("2. Giải mã, ghép file và nghe file khôi phục")
    manifests = list_manifests()
    if not manifests:
        st.warning("Chưa có manifest. Hãy mã hóa một file trước.")
    else:
        selected_manifest = st.selectbox("Chọn manifest", manifests, format_func=lambda p: p.name)
        try:
            manifest_preview = load_manifest(selected_manifest)
            render_manifest_stats(manifest_preview)
            render_chunk_table(manifest_preview, "Danh sách chunk sẽ được kiểm tra và giải mã")
        except Exception as exc:
            st.error(f"Không đọc được manifest: {exc}")
            manifest_preview = None

        st.markdown("### Quy trình giải mã sẽ chạy")
        st.markdown(
            """
1. Đọc manifest và kiểm tra HMAC.  
2. Kiểm tra định dạng file/chunk.  
3. Kiểm tra đủ chunk, đúng thứ tự, đúng SHA-256 từng chunk.  
4. Giải mã từng chunk bằng AES-GCM.  
5. Ghi từng phần vào file khôi phục.  
6. So sánh SHA-256 file khôi phục với file gốc.  
            """
        )

        if st.button("🔓 Giải mã và khôi phục", type="primary", use_container_width=True):
            events: list[str] = []
            progress_bar = st.progress(0)
            status_box = st.empty()
            events_box = st.empty()
            callback = make_progress_callback(progress_bar, status_box, events_box, events)
            try:
                with st.spinner("Đang kiểm tra manifest, giải mã chunk và ghép file..."):
                    recovered_path = decrypt_latest_or_path(selected_manifest, progress_callback=callback)
                st.success("Giải mã và khôi phục thành công. SHA-256 đã khớp file gốc.")
                st.code(str(recovered_path), language="text")
                render_process_events(events, "Quá trình giải mã đã thực hiện")
                display_media(recovered_path, "Nghe/xem file sau khi khôi phục")
            except Exception as exc:
                st.error(str(exc))

        recovered_files = list_recovered_media()
        if recovered_files:
            st.divider()
            selected_recovered = st.selectbox("File khôi phục đã có", recovered_files, format_func=lambda p: f"{p.name} ({format_bytes(p.stat().st_size)})")
            display_media(selected_recovered, "Phát lại file khôi phục")

with tab_manifest:
    st.subheader("Manifest JSON, thống kê và giải thích trường")
    manifests = list_manifests()
    if not manifests:
        st.warning("Chưa có manifest được tạo.")
    else:
        selected_manifest = st.selectbox("Chọn manifest để xem", manifests, format_func=lambda p: p.name, key="manifest_select")
        try:
            manifest = load_manifest(selected_manifest)
            render_manifest_stats(manifest)
            st.markdown("### Giải thích từng trường quan trọng")
            st.dataframe(FIELD_EXPLANATIONS, use_container_width=True, height=420)
            render_chunk_table(manifest, "Danh sách chunk trong manifest")

            chunks = manifest.get("chunks", [])
            if chunks:
                st.markdown("### Xem chi tiết một chunk")
                selected_chunk = st.selectbox("Chọn chunk", chunks, format_func=lambda c: f"{c.get('chunk_id')} | sequence={c.get('sequence_number')} | {c.get('encrypted_file')}")
                st.json(selected_chunk, expanded=True)

            st.markdown("### JSON manifest đầy đủ")
            manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False)
            st.text_area("Manifest full JSON", manifest_text, height=520)
            st.download_button("Tải manifest JSON", data=manifest_text, file_name=selected_manifest.name, mime="application/json")
        except Exception as exc:
            st.error(f"Manifest không hợp lệ hoặc không khớp HMAC: {exc}")
            st.markdown("Nội dung raw để kiểm tra:")
            st.text_area("Raw manifest", selected_manifest.read_text(encoding="utf-8", errors="replace"), height=420)

with tab_tests:
    st.subheader("Test bảo mật có thao tác thủ công và kết quả rõ ràng")
    st.info("Mỗi test sẽ tự tạo một transfer mới từ file đầu vào, sau đó cố ý gây lỗi rồi chạy giải mã. Vì vậy test này không phụ thuộc vào manifest đang có và không cần người dùng dọn dữ liệu.")
    media_files = list_input_media()
    if not media_files:
        st.warning("Chưa có file để test.")
    else:
        selected_input = st.selectbox("Chọn file đầu vào để tạo gói test", media_files, format_func=lambda p: f"{p.name} ({format_bytes(p.stat().st_size)})", key="security_input")
        auto_chunk = choose_optimal_chunk_size(selected_input.stat().st_size)
        estimated = (selected_input.stat().st_size + auto_chunk - 1) // auto_chunk if selected_input.stat().st_size else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("File test", selected_input.name)
        c2.metric("Chunk size tự động", format_bytes(auto_chunk))
        c3.metric("Số chunk dự kiến", estimated)
        chunk_number = st.number_input("Chọn số thứ tự chunk để test mất/sửa", min_value=1, max_value=max(1, estimated), value=1, step=1)
        wrong_ext = st.selectbox("Định dạng sai để test ghép sai định dạng", ["mp3", "wav", "mp4", "pdf", "docx"], index=0)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🧩 Test làm mất một đoạn", use_container_width=True):
                result = run_manual_security_test("missing", selected_input, chunk_number=int(chunk_number))
                render_test_result(result)
            if st.button("✏️ Test sửa một đoạn", use_container_width=True):
                result = run_manual_security_test("tamper", selected_input, chunk_number=int(chunk_number))
                render_test_result(result)
        with col_b:
            if st.button("🔀 Test đảo thứ tự đoạn", use_container_width=True):
                result = run_manual_security_test("wrong_order", selected_input, chunk_number=int(chunk_number))
                render_test_result(result)
            if st.button("📄 Test ghép sai định dạng", use_container_width=True):
                result = run_manual_security_test("wrong_format", selected_input, chunk_number=int(chunk_number), wrong_extension=wrong_ext)
                render_test_result(result)

    st.divider()
    st.subheader("Benchmark và pytest tự động")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 Chạy benchmark .mp3/.wav", use_container_width=True):
            with st.spinner("Đang chạy benchmark..."):
                report_path = run_benchmark()
            st.success(f"Đã tạo benchmark report: {report_path}")
        benchmark_report = REPORT_DIR / "benchmark_report.md"
        st.markdown("### Benchmark report")
        st.markdown(read_text_safe(benchmark_report) or "Chưa có benchmark report.")

    with c2:
        if st.button("✅ Chạy pytest -vv", use_container_width=True):
            with st.spinner("Đang chạy pytest..."):
                result = subprocess.run([sys.executable, "-m", "pytest", "-vv"], cwd=PROJECT_ROOT, capture_output=True, text=True)
            if result.returncode == 0:
                st.success("Pytest passed.")
            else:
                st.error("Pytest failed.")
            st.code(result.stdout + "\n" + result.stderr, language="text")
        test_report = REPORT_DIR / "test_report.md"
        st.markdown("### Test report")
        st.markdown(read_text_safe(test_report) or "Chưa có test report.")

with tab_logs:
    st.subheader("Log hệ thống")
    st.code(read_text_safe(LOG_FILE, limit=40000) or "Chưa có log.", language="text")
