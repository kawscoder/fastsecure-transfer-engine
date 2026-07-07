# Test Report

| Test case | Mô tả | Kỳ vọng |
|---|---|---|
| TC01 | Gửi file âm thanh hợp lệ | Giải mã, ghép file và SHA-256 khớp file gốc |
| TC02 | Làm mất một đoạn | Hệ thống báo thiếu đúng chunk bị mất |
| TC03 | Sửa một đoạn | Hệ thống báo hash chunk không khớp hoặc AES-GCM xác thực thất bại |
| TC04 | Đảo thứ tự đoạn | Hệ thống báo thứ tự chunk không hợp lệ |
| TC05 | Ghép sai định dạng | Hệ thống báo output format không khớp manifest |

Chạy kiểm thử tự động:

```bash
pytest -vv
```

Kết quả mong đợi: toàn bộ test passed.
