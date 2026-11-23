# Python Exam Trainer

App luyện thi "Lập trình với Python" gói trong một file: **`index.html`**.

## Format đề cuối kỳ (theo thầy thông báo)
- Phần 1: 50 câu trắc nghiệm trong 20 phút (khoảng 24 giây/câu), dạng đọc code đoán kết quả hoặc chọn code thay thế.
- Phần 2: 1 đến 2 bài lập trình trong 15 phút, thao tác trên list và dict.
- Thầy nói có thể thêm phần khác, nên app vẫn giữ đủ 8 chủ đề.

App bám theo format này ở hai chỗ:
- **Thi thử**: hai phần tính giờ riêng (50 câu / 20 phút, rồi 2 bài / 15 phút). Tỷ trọng điểm thầy chưa công bố, app tạm tính 50/50.
- **Luyện tốc độ**: mỗi câu có đồng hồ riêng 24 giây.

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
| `data/mcq.json` | 401 câu trắc nghiệm, 8 chủ đề. 342 câu thuộc dạng của đề thi: 267 câu đọc code, 75 câu thay thế code |
| `data/coding.json` | 50 bài code kèm test và lời giải mẫu (16 bài list/dict ngắn theo format đề) |
| `data/materials.json` | Tài liệu học theo chủ đề, mỗi mục ghi nguồn (giáo trình / đề cũ / bổ sung) |
| `src/app.html` | Giao diện và logic |
| `src/harness.py` | Bộ chấm Python, dùng chung cho app (Pyodide) và cho bước kiểm chứng |
| `src/verify.py` | Chạy Python thật để kiểm tra đáp án: câu đọc code, câu thay thế code (chỉ đúng 1 phương án in ra kết quả mong muốn), lời giải mẫu |
| `src/build.py` | Đóng gói mọi thứ thành `index.html` |

## Sửa nội dung
Sửa file trong `data/`, rồi chạy:
```
py -I src/verify.py data
py -I src/build.py
```
