# FSTE - FastSecure Transfer Engine


## Cập nhật giao diện bản demo nâng cao

Phiên bản GUI hiện tại đã được chỉnh để phục vụ quay video demo và bảo vệ bài trước giảng viên:

- Không cho người dùng nhập `chunk size` thủ công; hệ thống tự tính theo kích thước file để tránh file lớn bị chia thành quá nhiều chunk.
- Tab **Mã hóa từng bước** hiển thị rõ quy trình: nhận file, nhận diện định dạng, tính hash file gốc, chia chunk, mã hóa AES-GCM từng chunk, tạo manifest và HMAC.
- Tab **Giải mã & ghép** hiển thị các bước kiểm tra manifest, kiểm tra định dạng, kiểm tra thiếu/sửa/đảo chunk, giải mã từng chunk và so sánh SHA-256.
- Tab **Manifest & chunk** hiển thị thống kê, giải thích từng trường, danh sách chunk dạng bảng cuộn và JSON manifest đầy đủ.
- Tab **Test bảo mật** cho phép thao tác kiểm thử thủ công: làm mất một đoạn, sửa một đoạn, đảo thứ tự đoạn, ghép sai định dạng. Mỗi test hiển thị rõ đầu vào, kỳ vọng và kết quả thực tế.
- Pytest hiện có 5 test: transfer hợp lệ, thiếu chunk, sửa chunk, đảo thứ tự, sai định dạng.

## 1. Giới thiệu

**FSTE - FastSecure Transfer Engine** là hệ thống truyền file phân đoạn an toàn, được xây dựng cho bài tập lớn học phần **Nhập môn An toàn bảo mật thông tin**.

Dự án được phát triển theo đề tài:

**Đề tài 7: Secure Audio Segment Transfer - Gửi tập tin âm thanh chia thành nhiều đoạn**

Mục tiêu của hệ thống là nhận một file âm thanh, chia file thành nhiều đoạn nhỏ theo byte, mã hóa từng đoạn, tạo manifest chứa metadata và hash, sau đó giải mã và ghép lại file ban đầu. Hệ thống có khả năng phát hiện các lỗi hoặc hành vi tấn công như thiếu đoạn, sửa đoạn, đảo thứ tự đoạn và sai toàn vẹn dữ liệu.

Phiên bản hiện tại tập trung triển khai cho nhóm file media, đặc biệt là:

```text
.mp3
.wav
```

Các định dạng tài liệu như `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.zip`, `.rar`, `.7z` được để trong hướng mở rộng sau.

---

## 2. Điểm nâng cao của sản phẩm

Ngoài các yêu cầu nền của đề tài, hệ thống có thêm các điểm nâng cao:

| Nâng cấp | Ý nghĩa |
|---|---|
| AES-GCM | Vừa mã hóa dữ liệu, vừa phát hiện sửa đổi khi giải mã |
| SHA-256 từng chunk | Phát hiện chunk mã hóa bị sửa hoặc lỗi truyền |
| SHA-256 toàn file | Chứng minh file sau ghép giống file gốc |
| Manifest HMAC | Phát hiện manifest bị sửa đổi |
| AAD trong AES-GCM | Ràng buộc metadata quan trọng với ciphertext |
| Chia theo byte streaming | Không đọc toàn bộ file vào RAM, phù hợp file lớn |
| Cấu trúc mở rộng | Có thể phát triển thêm document mode/web module sau này |

---

## 3. Mục tiêu bảo mật

| Mục tiêu | Ý nghĩa |
|---|---|
| Tính bí mật | File được mã hóa, người ngoài không đọc/nghe được nội dung |
| Tính toàn vẹn | Phát hiện file hoặc chunk bị sửa đổi |
| Đúng thứ tự | Phát hiện chunk bị đảo thứ tự |
| Đầy đủ dữ liệu | Phát hiện thiếu chunk |
| Truy vết | Ghi log quá trình mã hóa, giải mã, kiểm tra và ghép file |

---

## 4. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python |
| Mã hóa | AES-GCM |
| Hash | SHA-256 |
| Bảo vệ manifest | HMAC-SHA256 |
| Manifest | JSON |
| Log | Python logging |
| Benchmark | time/performance measurement |
| Kiểm thử | pytest |

---

## 5. Cấu trúc thư mục

```text
fastsecure-transfer-engine/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── input_files/
│   └── sample.wav
│
├── future_document_mode/
│   ├── README.md
│   └── placeholder.txt
│
├── storage/
│   ├── encrypted_chunks/
│   ├── decrypted_chunks/
│   ├── recovered_files/
│   └── manifests/
│
├── logs/
│   └── transfer.log
│
├── reports/
│   ├── benchmark_report.md
│   └── test_report.md
│
├── src/
│   ├── main.py
│   ├── config.py
│   ├── file_detector.py
│   ├── audio_utils.py
│   ├── chunker.py
│   ├── crypto_engine.py
│   ├── hash_utils.py
│   ├── manifest_manager.py
│   ├── verifier.py
│   ├── benchmark.py
│   └── logger_config.py
│
└── tests/
    ├── test_valid_transfer.py
    ├── test_missing_chunk.py
    ├── test_tampered_chunk.py
    └── test_wrong_order.py
```

