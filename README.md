# Quick Launcher & Local Server Supervisor (`Super + W` — v2.1)

Công cụ GTK3 nhẹ trên Linux để mở nhanh website/ứng dụng và bật/tắt, giám sát các server dự án nội bộ (`toeic`, `news`, ...) từ một cửa sổ trung gian duy nhất.

## Điểm mới ở bản v2.1
- **Hết nháy ở tab Server**: Cập nhật trạng thái PID trực tiếp trên từng dòng (`in-place`), chỉ kiểm tra định kỳ mỗi 5 giây khi đang mở tab Server và không đọc lại file cấu hình trong vòng lặp poll.
- **Giao diện gọn & tự nhiên hơn**:
  - Căn lề trái chuẩn cho toàn bộ nút sidebar (`1 Web & App`, `2 Server`, `⚙ Cài đặt`).
  - Đưa badge đếm số server đang chạy (`X/Y chạy`) sang góc phải thanh tìm kiếm của tab Server.
  - Thay các dấu chấm tròn bằng thanh trạng thái màu bên trái và dấu gạch ngang thoáng `—`.
- **Tối ưu code & dọn dẹp tự động**:
  - Đọc/ghi `items.tsv` qua module `csv` chuẩn, giữ nguyên tương thích ngược với dữ liệu cũ.
  - Cảnh báo ngay trên dòng nếu server bật lên bị dừng sớm (sai lệnh/trùng port); tự dọn file `.pid`, `.log` khi xóa dự án và dọn socket IPC khi thoát hẳn.
  - Điều hướng mũi tên `Up`/`Down` chọn dòng mượt ngay khi đang đứng ở ô tìm kiếm.

## Cài đặt / Cập nhật
```bash
unzip Set-up-SuperW-v2.1.zip
cd Set-up-SuperW
chmod +x setup_launcher_gui.sh
bash setup_launcher_gui.sh
```
