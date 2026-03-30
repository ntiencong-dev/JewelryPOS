from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QComboBox, QMessageBox, QAbstractItemView, QTextBrowser
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import uuid # Dùng tạo mã vạch tự động
import base64
from io import BytesIO
from src.controllers.product_controller import ProductController

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.mode = "edit" if product_data else "add"
        self.action_type = None 
        
        title = "Cập nhật Sản Phẩm" if self.mode == "edit" else "Thêm Sản Phẩm Mới"
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Để trống sẽ tự động sinh mã")
        self.txt_name = QLineEdit()
        
        self.cb_unit = QComboBox()
        # Đã thêm ĐVT "Cân"
        self.cb_unit.addItems(["Chỉ", "Phân", "Ly", "Gram", "Cái", "Sợi", "Đôi", "Cân"]) 
        
        # Các field mới cấu thành Giá vốn
        self.txt_weight = QLineEdit("0")
        self.txt_base_price = QLineEdit("0")
        self.txt_labor_cost = QLineEdit("0")
        self.txt_stone_cost = QLineEdit("0")
        
        # Giá vốn khóa lại, chỉ hiển thị kết quả tính
        self.txt_cost_price = QLineEdit("0")
        self.txt_cost_price.setReadOnly(True)
        self.txt_cost_price.setStyleSheet("background-color: #e9ecef; font-weight: bold;")
        
        self.txt_unit_price = QLineEdit("0")
        self.txt_stock = QLineEdit("0")
        
        self.txt_note = QLineEdit()
        self.txt_note.setPlaceholderText("Ghi chú nội bộ...")

        form_layout.addRow("Mã vạch (SKU):", self.txt_barcode)
        form_layout.addRow("Tên sản phẩm (*):", self.txt_name)
        form_layout.addRow("Đơn vị tính:", self.cb_unit)
        form_layout.addRow("Khối lượng:", self.txt_weight)
        form_layout.addRow("Đơn giá (vật tư):", self.txt_base_price)
        form_layout.addRow("Tiền công:", self.txt_labor_cost)
        form_layout.addRow("Tiền hột:", self.txt_stone_cost)
        form_layout.addRow("GÍA VỐN (Tự tính):", self.txt_cost_price)
        form_layout.addRow("Giá bán lẻ (VNĐ):", self.txt_unit_price)
        form_layout.addRow("Tồn kho hiện tại:", self.txt_stock)
        form_layout.addRow("Ghi chú:", self.txt_note)

        # Bắt sự kiện gõ chữ để tự động tính Giá vốn
        self.txt_weight.textChanged.connect(lambda: self.format_money_input(self.txt_weight))
        self.txt_base_price.textChanged.connect(lambda: self.format_money_input(self.txt_base_price))
        self.txt_labor_cost.textChanged.connect(lambda: self.format_money_input(self.txt_labor_cost))
        self.txt_stone_cost.textChanged.connect(lambda: self.format_money_input(self.txt_stone_cost))
        self.txt_unit_price.textChanged.connect(lambda: self.format_money_input(self.txt_unit_price))
        layout.addLayout(form_layout)
        
        # Load thông tin nếu là edit mode
        if self.mode == "edit" and self.product_data:
            self.txt_barcode.setText(self.product_data.get("barcode", ""))
            self.txt_barcode.setReadOnly(True) 
            self.txt_name.setText(self.product_data.get("name", ""))
            self.cb_unit.setCurrentText(self.product_data.get("unit", "Chỉ"))
            
            self.txt_weight.setText(self.product_data.get("weight", "0"))
            self.txt_base_price.setText(self.product_data.get("base_price", "0"))
            self.txt_labor_cost.setText(self.product_data.get("labor_cost", "0"))
            self.txt_stone_cost.setText(self.product_data.get("stone_cost", "0"))
            
            self.txt_cost_price.setText(self.product_data.get("cost_price", "0"))
            self.txt_unit_price.setText(self.product_data.get("unit_price", "0"))
            self.txt_stock.setText(self.product_data.get("stock", "0"))
            self.txt_note.setText(self.product_data.get("note", ""))

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

    def calc_cost(self):
        """Hàm tự động tính Giá Vốn = Khối lượng * Đơn giá + Tiền Công + Tiền hột"""
        try:
            w = float(self.txt_weight.text().replace(',', '') or 0)
            b = float(self.txt_base_price.text().replace(',', '') or 0)
            l = float(self.txt_labor_cost.text().replace(',', '') or 0)
            s = float(self.txt_stone_cost.text().replace(',', '') or 0)
            t = str(self.cb_unit.currentText() or "Chỉ")
            if t == "Cân":
                cost = b + l + s
            else:
                cost = (w * b) + l + s
            self.txt_cost_price.setText(f"{cost:,.0f}")
        except:
            self.txt_cost_price.setText("0")

    def format_money_input(self, line_edit):
        """Hàm format số tiền, tự động thêm dấu phẩy hàng nghìn"""
        text = line_edit.text()
        # Loại bỏ ký tự không phải số
        raw = "".join(filter(str.isdigit, text))
        if not raw:
            raw = "0"
            
        formatted = f"{int(raw):,}"
        if text != formatted:
            # Lưu lại vị trí con trỏ
            pos = line_edit.cursorPosition()
            # Đếm số chữ số trước con trỏ
            char_count_before = len(''.join(filter(str.isdigit, text[:pos])))
            
            line_edit.blockSignals(True)
            line_edit.setText(formatted)
            line_edit.blockSignals(False)
            
            # Tính lại vị trí con trỏ mới
            new_pos = 0
            count = 0
            for i, char in enumerate(formatted):
                if count == char_count_before:
                    new_pos = i
                    break
                if char.isdigit():
                    count += 1
            else:
                new_pos = len(formatted)
                
            line_edit.setCursorPosition(new_pos)
            
        # Tự động tính lại giá vốn mỗi khi có một ô tiền tệ thay đổi format
        self.calc_cost()

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
        self.btn_print_barcode.clicked.connect(self.print_barcode_for_selected)

        self.btn_delete_product = QPushButton("🗑️ Xóa Sản Phẩm")
        self.btn_delete_product.setMinimumHeight(35)
        self.btn_delete_product.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.btn_delete_product.clicked.connect(self.delete_selected_product)

        self.btn_view_note = QPushButton("📝 Xem Ghi Chú")
        self.btn_view_note.setMinimumHeight(35)
        self.btn_view_note.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        self.btn_view_note.clicked.connect(self.view_product_note)

        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_refresh.setMinimumHeight(35)
        self.btn_refresh.clicked.connect(self.load_data)

        top_panel.addWidget(QLabel("Tra cứu:"))
        top_panel.addWidget(self.txt_search, stretch=1)
        top_panel.addWidget(self.btn_search)
        top_panel.addWidget(self.btn_add_product)
        top_panel.addWidget(self.btn_print_barcode)
        top_panel.addWidget(self.btn_view_note)
        top_panel.addWidget(self.btn_delete_product)
        top_panel.addWidget(self.btn_refresh)

        layout.addLayout(top_panel)

        # ==========================================
        # 2. Bảng Danh sách Sản phẩm
        # ==========================================
        self.table_inventory = QTableWidget(0, 11)
        self.table_inventory.setHorizontalHeaderLabels([
        "Mã vạch", "Tên sản phẩm", "ĐVT", "Khối lượng", "Đơn giá", 
        "Tiền công", "Tiền hột", "Giá vốn", "Giá bán", "Tồn kho", "Ghi chú"
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
        def get_text(col):
            cell = self.table_inventory.item(row, col)
            return cell.text() if cell else ""
        product_data = {
            "barcode": get_text(0),
            "name": get_text(1),
            "unit": get_text(2),
            "weight": get_text(3),
            "base_price": get_text(4),
            "labor_cost": get_text(5),
            "stone_cost": get_text(6),
            "cost_price": get_text(7),
            "unit_price": get_text(8),
            "stock": get_text(9),
            "note": get_text(10),
        }
        
        dialog = ProductDialog(self, product_data=product_data)
        if dialog.exec_():
            if dialog.action_type == "update":
                update_payload = {
                    "name": dialog.txt_name.text().strip(),
                    "unit": dialog.cb_unit.currentText(),
                    "weight": dialog.txt_weight.text().strip().replace(',', ''),
                    "base_price": dialog.txt_base_price.text().strip().replace(',', ''),
                    "labor_cost": dialog.txt_labor_cost.text().strip().replace(',', ''),
                    "stone_cost": dialog.txt_stone_cost.text().strip().replace(',', ''),
                    "cost_price": dialog.txt_cost_price.text().strip().replace(',', ''),
                    "unit_price": dialog.txt_unit_price.text().strip().replace(',', ''),
                    "stock": dialog.txt_stock.text().strip(),
                    "note": dialog.txt_note.text().strip()
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
                
            # --- BẮT ĐẦU ĐOẠN CẦN SỬA ---
            # Gom ĐẦY ĐỦ các trường dữ liệu mới từ giao diện
            product_data = {
                "barcode": barcode,
                "name": name,
                "unit": dialog.cb_unit.currentText(),
                "weight": dialog.txt_weight.text().strip().replace(',', ''),
                "base_price": dialog.txt_base_price.text().strip().replace(',', ''),
                "labor_cost": dialog.txt_labor_cost.text().strip().replace(',', ''),
                "stone_cost": dialog.txt_stone_cost.text().strip().replace(',', ''),
                "cost_price": dialog.txt_cost_price.text().strip().replace(',', ''),
                "unit_price": dialog.txt_unit_price.text().strip().replace(',', ''),
                "stock": dialog.txt_stock.text().strip(),
                "note": dialog.txt_note.text().strip()
            }
            # --- KẾT THÚC ĐOẠN CẦN SỬA ---
            
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

    def print_barcode_for_selected(self):
        current_row = self.table_inventory.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn một sản phẩm trong bảng để in mã vạch!")
            return

        barcode = self.table_inventory.item(current_row, 0).text()
        name = self.table_inventory.item(current_row, 1).text()
        price = self.table_inventory.item(current_row, 4).text()
        
        try:
            import barcode as pybarcode
            from barcode.writer import ImageWriter
            from io import BytesIO
            import base64
        except ImportError:
            QMessageBox.warning(self, "Thiếu thư viện", "Vui lòng cài đặt thư viện 'python-barcode' và 'pillow' để sử dụng tính năng này!\n\nLệnh: pip install python-barcode pillow")
            return

        from PyQt5.QtWidgets import QSpinBox, QDialog, QFormLayout, QVBoxLayout, QPushButton, QTextBrowser
        
        # Tạo Dialog hỏi số lượng in
        config_dlg = QDialog(self)
        config_dlg.setWindowTitle("Cấu hình in Tem Mã Vạch")
        cf_layout = QFormLayout(config_dlg)
        
        spin_total = QSpinBox()
        spin_total.setRange(1, 1000)
        spin_total.setValue(10) # Số lượng tem tổng cộng
        
        spin_per_row = QSpinBox()
        spin_per_row.setRange(1, 5)
        spin_per_row.setValue(2) # Cho phép người dùng chọn in mấy tem 1 hàng (thường là 2 hoặc 3 cho giấy 80mm)
        
        cf_layout.addRow("Tổng số lượng tem:", spin_total)
        cf_layout.addRow("Số tem trên một hàng:", spin_per_row)
        
        btn_ok = QPushButton("Tạo Preview")
        btn_ok.clicked.connect(config_dlg.accept)
        cf_layout.addRow(btn_ok)
        
        if config_dlg.exec_() != QDialog.Accepted:
            return
            
        total_tags = spin_total.value()
        per_row = spin_per_row.value()

        # Tạo mã vạch (Tắt text mặc định của thư viện để lát ta tự vẽ text cho đẹp)
        try:
            CODE = pybarcode.get_barcode_class('code128')
            rv = BytesIO()
            code128 = CODE(barcode, writer=ImageWriter())
            code128.write(rv, options={'module_height': 8.0, 'module_width': 0.3, 'quiet_zone': 1.0, 'write_text': False})
            
            # Chuyển image buffer sang base64 để làm màn hình Preview bằng HTML
            img_base64 = base64.b64encode(rv.getvalue()).decode('utf-8')
            
            html = f"""
            <html>
            <head>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; color: black; }}
                table {{ width: 100%; border-collapse: collapse; margin: 0; padding: 0; }}
                td {{ text-align: center; padding: 5px; vertical-align: top; width: {100.0/per_row}%; border: 1px dotted #ccc; }}
                .tag {{ display: inline-block; overflow: hidden; max-width: 100%; }}
                .product-name {{ font-size: 10pt; font-weight: bold; margin-bottom: 2px; }}
                .barcode-text {{ font-size: 8pt; letter-spacing: 2px; margin-bottom: 2px; }}
                .price {{ font-size: 11pt; font-weight: bold; margin-top: 2px; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
            </head>
            <body>
            <table>
            <tr>
            """
            
            for i in range(total_tags):
                if i > 0 and i % per_row == 0:
                    html += "</tr><tr>"
                
                html += f"""
                    <td>
                        <div class="tag">
                            <div class="product-name">{name}</div>
                            <img src="data:image/png;base64,{img_base64}" />
                            <div class="barcode-text">{barcode}</div>
                            <div class="price">{price} đ</div>
                        </div>
                    </td>
                """
                
            remainder = total_tags % per_row
            if remainder > 0:
                for _ in range(per_row - remainder):
                    html += "<td></td>"
            html += "</tr></table></body></html>"
            
            # Hiển thị Preview Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Preview Tem Mã Vạch")
            dialog.resize(600, 700)
            layout = QVBoxLayout(dialog)
            
            viewer = QTextBrowser()
            viewer.setHtml(html)
            layout.addWidget(viewer)
            
            btn_print = QPushButton("In Tem (Đẩy Lệnh RAW)")
            btn_print.setStyleSheet("background-color: #007bff; color: white; padding: 12px; font-size: 16px; font-weight: bold;")
            
            # HÀM IN ẤN CHUẨN CÔNG NGHIỆP ESC/POS QUA WIN32PRINT
            def execute_print():
                from PyQt5.QtGui import QImage, QPainter, QFont, QPen
                from PyQt5.QtCore import Qt, QRect
                import win32print
                
                # Chiều ngang tiêu chuẩn của máy in 80mm là khoảng 576 pixel
                printer_width_px = 576
                cell_width = printer_width_px // per_row
                cell_height = 135  # Khoảng cách chiều cao mỗi con tem
                
                rows = (total_tags + per_row - 1) // per_row
                total_height_px = rows * cell_height
                
                # 1. Tự động dàn trang bằng toán học (Vẽ lên QImage)
                img = QImage(printer_width_px, total_height_px, QImage.Format_Mono)
                img.fill(1) # Đổ nền trắng (1 = Trắng trong hệ Format_Mono)
                
                painter = QPainter(img)
                painter.setPen(QPen(Qt.black))
                
                # Set font cho Tiếng Việt (QPainter tự động render tiếng Việt có dấu cực nét)
                font_name = QFont("Arial", 16, QFont.Bold)
                font_bc_text = QFont("Arial", 12, QFont.Normal)
                font_price = QFont("Arial", 18, QFont.Bold)
                
                # Load ảnh Barcode thô
                bc_img = QImage()
                bc_img.loadFromData(rv.getvalue())
                
                # Tính toán kích thước barcode thu nhỏ để vừa với ô
                # Dành ra 20px biên. Chiều cao khoảng 60px
                target_bc_width = cell_width - 20
                bc_scaled = bc_img.scaled(target_bc_width, 60, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                
                # Vẽ từng con tem vào vị trí
                for i in range(total_tags):
                    row_idx = i // per_row
                    col_idx = i % per_row
                    x = col_idx * cell_width
                    y = row_idx * cell_height
                    
                    # Cắt ngắn tên nếu quá dài để không bị tràn
                    short_name = name if len(name) < 20 else name[:18] + ".."
                    
                    # Vẽ Tên Sản phẩm
                    painter.setFont(font_name)
                    painter.drawText(QRect(x, y + 0, cell_width, 30), Qt.AlignCenter, short_name)
                    
                    # Vẽ Mã vạch (Hình ảnh)
                    bc_x = x + (cell_width - bc_scaled.width()) // 2
                    bc_y = y + 30
                    painter.drawImage(bc_x, bc_y, bc_scaled)
                    
                    # Vẽ số mã vạch ở dưới mã vạch
                    painter.setFont(font_bc_text)
                    painter.drawText(QRect(x, bc_y + 60, cell_width, 20), Qt.AlignCenter, barcode)
                    
                    # Vẽ Giá tiền
                    painter.setFont(font_price)
                    painter.drawText(QRect(x, y + 105, cell_width, 30), Qt.AlignCenter, f"{price} đ")
                    
                painter.end()
                
                # 2. Chuyển đổi QImage thành mảng lệnh ESC/POS Raster (GS v 0)
                bytes_width = (printer_width_px + 7) // 8
                xL = bytes_width % 256
                xH = bytes_width // 256
                yL = total_height_px % 256
                yH = total_height_px // 256
                
                ESC_INIT = b'\x1B\x40'
                GS_V_0 = b'\x1D\x76\x30\x00' + bytes([xL, xH, yL, yH])
                
                raster_data = bytearray()
                # Quét từng dòng điểm ảnh (pixel)
                for y_idx in range(total_height_px):
                    scanline_str = img.constScanLine(y_idx).asstring(img.bytesPerLine())
                    line_data = bytearray(scanline_str[:bytes_width])
                    for j in range(len(line_data)):
                        # Đảo bit: Vì hệ QImage nền trắng là 1 mực đen là 0, 
                        # nhưng máy in nhiệt quy định mực đen là 1, nên ta dùng phép ~ (NOT)
                        line_data[j] = ~line_data[j] & 0xFF
                    raster_data.extend(line_data)
                    
                CUT_PAPER = b'\x1D\x56\x42\x00'
                
                # Ghép toàn bộ dữ liệu (cộng thêm vài khoảng trắng cuối để đẩy giấy qua khỏi răng cưa)
                raw_data = ESC_INIT + GS_V_0 + raster_data + b"\n\n\n\n\n" + CUT_PAPER
                
                # 3. Mở kết nối Spooler bắn thẳng xuống máy in
                try:
                    # Chú ý: Đảm bảo tên máy in này TRÙNG KHỚP với tên bạn đang dùng bên pos_view.py
                    printer_name = "HPRT" 
                    hPrinter = win32print.OpenPrinter(printer_name)
                    try:
                        hJob = win32print.StartDocPrinter(hPrinter, 1, ("Barcode Print", None, "RAW"))
                        win32print.StartPagePrinter(hPrinter)
                        win32print.WritePrinter(hPrinter, raw_data)
                        win32print.EndPagePrinter(hPrinter)
                        win32print.EndDocPrinter(hPrinter)
                    finally:
                        win32print.ClosePrinter(hPrinter)
                        
                    dialog.accept()
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi in ấn", f"Không thể gửi lệnh RAW tới Windows Spooler:\n{str(e)}")

            btn_print.clicked.connect(execute_print)
            layout.addWidget(btn_print)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi tạo tem", f"Đã xảy ra lỗi: {str(e)}")

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
            self.table_inventory.setItem(row_idx, 3, QTableWidgetItem(item['weight']))
            self.table_inventory.setItem(row_idx, 4, QTableWidgetItem(f"{int(item['base_price']):,}"))
            self.table_inventory.setItem(row_idx, 5, QTableWidgetItem(f"{int(item['labor_cost']):,}"))
            self.table_inventory.setItem(row_idx, 6, QTableWidgetItem(f"{int(item['stone_cost']):,}"))
            self.table_inventory.setItem(row_idx, 7, QTableWidgetItem(f"{int(item['cost_price']):,}"))
            self.table_inventory.setItem(row_idx, 8, QTableWidgetItem(f"{int(float(item['unit_price'])):,}"))
            
            stock_val = item['stock']
            stock_item = QTableWidgetItem(stock_val)
            if int(float(stock_val)) < CONFIG_MIN_STOCK:
                stock_item.setBackground(Qt.red)
                stock_item.setForeground(Qt.white)
                stock_item.setToolTip("Cảnh báo: Sản phẩm sắp hết!")

            self.table_inventory.setItem(row_idx, 9, stock_item)
            self.table_inventory.setItem(row_idx, 10, QTableWidgetItem(item['note']))

    def delete_selected_product(self):
        """Hàm xử lý khi bấm nút Xóa Sản Phẩm ở màn hình chính"""
        current_row = self.table_inventory.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng click chọn một sản phẩm trong bảng để xóa!")
            return

        barcode = self.table_inventory.item(current_row, 0).text()
        name = self.table_inventory.item(current_row, 1).text()

        reply = QMessageBox.question(self, 'Xác nhận xóa', f'Bạn có chắc chắn muốn xóa sản phẩm:\n{name} ({barcode})?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, msg = ProductController.delete_product(barcode)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data() # Cập nhật lại bảng sau khi xóa (hoặc ẩn)
            else:
                QMessageBox.warning(self, "Lỗi", msg)

    def view_product_note(self):
        """Hàm mở popup đọc toàn bộ nội dung ghi chú của sản phẩm"""
        current_row = self.table_inventory.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn một sản phẩm trong bảng để xem ghi chú!")
            return

        # Lấy tên sản phẩm ở cột 1 và ghi chú ở cột 10
        name = self.table_inventory.item(current_row, 1).text()
        
        note_item = self.table_inventory.item(current_row, 10)
        note_text = note_item.text() if note_item else ""

        if not note_text.strip():
            QMessageBox.information(self, "Ghi chú trống", f"Sản phẩm '{name}' hiện không có ghi chú nào.")
            return

        # Tạo một Dialog (Popup) riêng chỉ để đọc ghi chú
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Ghi chú: {name}")
        dlg.setMinimumSize(400, 300)
        layout = QVBoxLayout(dlg)

        # Dùng QTextBrowser để hiển thị văn bản nhiều dòng, tự động cuộn (scroll) và chỉ đọc
        txt_viewer = QTextBrowser()
        txt_viewer.setPlainText(note_text)
        txt_viewer.setStyleSheet("font-size: 15px; padding: 10px; background-color: #fdfdfd; border: 1px solid #ccc;")
        layout.addWidget(txt_viewer)

        btn_close = QPushButton("Đóng")
        btn_close.setMinimumHeight(40)
        btn_close.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; font-size: 14px;")
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)

        dlg.exec_()