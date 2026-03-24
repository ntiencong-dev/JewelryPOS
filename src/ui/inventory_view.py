from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QDialog, QFormLayout, QComboBox, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer
import uuid # Dùng tạo mã vạch tự động
from src.controllers.product_controller import ProductController

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.mode = "edit" if product_data else "add"
        self.action_type = None # "save", "update", "delete"
        
        title = "Cập nhật Sản Phẩm" if self.mode == "edit" else "Thêm Sản Phẩm Mới"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Để trống sẽ tự động sinh mã")
        self.txt_name = QLineEdit()
        
        self.cb_unit = QComboBox()
        self.cb_unit.addItems(["Chỉ", "Phân", "Ly", "Gram", "Cái", "Sợi", "Đôi"])
        
        self.txt_cost_price = QLineEdit("0")
        self.txt_unit_price = QLineEdit("0")
        self.txt_stock = QLineEdit("0")

        form_layout.addRow("Mã vạch (SKU):", self.txt_barcode)
        form_layout.addRow("Tên sản phẩm (*):", self.txt_name)
        form_layout.addRow("Đơn vị tính:", self.cb_unit)
        form_layout.addRow("Giá vốn (VNĐ):", self.txt_cost_price)
        form_layout.addRow("Giá bán lẻ (VNĐ):", self.txt_unit_price)
        form_layout.addRow("Tồn kho hiện tại:", self.txt_stock)

        layout.addLayout(form_layout)
        
        # Load thông tin nếu là edit mode
        if self.mode == "edit" and self.product_data:
            self.txt_barcode.setText(self.product_data.get("barcode", ""))
            self.txt_barcode.setReadOnly(True) # Mã vạch thường không cho sửa
            self.txt_name.setText(self.product_data.get("name", ""))
            self.cb_unit.setCurrentText(self.product_data.get("unit", "Chỉ"))
            self.txt_cost_price.setText(self.product_data.get("cost_price", "0"))
            self.txt_unit_price.setText(self.product_data.get("unit_price", "0"))
            self.txt_stock.setText(self.product_data.get("stock", "0"))

        # Nút bấm Lưu / Cập nhật / Xóa / Hủy
        btn_layout = QHBoxLayout()
        
        if self.mode == "add":
            self.btn_save = QPushButton("Lưu thông tin")
            self.btn_save.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
            self.btn_save.clicked.connect(self.on_save)
            btn_layout.addWidget(self.btn_save)
        else:
            self.btn_update = QPushButton("Cập nhật")
            self.btn_update.setStyleSheet("background-color: #ffc107; font-weight: bold; padding: 6px;")
            self.btn_update.clicked.connect(self.on_update)
            
            self.btn_delete = QPushButton("Xóa")
            self.btn_delete.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 6px;")
            self.btn_delete.clicked.connect(self.on_delete)
            
            btn_layout.addWidget(self.btn_update)
            btn_layout.addWidget(self.btn_delete)

        self.btn_cancel = QPushButton("Hủy bỏ")
        self.btn_cancel.setStyleSheet("padding: 6px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_save(self):
        self.action_type = "save"
        self.accept()
        
    def on_update(self):
        # Yêu cầu xác nhận cập nhật
        reply = QMessageBox.question(self, 'Xác nhận cập nhật', 'Bạn có chắc muốn cập nhật thông tin sản phẩm này?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.action_type = "update"
            self.accept()
            
    def on_delete(self):
        # Yêu cầu xác nhận xóa
        reply = QMessageBox.question(self, 'Xác nhận xóa', 'Bạn có chắc chắn muốn xóa sản phẩm này?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.action_type = "delete"
            self.accept()

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Cấu hình timer để hoãn tìm kiếm (debounce 1.5s)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_data)

    def on_search_text_changed(self):
        # Khi sửa text thì timer được reset về 1500 ms (1.5 giây)
        self.search_timer.start(1500)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # ==========================================
        # 1. Thanh điều khiển Top (Tìm kiếm & Thêm mới)
        # ==========================================
        top_panel = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm kiếm theo mã vạch SP, tên sản phẩm...")
        self.txt_search.setMinimumHeight(35)
        
        self.btn_search = QPushButton("🔍 Tìm kiếm")
        self.btn_search.setMinimumHeight(35)
        self.btn_search.clicked.connect(self.search_now)
        self.txt_search.returnPressed.connect(self.search_now)
        self.txt_search.textChanged.connect(self.on_search_text_changed)

        self.btn_add_product = QPushButton("➕ Thêm Sản Phẩm Mới")
        self.btn_add_product.setMinimumHeight(35)
        self.btn_add_product.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        self.btn_add_product.clicked.connect(self.show_add_dialog)

        self.btn_print_barcode = QPushButton("🖨️ In Tem Mã Vạch")
        self.btn_print_barcode.setMinimumHeight(35)
        self.btn_print_barcode.setStyleSheet("background-color: #ffc107; font-weight: bold;")
        
        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_refresh.setMinimumHeight(35)
        self.btn_refresh.clicked.connect(self.load_data)

        top_panel.addWidget(QLabel("Tra cứu:"))
        top_panel.addWidget(self.txt_search, stretch=1)
        top_panel.addWidget(self.btn_search)
        top_panel.addWidget(self.btn_add_product)
        top_panel.addWidget(self.btn_print_barcode)
        top_panel.addWidget(self.btn_refresh)

        layout.addLayout(top_panel)

        # ==========================================
        # 2. Bảng Danh sách Sản phẩm
        # ==========================================
        self.table_inventory = QTableWidget(0, 6)
        self.table_inventory.setHorizontalHeaderLabels([
            "Mã vạch", "Tên sản phẩm", "ĐVT", "Giá vốn", 
            "Giá bán", "Tồn kho"
        ])
        
        # Thiết lập bảng không cho chỉ sửa trực tiếp và bắt sự kiện click đúp
        self.table_inventory.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_inventory.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_inventory.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Căn chỉnh để Tên sản phẩm co giãn chiếm chỗ trống
        header = self.table_inventory.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        layout.addWidget(self.table_inventory)
        
        # Hiển thị dữ liệu thực tế từ Database
        self.load_data()

    def on_item_double_clicked(self, item):
        row = item.row()
        product_data = {
            "barcode": self.table_inventory.item(row, 0).text(),
            "name": self.table_inventory.item(row, 1).text(),
            "unit": self.table_inventory.item(row, 2).text(),
            "cost_price": self.table_inventory.item(row, 3).text(),
            "unit_price": self.table_inventory.item(row, 4).text(),
            "stock": self.table_inventory.item(row, 5).text(),
        }
        
        dialog = ProductDialog(self, product_data=product_data)
        if dialog.exec_():
            if dialog.action_type == "update":
                update_payload = {
                    "name": dialog.txt_name.text().strip(),
                    "unit": dialog.cb_unit.currentText(),
                    "cost_price": dialog.txt_cost_price.text().strip().replace(',', ''),
                    "unit_price": dialog.txt_unit_price.text().strip().replace(',', ''),
                    "stock": dialog.txt_stock.text().strip()
                }
                success, msg = ProductController.update_product(product_data["barcode"], update_payload)
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.load_data()  # Reload từ DB cho chắc chắn
                else:
                    QMessageBox.warning(self, "Lỗi", msg)
                    
            elif dialog.action_type == "delete":
                success, msg = ProductController.delete_product(product_data["barcode"])
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Lỗi", msg)

    def show_add_dialog(self):
        """Hiển thị cửa sổ popup Thêm sản phẩm mới"""
        dialog = ProductDialog(self)
        if dialog.exec_(): # Nếu người dùng ấn 'Lưu thông tin' và pass
            name = dialog.txt_name.text().strip()
            barcode = dialog.txt_barcode.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Lỗi Nhập Liệu", "Tên sản phẩm không được để trống!")
                return
            
            if not barcode:
                barcode = f"SKU-{str(uuid.uuid4())[:8].upper()}"  # Sinh tự động
                
            product_data = {
                "barcode": barcode,
                "name": name,
                "unit": dialog.cb_unit.currentText(),
                "cost_price": dialog.txt_cost_price.text().strip().replace(',', ''),
                "unit_price": dialog.txt_unit_price.text().strip().replace(',', ''),
                "stock": dialog.txt_stock.text().strip()
            }
            
            success, msg = ProductController.add_product(product_data)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data()  # Reload lại bảng
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def search_now(self):
        """Hủy bộ đếm và tìm ngay lập tức khi nhấn Enter hoặc nút Tìm"""
        self.search_timer.stop()
        self.load_data()

    def load_data(self):
        """Tải dữ liệu thật từ Controller"""
        keyword = self.txt_search.text().strip()
        data = ProductController.get_all_products(keyword)
        
        self.table_inventory.setRowCount(0) # Clear bảng
        CONFIG_MIN_STOCK = 5 # Hoặc bóc từ db sau này
        
        for row_idx, item in enumerate(data):
            self.table_inventory.insertRow(row_idx)
            
            self.table_inventory.setItem(row_idx, 0, QTableWidgetItem(item['barcode']))
            self.table_inventory.setItem(row_idx, 1, QTableWidgetItem(item['name']))
            self.table_inventory.setItem(row_idx, 2, QTableWidgetItem(item['unit']))
            self.table_inventory.setItem(row_idx, 3, QTableWidgetItem(f"{int(item['cost_price']):,}"))
            self.table_inventory.setItem(row_idx, 4, QTableWidgetItem(f"{int(item['unit_price']):,}"))
            
            stock_val = item['stock']
            stock_item = QTableWidgetItem(stock_val)
            if int(stock_val) < CONFIG_MIN_STOCK:
                stock_item.setBackground(Qt.red)
                stock_item.setForeground(Qt.white)
                stock_item.setToolTip("Cảnh báo: Sản phẩm sắp hết!")
                
            self.table_inventory.setItem(row_idx, 5, stock_item)