---

## 6. Nguyên lý hoạt động

### 6.1. Mã hóa file

```text
File gốc
   ↓
Đọc file dưới dạng byte
   ↓
Chia file thành nhiều chunk
   ↓
Mã hóa từng chunk bằng AES-GCM
   ↓
Tính hash từng chunk đã mã hóa
   ↓
Tạo manifest.json + manifest_hmac
   ↓
Lưu chunk mã hóa và manifest
```

### 6.2. Giải mã và khôi phục file

```text
Đọc manifest
   ↓
Kiểm tra HMAC của manifest
   ↓
Kiểm tra đủ chunk
   ↓
Kiểm tra hash từng chunk
   ↓
Kiểm tra thứ tự chunk
   ↓
Giải mã từng chunk
   ↓
Ghép lại file hoàn chỉnh
   ↓
So sánh hash file gốc và file khôi phục
```

Nếu hash khớp, file được khôi phục thành công. Nếu hash không khớp, hệ thống báo lỗi toàn vẹn dữ liệu.

---

## 7. Manifest là gì?

Manifest là file JSON kê khai thông tin của file sau khi được chia thành nhiều chunk.

Manifest lưu:

```text
- transfer_id / audio_id
- Tên file gốc
- Định dạng file
- Kích thước file
- Số lượng chunk
- Kích thước mỗi chunk
- Nonce của từng chunk
- Hash từng chunk đã mã hóa
- Hash toàn bộ file gốc
- HMAC bảo vệ manifest
```

Ví dụ manifest:

```json
{
  "transfer_id": "TRF-20260707-001",
  "file_name": "sample.wav",
  "file_extension": "wav",
  "file_category": "media",
  "delivery_type": "type_1_media",
  "algorithm": "AES-GCM",
  "chunk_size_bytes": 4194304,
  "total_chunks": 3,
  "original_sha256": "hash_file_goc",
  "chunks": [
    {
      "audio_id": "TRF-20260707-001",
      "segment_id": "CHK-000001",
      "sequence_number": 1,
      "offset": 0,
      "plain_size": 4194304,
      "duration": 2.0,
      "format": "wav",
      "encrypted_file": "CHK-000001_OF-000003_sample.wav.enc",
      "nonce": "base64_nonce",
      "encrypted_sha256": "hash_chunk_da_ma_hoa"
    }
  ],
  "manifest_hmac": "hmac_sha256"
}
```

Manifest giúp hệ thống phát hiện:

```text
- Thiếu chunk
- Chunk bị sửa
- Chunk bị đảo thứ tự
- Manifest bị sửa
- File sau ghép không giống file gốc
```

---

## 8. Hash đóng vai trò gì?

Hệ thống sử dụng **SHA-256** để kiểm tra toàn vẹn dữ liệu.

### Hash từng chunk

Dùng để phát hiện chunk đã mã hóa có bị sửa không.

```text
CHK-000001.enc → SHA-256 → encrypted_sha256
```

Nếu ai đó sửa file `.enc`, hash tính lại sẽ khác với hash trong manifest.

### Hash toàn bộ file

Dùng để chứng minh file sau khi khôi phục giống file gốc.

```text
sample.wav → SHA-256 → original_sha256
RECOVERED_sample.wav → SHA-256 → recovered_sha256
```

Nếu hai giá trị hash giống nhau, file sau khi khôi phục là hợp lệ.

---

## 9. Mã hóa bằng AES-GCM

Hệ thống sử dụng **AES-GCM** để mã hóa từng chunk.

AES-GCM có hai vai trò:

```text
1. Mã hóa dữ liệu để bảo vệ tính bí mật.
2. Phát hiện dữ liệu bị sửa đổi trong quá trình giải mã.
```

Mỗi chunk có một `nonce` riêng.

```text
chunk gốc + key + nonce + AAD → AES-GCM → chunk mã hóa
```

`AAD` là metadata xác thực bổ sung. Trong hệ thống này, AAD gồm `transfer_id`, `chunk_id`, `sequence_number`, `offset`, `plain_size`, `file_name`. Nếu metadata bị sửa, quá trình giải mã sẽ thất bại.

---

## 10. Cài đặt môi trường

### Bước 1: Tạo môi trường ảo

```bash
python -m venv venv
```

### Bước 2: Kích hoạt môi trường ảo

Trên Windows PowerShell:

```bash
.\venv\Scripts\activate
```

Trên macOS/Linux:

```bash
source venv/bin/activate
```

### Bước 3: Cài thư viện

```bash
pip install -r requirements.txt
```

---

## 11. Cách chạy chương trình

### Mã hóa file

```bash
python src/main.py encrypt input_files/sample.wav
```

Có thể chỉnh chunk size để tạo nhiều chunk hơn khi demo:

```bash
python src/main.py encrypt input_files/sample.wav --chunk-size 1024
```

### Giải mã và khôi phục file

```bash
python src/main.py decrypt
```

### Chạy benchmark

```bash
python src/main.py benchmark
```

### Kiểm thử mất chunk

Trước tiên mã hóa file:

