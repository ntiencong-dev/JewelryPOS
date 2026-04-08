"""
src/ui/password_dialog.py
=========================
Dialog nhập mật khẩu khởi động – hiển thị TRƯỚC khi thiết lập database.

Features:
  - Ô nhập password ẩn (*), có nút 👁 ẩn/hiện
  - Tối đa 3 lần thử sai → tự thoát ứng dụng
  - Giao diện tối giản, gọn gàng
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QPixmap


class PasswordDialog(QDialog):
    """Dialog yêu cầu nhập mật khẩu khi khởi động ứng dụng."""

    MAX_ATTEMPTS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attempts = 0
        self._setup_ui()

    # ─────────────────────────────────────────────
    # UI Setup
    # ─────────────────────────────────────────────
    def _setup_ui(self):
        self.setWindowTitle("Xác thực – Jewelry POS")
        self.setFixedSize(380, 230)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)

        # Không cho phép đóng cửa sổ bằng Alt+F4 / nút X mà không xác thực
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 25, 30, 20)

        # Tiêu đề
        lbl_title = QLabel("🔒  Jewelry POS")
        lbl_title.setFont(QFont("Arial", 15, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Nhập mật khẩu để tiếp tục")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(lbl_sub)

        # Ô nhập password
        pw_layout = QHBoxLayout()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("Mật khẩu...")
        self.txt_password.setMinimumHeight(36)
        self.txt_password.setStyleSheet(
            "QLineEdit { border: 1.5px solid #bdc3c7; border-radius: 6px;"
            " padding: 0 10px; font-size: 13px; }"
            "QLineEdit:focus { border-color: #3498db; }"
        )
        self.txt_password.returnPressed.connect(self._on_confirm)

        self.btn_toggle = QPushButton("👁")
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setStyleSheet(
            "QPushButton { border: 1.5px solid #bdc3c7; border-radius: 6px;"
            " background: white; font-size: 14px; }"
            "QPushButton:checked { background: #ecf0f1; }"
        )
        self.btn_toggle.clicked.connect(self._toggle_echo)

        pw_layout.addWidget(self.txt_password)
        pw_layout.addWidget(self.btn_toggle)
        layout.addLayout(pw_layout)

        # Thông báo số lần còn lại
        self.lbl_hint = QLabel("")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        self.lbl_hint.setStyleSheet("color: #e74c3c; font-size: 10px;")
        layout.addWidget(self.lbl_hint)

        # Nút xác nhận
        self.btn_confirm = QPushButton("Xác nhận  →")
        self.btn_confirm.setMinimumHeight(38)
        self.btn_confirm.setStyleSheet(
            "QPushButton { background-color: #2980b9; color: white;"
            " border-radius: 6px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background-color: #3498db; }"
            "QPushButton:pressed { background-color: #1a5276; }"
        )
        self.btn_confirm.clicked.connect(self._on_confirm)
        layout.addWidget(self.btn_confirm)

        self.txt_password.setFocus()

    # ─────────────────────────────────────────────
    # Handlers
    # ─────────────────────────────────────────────
    def _toggle_echo(self, checked: bool):
        mode = QLineEdit.Normal if checked else QLineEdit.Password
        self.txt_password.setEchoMode(mode)

    def _on_confirm(self):
        from src.utils.auth import verify_password

        password = self.txt_password.text()
        if not password:
            self.lbl_hint.setText("Vui lòng nhập mật khẩu.")
            return

        if verify_password(password):
            self.accept()
        else:
            self._attempts += 1
            remaining = self.MAX_ATTEMPTS - self._attempts

            if remaining <= 0:
                QMessageBox.critical(
                    self, "Xác thực thất bại",
                    "Sai mật khẩu quá số lần cho phép.\nỨng dụng sẽ thoát."
                )
                import sys
                sys.exit(1)
            else:
                self.txt_password.clear()
                self.txt_password.setFocus()
                self.lbl_hint.setText(
                    f"❌ Mật khẩu không đúng. Còn {remaining} lần thử."
                )
                self.btn_confirm.setStyleSheet(
                    self.btn_confirm.styleSheet()
                    + "QPushButton { border: 1px solid #e74c3c; }"
                )

    # ─────────────────────────────────────────────
    # Override close – không cho thoát bằng nút X
    # ─────────────────────────────────────────────
    def closeEvent(self, event):
        """Chặn đóng cửa sổ bằng nút X – phải nhập mật khẩu đúng."""
        import sys
        sys.exit(0)
