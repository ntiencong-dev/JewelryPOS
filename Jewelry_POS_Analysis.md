# Phân tích và Thiết kế: Hệ thống Quản lí Bán hàng Trang sức (Jewelry POS)

## 1. Tổng quan dự án
Hệ thống phần mềm quản lý kho và bán hàng (POS - Point of Sale) dành riêng cho cửa hàng trang sức, hoạt động dưới dạng Desktop App chạy cục bộ trên máy Laptop/PC (Windows). Hệ thống tích hợp quét mã vạch qua USB/Bluetooth để quản lý kho/bán hàng nhanh chóng và kết nối trực tiếp với máy in HM-A300E (qua USB/Bluetooth) để xuất hóa đơn và in tem mã vạch. Hỗ trợ tính năng sao lưu (backup) dữ liệu và cài đặt thông qua file `.exe`.

## 2. Phân tích Tính năng Chi tiết (Feature Breakdown)

### 2.1. Module Quản lý Sản phẩm & Kho hàng (Inventory Management)
*   **Thông tin sản phẩm:** Tên sản phẩm, Mã sản phẩm (SKU/Barcode), Đơn giá, Số lượng tồn kho, Đơn vị tính (Chỉ, Phân, Gram, Cái...).
*   **Quản lý Barcode:** Tự động sinh mã vạch nội bộ hoặc nhận diện mã vạch từ nhà cung cấp. Hỗ trợ tính năng in tem nhãn mã vạch (tích hợp máy in HM-A300E) để dán lên sản phẩm.
*   **Nhập/Xuất kho & Tìm kiếm:** 
    *   Tạo phiếu nhập kho, cập nhật số lượng và tính toán giá vốn.
    *   Hỗ trợ quét mã vạch chuyên dụng (qua cổng USB/Bluetooth) để tìm kiếm nhanh sản phẩm hoặc xử lý kho.
*   **Cảnh báo tồn kho:** Báo động khi sản phẩm sắp hết hàng.

### 2.2. Module Quản lý Khách hàng & Công nợ (Customer & Debt Management)
*(Để tính toán được "Nợ cũ", "Công nợ mới", bắt buộc phải có hệ thống Quản lý Khách hàng)*
*   **Hồ sơ khách hàng:** Tên, Số điện thoại, Địa chỉ.
*   **Kiểm soát công nợ:** Theo dõi tổng nợ của khách. Tích hợp tự động vào hóa đơn mua hàng tiếp theo.
*   **Lịch sử giao dịch:** Xem lại danh sách các hóa đơn khách đã mua và tiến trình trả nợ.

### 2.3. Module Bán hàng & Hóa đơn (Sales & Invoicing)
*   **Giao diện bán hàng (POS):** 
    *   Thêm sản phẩm vào giỏ hàng bằng cách quét mã vạch hoặc tìm kiếm tên/mã.
    *   Tùy chỉnh linh hoạt số lượng, đơn giá (nếu có chiết khấu riêng hoặc giá vàng thay đổi).
*   **Cấu trúc Hóa đơn:**
    *   *Thông tin chung:* Số hóa đơn (Tự động tăng), Ngày bán hàng, Ngày ký/xuất hóa đơn.
    *   *Chi tiết:* Danh sách sản phẩm (Tên, Số lượng, Đơn giá, Thành tiền = SL * Đơn giá).
    *   *Thanh toán:* 
        *   Tổng cộng (Subtotal)
        *   Giảm giá (Discount)
        *   Nợ cũ (tự động truy xuất từ hồ sơ Khách hàng)
        *   Tổng thanh toán = (Tổng cộng - Giảm giá) + Nợ cũ
        *   Tiền khách thanh toán (Số tiền khách đưa thực tế)
        *   Công nợ mới = Tổng thanh toán - Tiền khách thanh toán.
*   **In Hóa đơn (Hardware Integration):**
    *   In hóa đơn biên lai trực tiếp từ máy in HM-A300E qua kết nối Bluetooth hoặc USB cable.

