import sys
import os
from PyQt5.QtWidgets import QApplication

# Fix UnicodeEncodeError trên Windows với console (Nuitka / PyInstaller)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")

# Thêm thư mục src vào path để dễ dàng import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import traceback
def global_exception_handler(exc_type, exc_value, exc_traceback):
    try:
        exe_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
        log_path = os.path.join(exe_dir, "jewelry_crash.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("=== CRASH REPORT ===\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            f.write("====================\n\n")
    except:
        pass
    # Thử hiển thị popup nếu PyQt đã load
    try:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Lỗi Nghiêm Trọng", f"App bị crash! Lỗi ghi ở jewelry_crash.log\n{str(exc_value)}")
    except:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

from src.database.init_db import init_database
from src.utils.config_manager import verify_and_setup_config


def _check_startup_password(app: QApplication) -> bool:
    """
    Hiện PasswordDialog nếu đang chạy bản Release (hash đã được nhúng).
    Trong môi trường dev (PLACEHOLDER_HASH), bỏ qua bước này.
    Trả về True nếu xác thực thành công hoặc đang ở dev mode.
    """
    from src.utils.auth import _APP_PASSWORD_HASH
    if _APP_PASSWORD_HASH == "PLACEHOLDER_HASH":
        # Dev mode – không hỏi mật khẩu
        return True

    from src.ui.password_dialog import PasswordDialog
    dlg = PasswordDialog()
    # exec_() trả QDialog.Accepted(1) nếu đúng mật khẩu
    return dlg.exec_() == 1


def main():
    print("Khởi động hệ thống Jewelry POS...")

    # Khởi tạo App PyQt5 đầu tiên để có thể hiển thị dialog
    app = QApplication(sys.argv)

    # ── BƯỚC 1: Xác thực mật khẩu khởi động ─────────────────────────────
    if not _check_startup_password(app):
        # Người dùng đóng dialog hoặc sai quá số lần → đã sys.exit() bên trong
        sys.exit(0)

    # ── BƯỚC 2: Kiểm tra / thiết lập kết nối Database ────────────────────
    if not verify_and_setup_config():
        print("Cấu hình Database thất bại hoặc bị hủy. Thoát ứng dụng.")
        sys.exit(0)

    # ── BƯỚC 3: Khởi tạo Database (tạo bảng nếu chưa có) ─────────────────
    init_database()

    # Áp dụng style chung
    app.setStyle("Fusion")

    # ── BƯỚC 4: Nạp giao diện chính ──────────────────────────────────────
    from src.ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()