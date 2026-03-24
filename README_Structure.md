# Ghi chú về cách tổ chức thư mục dự án (Project Structure)

Dự án được ứng dụng kiến trúc phân lớp (layered architecture) cơ bản cho Desktop App, giúp code dễ bảo trì và dễ scale khi mở rộng tính năng:

- **`config/`**: Chứa các file cấu hình hệ thống (như `.env` cấu hình Database, các file text/ini cấu hình máy in/cổng COM).
- **`assets/`**: Nơi lưu trữ icon, hình ảnh, file style (`.qss` cho PyQt) của ứng dụng.
- **`src/`**: Thư mục chứa mã nguồn chính.
  - `database/`: Chứa file kết nối DB (`db_core.py`), quản lý session của SQLAlchemy.
  - `models/`: Chứa các file định nghĩa Bảng dữ liệu (ORM Model) như `product.py`, `customer.py`, `invoice.py`.
  - `ui/`: File source chứa giao diện chia theo từng màn hình (Ví dụ: `main_window.py`, `pos_view.py`, `inventory_view.py`).
  - `hardware/`: Mã nguồn điều khiển máy in dải (HM-A300E) và máy quét dải mã vạch.
  - `utils/`: Các script hỗ trợ định dạng số liệu, tính toán, backup dữ liệu `.sql`.
- **`main.py`**: File khởi chạy (Entry point) toàn bộ ứng dụng.
- **`requirements.txt`**: Danh sách thư viện Python cần thiết (`pip install -r requirements.txt`).