### 2.4. Module Hệ thống & Dữ liệu (System & Backup)
*   **Backup & Khôi phục dữ liệu:** Tính năng sao lưu CSDL (export file backup). Giúp người dùng dễ dàng chuyển đổi qua máy mới cài đặt lại phần mềm và khôi phục (import) giữ nguyên toàn bộ lịch sử dữ liệu.
*   **Cài đặt:** Đóng gói phần mềm thành file chạy `setup.exe` thuận tiện cho việc cài đặt và khởi chạy.

---

## 3. Đề xuất Công nghệ (Tech Stack Recommendation)

Hệ thống được xây dựng dưới dạng ứng dụng Desktop chạy offline/cục bộ (Local).

*   **Ngôn ngữ Lập trình (Logic & UI):**
    *   **Công nghệ:** **Python**.
    *   **Lý do:** Python có các thư viện hỗ trợ giao diện tốt (PyQt/PySide hoặc Tkinter/CustomTkinter), đồng thời cực kỳ mạnh mẽ trong việc kiểm soát phần cứng qua Serial/USB/Bluetooth (phù hợp với máy in HM-A300E và máy quét mã vạch), và có thể đóng gói thành file `.exe` bằng PyInstaller.
*   **Cơ sở dữ liệu (Database):**
    *   **Công nghệ:** **PostgreSQL** (chạy cục bộ).
    *   **Lý do:** PostgreSQL là RDBMS rất bền bỉ, tính toàn vẹn dữ liệu tốt (đảm bảo tính tiền, công nợ chính xác). Có thể dễ dàng thực hiện script Export/Import qua lệnh `pg_dump`/`pg_restore` cho tính năng DB Backup.

---

## 4. Kiến trúc Hệ thống (System Architecture)

*   **Mô hình hoạt động:** Standalone Desktop Application.
    *   **Giao diện & Logic:** App Python cài đặt thẳng trên Laptop Windows của cửa hàng, tương tác/kết nối trực tiếp với Database PostgreSQL Local.
    *   **Quét mã vạch:** Dùng máy quét mã vạch (Bluetooth / USB Cable). Cửa sổ POS hoặc Kho liên tục lắng nghe raw input từ máy quét để tìm kiếm hoặc thêm sản phẩm tự động vào giỏ hàng.
    *   **Xử lý In ấn:** Python gửi lệnh trực tiếp bằng packet data qua cổng USB/COM (Bluetooth) xuống máy in HM-A300E để in lệnh in tem (TSPL hoặc ngôn ngữ tương đương) và in hóa đơn (ESC/POS).

---

## 5. Các bước triển khai (Phase Plan)

1.  **Thiết kế UI/UX & Database Schema:** Mockup giao diện Desktop, thiết kế sơ đồ ERD dựa trên PostgreSQL.
2.  **Khởi tạo App & Database (Python & PostgreSQL):** 
    *   Set up cấu trúc code Python app.
    *   Kết nối và ánh xạ Database thông qua SQLAlchemy/psycopg2.
3.  **Xây dựng các Module Lõi:** 
    *   Quản lý kho (nhập kho, barcode).
    *   Bán hàng (POS), thanh toán, trừ tồn kho và tự động cộng dồn nợ vào hồ sơ dòng tiền khách.
4.  **Tích hợp Hardware (Máy quét & Máy in HM-A300E):**
    *   Tích hợp input máy quét mã để tìm kiếm/đưa hàng vào giỏ.
    *   Thiết lập logic lệnh in: In Tem nhãn và In bill (với khổ giấy HM-A300E).
5.  **Tính năng Hệ thống:** Xây dựng luồng Export toàn bộ DB (Backup dữ liệu) thành file zip/sql và luồng Restore để nạp lại dữ liệu.
6.  **Đóng gói & Cài đặt (Packaging):** Dùng PyInstaller build Python code thành file `.exe` và kết hợp PostgreSQL portable/tạo Installer chung để khách dễ cài đặt lên mọi Windows PC.
