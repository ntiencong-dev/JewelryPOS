from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
)
from src.ui.pos_view import POSView
from src.ui.inventory_view import InventoryView
from src.ui.customer_view import CustomerView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Quản lý Bán hàng Trang sức - Jewelry POS")
        self.resize(1200, 700)  # Kích thước mặc định rộng rãi cho app Desktop
        self.init_ui()

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
