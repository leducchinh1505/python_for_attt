# Python Exam Trainer

App luyện thi "Lập trình với Python" gói trong một file: **`index.html`**.

## Mở app
- Bấm đúp `index.html` để mở trong Chrome hoặc Edge.
- Nếu trình duyệt chặn chạy code khi mở file trực tiếp, chạy lệnh sau trong thư mục này rồi mở http://localhost:8765:
  `py -m http.server 8765`
- Phần trắc nghiệm, tài liệu, Error Log chạy offline. Phần chạy code cần Internet ở lần đầu để tải Pyodide 0.26.4 (khoảng 10 MB, sau đó trình duyệt cache lại).
- Tiến độ lưu trong trình duyệt. Mỗi cách mở (file:// hay localhost) là một kho lưu riêng. Dùng **Cài đặt → Xuất file JSON** để sao lưu.

## Cấu trúc
| Đường dẫn | Nội dung |
|---|---|
| `index.html` | App hoàn chỉnh (file duy nhất cần dùng) |
| `data/mcq.json` | 160 câu trắc nghiệm, 8 chủ đề, mỗi chủ đề 15 câu thường + 5 câu dự phòng |
| `data/coding.json` | 34 bài code kèm test và lời giải mẫu |
| `data/materials.json` | Tài liệu học theo chủ đề, mỗi mục ghi nguồn (giáo trình / đề cũ / bổ sung) |
| `src/app.html` | Giao diện và logic |
| `src/harness.py` | Bộ chấm Python, dùng chung cho app (Pyodide) và cho bước kiểm chứng |
| `src/verify.py` | Chạy code mọi câu trắc nghiệm dạng đọc code và mọi lời giải mẫu để kiểm tra đáp án |
| `src/build.py` | Đóng gói mọi thứ thành `index.html` |

## Sửa nội dung
Sửa file trong `data/`, rồi chạy:
```
py -I src/verify.py data
py -I src/build.py
```
