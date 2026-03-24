import os
import sys
import json
import psycopg2
from dotenv import load_dotenv, set_key
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, 
    QMessageBox, QHBoxLayout, QFileDialog, QLabel
)
from PyQt5.QtCore import Qt

CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.jewelrypos_config.json')

def get_data_folder():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('data_folder')
        except:
            pass
    return None

def save_data_folder(path):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'data_folder': path}, f)

def get_env_path():
    data_dir = get_data_folder()
    if data_dir and os.path.exists(data_dir):
        return os.path.join(data_dir, '.env')
    return None

def init_env_file(env_path):
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=\n")
            f.write("DB_USER=\n")
            f.write("DB_PASS=\n")
            f.write("DB_NAME=jewelry_pos\n")

def check_db_connection(host, port, user, password):
    if not host or not port or not user or password is None:
        return False, "Vui lòng điền đầy đủ thông tin!"
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname="postgres",
            connect_timeout=3
        )
        conn.close()
        return True, "Kết nối thành công!"
    except Exception as e:
        return False, f"Lỗi kết nối:\n{str(e)}"

class SelectFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn Thư Mục Dữ Liệu")
        self.setMinimumWidth(450)
        self.selected_folder = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Vui lòng chọn thư mục để lưu trữ cấu hình và data của phần mềm:")
        layout.addWidget(lbl)
        
        hbox = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setReadOnly(True)
        hbox.addWidget(self.txt_path)
        
        btn_browse = QPushButton("Chọn Thư Mục...")
        btn_browse.clicked.connect(self.browse_folder)
        hbox.addWidget(btn_browse)
        
        layout.addLayout(hbox)
        
        btn_next = QPushButton("Tiếp theo (Next)")
        btn_next.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 5px;")
        btn_next.clicked.connect(self.on_next)
        layout.addWidget(btn_next)
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục data")
        if folder:
            self.txt_path.setText(folder)
            
    def on_next(self):
        f = self.txt_path.text().strip()
        if not f or not os.path.exists(f):
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một thư mục hợp lệ hợp lệ!")
            return
        self.selected_folder = f
        self.accept()

class DatabaseConfigDialog(QDialog):
    def __init__(self, env_path, parent=None):
        super().__init__(parent)
        self.env_path = env_path
        self.setWindowTitle("Cấu hình Database PostgreSQL")
        self.setMinimumWidth(400)
        self.success = False
        self.init_ui()
        self.load_current_env()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_host = QLineEdit()
        self.txt_port = QLineEdit()
        self.txt_user = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_dbname = QLineEdit()

        form.addRow("Host:", self.txt_host)
        form.addRow("Port (VD 5432):", self.txt_port)
        form.addRow("User (VD postgres):", self.txt_user)
        form.addRow("Password:", self.txt_pass)
        form.addRow("Database Name:", self.txt_dbname)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.btn_test = QPushButton("Kiểm tra kết nối")
        self.btn_test.clicked.connect(self.test_connection)
        
        self.btn_save = QPushButton("Lưu cấu hình")
        self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_config)
        
        btn_layout.addWidget(self.btn_test)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def load_current_env(self):
        load_dotenv(self.env_path)
        self.txt_host.setText(os.getenv("DB_HOST", "localhost"))
        self.txt_port.setText(os.getenv("DB_PORT", ""))
        self.txt_user.setText(os.getenv("DB_USER", ""))
        self.txt_pass.setText(os.getenv("DB_PASS", ""))
        self.txt_dbname.setText(os.getenv("DB_NAME", "jewelry_pos"))

    def test_connection(self):
        h = self.txt_host.text().strip()
        p = self.txt_port.text().strip()
        u = self.txt_user.text().strip()
        pw = self.txt_pass.text()
        
        ok, msg = check_db_connection(h, p, u, pw)
        if ok:
            QMessageBox.information(self, "Thành công", msg)
        else:
            QMessageBox.warning(self, "Thất bại", msg)

    def save_config(self):
        h = self.txt_host.text().strip()
        p = self.txt_port.text().strip()
        u = self.txt_user.text().strip()
        pw = self.txt_pass.text()
        db = self.txt_dbname.text().strip()
        
        if not db:
            QMessageBox.warning(self, "Lỗi", "Tên Database không được để trống!")
            return
            
        ok, msg = check_db_connection(h, p, u, pw)
        if not ok:
            ans = QMessageBox.question(self, "Cảnh báo", "Kết nối test thất bại! Bạn có chắc chắn muốn lưu?", QMessageBox.Yes | QMessageBox.No)
            if ans == QMessageBox.No:
                return

        set_key(self.env_path, "DB_HOST", h)
        set_key(self.env_path, "DB_PORT", p)
        set_key(self.env_path, "DB_USER", u)
        set_key(self.env_path, "DB_PASS", pw)
        set_key(self.env_path, "DB_NAME", db)
        
        os.environ["DB_HOST"] = h
        os.environ["DB_PORT"] = p
        os.environ["DB_USER"] = u
        os.environ["DB_PASS"] = pw
        os.environ["DB_NAME"] = db
        
        self.success = True
        QMessageBox.information(self, "Thành công", "Đã lưu cấu hình!")
        self.accept()

def verify_and_setup_config():
    data_folder = get_data_folder()
    
    # Kịch bản 1: Chưa chọn folder (lần đầu tiên) hoặc folder không tồn tại
    if not data_folder or not os.path.exists(data_folder):
        folder_dialog = SelectFolderDialog()
        if folder_dialog.exec_():
            data_folder = folder_dialog.selected_folder
            save_data_folder(data_folder)
        else:
            # User tắt dialog chọn folder => Thoát
            return False

    env_path = os.path.join(data_folder, '.env')
    
    # Tạo file .env nếu chưa có
    init_env_file(env_path)
    
    # Load thử cấu hình
    load_dotenv(env_path)
    h = os.getenv("DB_HOST", "")
    p = os.getenv("DB_PORT", "")
    u = os.getenv("DB_USER", "")
    pw = os.getenv("DB_PASS", "")
    
    ok, msg = check_db_connection(h, p, u, pw)
    if not ok:
        # Kịch bản 2: Thông tin sai => hiện popup config db
        db_dialog = DatabaseConfigDialog(env_path)
        if db_dialog.exec_():
            return db_dialog.success
        return False
    return True
