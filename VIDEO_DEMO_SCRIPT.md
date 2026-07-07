# Kịch bản quay video demo FSTE

## 1. Mở giao diện

```powershell
cd fastsecure-transfer-engine
.\venv\Scripts\activate
streamlit run app.py
```

Giới thiệu: FSTE là hệ thống truyền file âm thanh phân đoạn an toàn. Hệ thống chia file thành chunk, mã hóa AES-GCM, tạo manifest JSON, kiểm tra toàn vẹn và khôi phục file.

## 2. Tab Tổng quan

- Cho giảng viên thấy số file input, manifest, recovered files.
- Chọn `sample.mp3` hoặc `sample.wav` và bấm nghe file gốc.

## 3. Tab Mã hóa từng bước

- Chọn file âm thanh.
- Chỉ ra hệ thống tự tính `chunk size` và số chunk dự kiến.
- Bấm **Mã hóa file**.
- Quay phần progress: nhận file, nhận diện định dạng, tính SHA-256, mã hóa từng chunk, tạo manifest.
- Hiển thị danh sách chunk đã mã hóa dạng bảng cuộn.

## 4. Tab Manifest & chunk

- Chọn manifest mới tạo.
- Giải thích các trường quan trọng: `transfer_id`, `algorithm`, `total_chunks`, `original_sha256`, `nonce`, `encrypted_sha256`, `manifest_hmac`.
- Mở chi tiết một chunk.
- Kéo xuống phần JSON manifest đầy đủ.

## 5. Tab Giải mã & ghép

- Chọn manifest.
- Cho thấy danh sách chunk sẽ được kiểm tra.
- Bấm **Giải mã và khôi phục**.
- Quay quá trình: kiểm tra HMAC, kiểm tra chunk, giải mã từng chunk, ghép file, so sánh SHA-256.
- Nghe file khôi phục sau khi giải mã.

## 6. Tab Test bảo mật

Chạy lần lượt các test thủ công:

### Test làm mất một đoạn
- Chọn chunk số 1.
- Bấm **Test làm mất một đoạn**.
- Nói rõ: đầu vào là xóa chunk cụ thể; kỳ vọng là hệ thống báo thiếu đúng chunk; kết quả thực tế hiển thị tên chunk bị thiếu.

### Test sửa một đoạn
- Bấm **Test sửa một đoạn**.
- Nói rõ: hệ thống sửa 1 byte trong chunk mã hóa; kỳ vọng là hash chunk không khớp; kết quả thực tế báo đúng file chunk bị sửa.

### Test đảo thứ tự đoạn
- Bấm **Test đảo thứ tự đoạn**.
- Nói rõ: hệ thống đảo sequence của chunk 1 và chunk 2; kỳ vọng là báo `Invalid chunk order`.

### Test ghép sai định dạng
- Chọn định dạng sai, ví dụ `.pdf` hoặc `.mp3` khi manifest yêu cầu `.wav`.
- Bấm **Test ghép sai định dạng**.
- Kỳ vọng là hệ thống báo `Output format mismatch`.

## 7. Benchmark và pytest

- Bấm **Chạy benchmark .mp3/.wav**.
- Bấm **Chạy pytest -vv**.
- Cho thấy 5 test passed.

## 8. Kết luận demo

Kết luận ngắn:

> Hệ thống đã đáp ứng yêu cầu đề tài: có source code, file âm thanh mẫu, manifest mẫu, benchmark report, video demo, mã hóa từng đoạn, phát hiện thiếu đoạn, sửa đoạn, đảo thứ tự đoạn và sai định dạng. File khôi phục có thể nghe lại và SHA-256 khớp với file gốc.