```bash
python src/main.py clean
python src/main.py encrypt input_files/sample.wav --chunk-size 1024
```

Sau đó chạy:

```bash
python src/main.py test-missing
```

Kết quả mong đợi: hệ thống báo thiếu chunk.

### Kiểm thử sửa chunk

```bash
python src/main.py clean
python src/main.py encrypt input_files/sample.wav --chunk-size 1024
python src/main.py test-tamper
```

Kết quả mong đợi: hệ thống báo hash chunk không khớp hoặc giải mã thất bại.

### Kiểm thử đảo thứ tự chunk / sửa manifest

```bash
python src/main.py clean
python src/main.py encrypt input_files/sample.wav --chunk-size 1024
python src/main.py test-wrong-order
```

Kết quả mong đợi: hệ thống báo manifest đã bị sửa đổi do HMAC không hợp lệ.

---

## 12. Chạy pytest

```bash
pytest
```

Các test chính:

| Mã test | Nội dung kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC01 | Gửi file âm thanh hợp lệ | Giải mã và ghép file thành công |
| TC02 | Làm mất một chunk | Hệ thống phát hiện thiếu chunk |
| TC03 | Sửa một chunk đã mã hóa | Hệ thống phát hiện hash sai hoặc giải mã lỗi |
| TC04 | Đảo thứ tự chunk / sửa manifest | Hệ thống phát hiện manifest không hợp lệ |
| TC05 | So sánh hash file gốc và file khôi phục | Hai hash phải giống nhau nếu dữ liệu hợp lệ |
| TC06 | Benchmark `.mp3` và `.wav` | Có kết quả thời gian xử lý |

---

## 13. Benchmark

Benchmark đo các thông tin:

```text
- Kích thước file
- Số lượng chunk
- Thời gian mã hóa
- Thời gian giải mã
- Kết quả kiểm tra hash
```

Kết quả được ghi vào:

```text
reports/benchmark_report.md
```

---

## 14. Log hệ thống

Log được lưu tại:

```text
logs/transfer.log
```

Ví dụ log:

```text
[INFO] Start encrypt file: sample.wav
[INFO] Encrypted chunk: CHK-000001
[INFO] Manifest created successfully
[INFO] Start decrypt process
[INFO] Recovered file successfully
```

Log giúp truy vết quá trình xử lý và làm minh chứng cho báo cáo.

---

## 15. Phạm vi hiện tại và hướng phát triển

### Phạm vi hiện tại

Phiên bản hiện tại tập trung vào:

```text
- File âm thanh .mp3 và .wav
- Chia file theo byte
- Mã hóa từng chunk
- Tạo manifest
- Kiểm tra toàn vẹn
- Benchmark
- Log
```

### Hướng phát triển

Trong tương lai, hệ thống có thể mở rộng thêm:

```text
- Complete Document Mode cho .docx, .pptx, .xlsx, .pdf, .zip, .rar, .7z
- Tích hợp vào website quản lý tài liệu
- Phân quyền người dùng
- Watermark tài liệu
- Upload/download qua web
- Hàng đợi xử lý nền bằng Redis Queue hoặc Celery
- Stream Mode cho audio/video lớn
- Resume upload/download khi mất kết nối
```

---

## 16. Tóm tắt

FSTE là hệ thống truyền file phân đoạn an toàn. Hệ thống đọc file dưới dạng byte, chia thành nhiều chunk, mã hóa từng chunk bằng AES-GCM, tạo manifest chứa metadata và hash, sau đó giải mã và ghép lại file ban đầu. Hệ thống có thể phát hiện thiếu chunk, sửa chunk, đảo thứ tự chunk, sửa manifest và kiểm tra file khôi phục bằng SHA-256.

Dự án đáp ứng yêu cầu chính của đề tài **Secure Audio Segment Transfer** và có khả năng mở rộng thành module bảo mật file cho các hệ thống thực tế.

---

## 11A. Chạy giao diện web demo

Ngoài CLI, dự án có giao diện web local bằng Streamlit để quay video demo dễ hơn. Giao diện hỗ trợ:

```text
- Nghe file âm thanh gốc trong input_files
- Upload thêm file âm thanh/video để thử
- Mã hóa file thành nhiều chunk
- Xem manifest JSON trực tiếp
- Giải mã và ghép file
- Nghe file âm thanh sau khi khôi phục
- Chạy benchmark .mp3/.wav
- Chạy pytest
- Xem log hệ thống
```

Chạy giao diện:

```bash
streamlit run app.py
```

Trên Windows có thể chạy nhanh:

```bash
run_gui.bat
```

Sau khi chạy, trình duyệt sẽ mở giao diện FSTE. Thứ tự demo khuyến nghị:

```text
1. Vào tab Tổng quan để nghe file gốc.
2. Vào tab Mã hóa để chia file và mã hóa từng chunk.
3. Vào tab Giải mã & nghe để khôi phục và nghe file recovered.
4. Vào tab Manifest để giải thích metadata, hash, nonce, HMAC.
5. Vào tab Benchmark/Test để chạy benchmark và pytest.
6. Vào tab Log để xem quá trình xử lý.
```
