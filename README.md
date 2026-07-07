# FSTE - FastSecure Transfer Engine

## Giới thiệu

**FSTE - FastSecure Transfer Engine** là hệ thống truyền file âm thanh phân đoạn an toàn, được xây dựng cho bài tập lớn học phần **Nhập môn An toàn bảo mật thông tin**.

Dự án triển khai theo đề tài:

**Đề tài 7: Secure Audio Segment Transfer - Gửi tập tin âm thanh chia thành nhiều đoạn**

Hệ thống cho phép chọn một file âm thanh, chia file thành nhiều đoạn nhỏ theo byte, mã hóa từng đoạn, tạo manifest chứa metadata và hash, sau đó giải mã và ghép lại file ban đầu. File sau khi khôi phục được kiểm tra bằng SHA-256 để xác nhận có giống file gốc hay không.

Dự án hỗ trợ giao diện web local bằng Streamlit để dễ quan sát quá trình mã hóa, giải mã, xem manifest, chạy kiểm thử và quay video demo.

---

## Chức năng chính

- Chọn file âm thanh đầu vào.
- Nghe file âm thanh gốc trên giao diện.
- Tự động tính kích thước chunk phù hợp theo kích thước file.
- Chia file thành nhiều chunk theo byte.
- Mã hóa từng chunk bằng AES-GCM.
- Tạo nonce riêng cho từng chunk.
- Tạo manifest JSON chứa metadata, hash từng chunk và hash toàn file.
- Bảo vệ manifest bằng HMAC-SHA256.
- Giải mã từng chunk và ghép lại file ban đầu.
- So sánh SHA-256 của file khôi phục với file gốc.
- Nghe file âm thanh sau khi khôi phục.
- Kiểm thử các trường hợp: thiếu chunk, sửa chunk, đảo thứ tự chunk và sai định dạng.
- Chạy benchmark với file `.mp3` và `.wav`.
- Ghi log quá trình xử lý.

---

## Mục tiêu bảo mật

| Mục tiêu | Cách hệ thống xử lý |
|---|---|
| Tính bí mật | Mã hóa từng chunk bằng AES-GCM |
| Tính toàn vẹn | Kiểm tra SHA-256 của chunk và file khôi phục |
| Tính xác thực dữ liệu | AES-GCM xác thực dữ liệu mã hóa và AAD |
| Bảo vệ manifest | HMAC-SHA256 phát hiện manifest bị sửa |
| Truy vết | Ghi log quá trình mã hóa, giải mã và kiểm thử |

---

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python |
| Giao diện | Streamlit |
| Mã hóa | AES-GCM |
| Hash | SHA-256 |
| Bảo vệ manifest | HMAC-SHA256 |
| Manifest | JSON |
| Kiểm thử | pytest |
| Log | Python logging |

---

## Cấu trúc thư mục

