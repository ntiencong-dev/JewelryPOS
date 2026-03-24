from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QMenuBar, QMenu, QAction, QFileDialog, QMessageBox
)
from src.ui.pos_view import POSView
from src.ui.inventory_view import InventoryView
from src.ui.customer_view import CustomerView
from src.utils.backup_manager import export_database_to_json, restore_database_from_json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý Bán hàng Trang sức - Jewelry POS")
        self.resize(1200, 700) 
        self.init_ui()
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        backup_menu = menubar.addMenu("Dữ Liệu")

        export_action = QAction("Xuất Dữ Liệu (Backup)", self)
        export_action.triggered.connect(self.export_data)
        backup_menu.addAction(export_action)

        import_action = QAction("Nhập Dữ Liệu (Restore)", self)
        import_action.triggered.connect(self.import_data)
        backup_menu.addAction(import_action)

    def export_data(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Lưu file Backup", "jewelry_backup.json", "JSON Files (*.json)")
        if filepath:
            success, msg = export_database_to_json(filepath)
            if success:
                QMessageBox.information(self, "Thành công", msg)
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def import_data(self):
        ans = QMessageBox.warning(self, "Cảnh báo", "Việc phục hồi dữ liệu sẽ GHI ĐÈ toàn bộ dữ liệu hiện tại.\nBạn có chắc chắn muốn tiếp tục?", QMessageBox.Yes | QMessageBox.No)
        if ans == QMessageBox.No:
            return
            
        filepath, _ = QFileDialog.getOpenFileName(self, "Chọn file Backup", "", "JSON Files (*.json)")
        if filepath:
            success, msg = restore_database_from_json(filepath)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                # Tải lại data trên giao diện
                self.tab_inventory.load_data()
                self.tab_customers.load_data()
                self.tab_pos.clear_cart()
            else:
                QMessageBox.critical(self, "Lỗi", msg)

    def init_ui(self):
        # Tạo Widget chính chứa các Tabs (Tab widget)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Màn hình bán hàng POS
        self.tab_pos = POSView()
        self.tabs.addTab(self.tab_pos, "Bán Hàng (POS)")

        # Tab 2: Quản lý Kho Hàng
        self.tab_inventory = InventoryView()
        self.tabs.addTab(self.tab_inventory, "Quản lý Kho")

        # Tab 3: Khách hàng & Công nợ
        self.tab_customers = CustomerView()
        self.tabs.addTab(self.tab_customers, "Khách hàng")

    def _setup_placeholder_tab(self, widget, text):
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setStyleSheet("font-size: 20px; color: gray;")
        layout.addWidget(label)
        widget.setLayout(layout)
