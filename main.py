import sys
import os
from PyQt5.QtWidgets import QApplication

# Thêm thư mục src vào path để dễ dàng import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.database.init_db import init_database
from src.utils.config_manager import verify_and_setup_config

def main():
    print("Khởi động hệ thống Jewelry POS...")
    
    # Khởi tạo App PyQt5 đầu tiên để có thể hiển thị UI check cấu hình (dialog)
    app = QApplication(sys.argv)
    
    # Ở lần đầu tiên hoặc nếu ko kết nối được DB -> sẽ hiện Dialog cấu hình thư mục, db
    if not verify_and_setup_config():
        print("Cấu hình Database thất bại hoặc bị hủy. Thoát ứng dụng.")
        sys.exit(0)
    
    # Kiểm tra và tạo Database luôn nếu chưa có trước khi tải UI chính
    init_database()
    
    # Áp dụng một style chung (nếu cần)
    app.setStyle("Fusion")
    
    # Phải gọi MainWindow sau khi app đã có thông tin database
    from src.ui.main_window import MainWindow
    
    # Khởi chạy giao diện chính (UI)
    window = MainWindow()
    window.show()
    
    # Bắt đầu vòng lặp sự kiện (Event Loop) cửa sổ Desktop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()