```text
fastsecure-transfer-engine/
│
├── app.py
├── README.md
├── requirements.txt
├── run_gui.bat
├── .gitignore
│
├── input_files/
│   ├── sample.mp3
│   └── sample.wav
│
├── docs/
│   └── SAMPLE_MANIFEST_EXAMPLE.json
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
├── storage/
│   ├── encrypted_chunks/
│   ├── decrypted_chunks/
│   ├── recovered_files/
│   └── manifests/
│
├── logs/
│
├── reports/
│   └── benchmark_report.md
│
└── tests/
    ├── test_valid_transfer.py
    ├── test_missing_chunk.py
    ├── test_tampered_chunk.py
    ├── test_wrong_order.py
    └── test_wrong_format.py
Nguyên lý hoạt động
Mã hóa file
File âm thanh gốc
    ↓
Đọc file dưới dạng byte
    ↓
Tự chọn chunk size
    ↓
Chia file thành nhiều chunk
    ↓
Tạo metadata và AAD cho từng chunk
    ↓
Mã hóa từng chunk bằng AES-GCM
    ↓
Tính SHA-256 cho từng chunk mã hóa
    ↓
Tạo manifest JSON
    ↓
Ký HMAC-SHA256 cho manifest
Giải mã và khôi phục file
Chọn manifest JSON
    ↓
Kiểm tra HMAC manifest
    ↓
Kiểm tra đủ chunk
    ↓
Kiểm tra thứ tự chunk
    ↓
Kiểm tra SHA-256 từng chunk
    ↓
Giải mã từng chunk bằng AES-GCM
    ↓
Ghép chunk theo đúng thứ tự
    ↓
Tạo file recovered
    ↓
So sánh SHA-256 với file gốc

Nếu SHA-256 của file khôi phục khớp với SHA-256 của file gốc, hệ thống xác nhận file đã được khôi phục chính xác.

Manifest JSON

Manifest là file JSON dùng để lưu thông tin quản lý toàn bộ quá trình chia, mã hóa và khôi phục file.

Manifest chứa các thông tin chính:

- system_name
- transfer_id
- file_name
- file_extension
- format
- algorithm
- hash_algorithm
- file_size_bytes
- chunk_size_bytes
- total_chunks
- original_sha256
- chunks
- manifest_hmac

Mỗi chunk trong manifest có metadata riêng:

- audio_id
- segment_id
- chunk_id
- sequence_number
- offset
- plain_size
- encrypted_size
- duration
- format
- encrypted_file
- nonce
- encrypted_sha256
- aad

Manifest giúp hệ thống phát hiện các lỗi như thiếu chunk, chunk bị sửa, sai thứ tự chunk, sai định dạng hoặc manifest bị chỉnh sửa.

Cài đặt môi trường

Tạo môi trường ảo:

python -m venv venv

Kích hoạt môi trường trên Windows PowerShell:

.\venv\Scripts\activate

Cài thư viện:

pip install -r requirements.txt
Chạy giao diện web

Chạy bằng Streamlit:

streamlit run app.py

Hoặc chạy nhanh trên Windows:

.\run_gui.bat

Sau khi chạy, mở trình duyệt tại:

http://localhost:8501

Trên giao diện, người dùng có thể chọn file âm thanh, mã hóa, xem danh sách chunk, xem manifest JSON, giải mã, nghe file khôi phục, chạy kiểm thử và xem log.

Chạy bằng CLI

Mã hóa file:

python src/main.py encrypt input_files/sample.wav

Giải mã file mới nhất:

python src/main.py decrypt

Chạy benchmark:

python src/main.py benchmark

Dọn dữ liệu sinh ra trong quá trình chạy:

python src/main.py clean
Chạy kiểm thử

Chạy toàn bộ test:

pytest

Các test chính:

Test	Nội dung
test_valid_transfer.py	Mã hóa, giải mã và so sánh hash file hợp lệ
test_missing_chunk.py	Phát hiện thiếu chunk
test_tampered_chunk.py	Phát hiện chunk bị sửa
test_wrong_order.py	Phát hiện sai thứ tự chunk hoặc manifest bị sửa
test_wrong_format.py	Phát hiện ghép sai định dạng
Benchmark

Benchmark đo thời gian mã hóa, giải mã, kích thước file, chunk size và kết quả khôi phục.

Chạy benchmark:

python src/main.py benchmark

Kết quả được ghi tại:

reports/benchmark_report.md
Log hệ thống

Log được lưu tại:

logs/transfer.log

Log ghi lại các bước như mã hóa chunk, tạo manifest, kiểm tra manifest, giải mã chunk và khôi phục file.

Lưu ý bảo mật

Không đưa các file sau lên GitHub:

secret.key
venv/
storage/encrypted_chunks/
storage/decrypted_chunks/
storage/recovered_files/
storage/manifests/
logs/*.log

Trong đó, secret.key là file chứa khóa bí mật dùng cho AES-GCM và HMAC. Nếu lộ file này, dữ liệu đã mã hóa có thể bị giải mã.

Thành phần nộp bài
Thành phần	Vị trí
Source code	Toàn bộ repository
File âm thanh mẫu	input_files/sample.mp3, input_files/sample.wav
Manifest mẫu	docs/SAMPLE_MANIFEST_EXAMPLE.json
Benchmark report	reports/benchmark_report.md
Video demo	Quay giao diện Streamlit khi mã hóa, giải mã và kiểm thử

