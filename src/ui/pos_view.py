from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QFrame, QDialog, QMessageBox, QTextBrowser,
    QListWidget, QListWidgetItem, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import datetime
import unicodedata
import textwrap
from src.controllers.product_controller import ProductController
from src.controllers.customer_controller import CustomerController
from src.controllers.invoice_controller import InvoiceController

class CustomerSearchDialog(QDialog):
    def __init__(self, parent=None, search_kw=""):
        super().__init__(parent)
        self.setWindowTitle("Tìm kiếm Khách Hàng")
        self.setMinimumWidth(550)
        self.search_kw = search_kw
        self.selected_customer = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        self.txt_search = QLineEdit(self.search_kw)
        self.txt_search.setPlaceholderText("Nhập SĐT hoặc Tên khách hàng...")
        btn_search = QPushButton("Tìm kiếm")
        btn_search.clicked.connect(self.do_search)
        search_layout.addWidget(self.txt_search)
        search_layout.addWidget(btn_search)
        layout.addLayout(search_layout)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["SĐT", "Tên KH", "Địa chỉ", "Nợ cũ"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self.select_customer)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_select = QPushButton("Chọn Khách Hàng (Click đúp)")
        btn_select.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 5px;")
        btn_select.clicked.connect(self.select_customer)
        btn_layout.addWidget(btn_select)
        layout.addLayout(btn_layout)
        
        self.do_search()

    def do_search(self):
        kw = self.txt_search.text().strip()
        data = CustomerController.get_all_customers(kw)
        
        self.table.setRowCount(0)
        for row in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["phone"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["address"]))
            self.table.setItem(r, 3, QTableWidgetItem(f"{float(row['debt']):,}"))

    def select_customer(self):
        selected = self.table.selectedItems()
        if selected:
            r = selected[0].row()
            self.selected_customer = {
                "phone": self.table.item(r, 0).text(),
                "name": self.table.item(r, 1).text(),
                "address": self.table.item(r, 2).text(),
                "debt": self.table.item(r, 3).text(),
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn 1 dòng khách hàng!")

class ProductSearchPopup(QFrame):
    """
    Floating popup hiển thị danh sách sản phẩm matching khi người dùng gõ từ khóa.
    Popup này gắn vào parent widget và được hiển thị floating (không modal).
    """
    def __init__(self, parent_widget, target_input, on_select_callback):
        super().__init__(parent_widget, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.target_input = target_input
        self.on_select_callback = on_select_callback
        self._products = []
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QLabel("🔍 Kết quả tìm kiếm sản phẩm")
        header.setStyleSheet(
            "background-color: #1e3a5f; color: white; font-weight: bold;"
            "padding: 6px 10px; font-size: 13px;"
        )
        layout.addWidget(header)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 2px solid #1e3a5f;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 7px 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #2d6bc4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #dce8ff;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        # Footer hint
        footer = QLabel("↵ Enter chọn | Esc đóng")
        footer.setStyleSheet(
            "background-color: #f0f4ff; color: #666; padding: 4px 10px; font-size: 11px;"
            "border-top: 1px solid #ccc;"
        )
        layout.addWidget(footer)

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background: white; border: 2px solid #1e3a5f; border-radius: 4px;")

    def show_results(self, products):
        """Hiển thị popup với danh sách sản phẩm."""
        self._products = products
        self.list_widget.clear()

        if not products:
            self.hide()
            return

        for p in products:
            barcode = p.get("barcode", "")
            name = p.get("name", "")
            unit = p.get("unit", "")
            price = p.get("unit_price", p.get("price", 0))
            try:
                price_str = f"{int(float(price)):,}"
            except:
                price_str = str(price)

            item = QListWidgetItem()
            item.setText(f"  {name}")
            item.setToolTip(f"Mã: {barcode} | ĐVT: {unit} | Giá: {price_str} đ")
            # Lưu data để dùng khi chọn
            item.setData(Qt.UserRole, p)
            # Sub-text bằng cách thêm icon và thông tin phụ vào text
            item.setText(f"📦 {name}   [{unit}]   {price_str} đ")

            self.list_widget.addItem(item)

        # Tính toán kích thước popup
        visible_rows = min(len(products), 8)
        row_h = 38
        self.list_widget.setFixedHeight(visible_rows * row_h)

        self._reposition()
        self.show()
        self.raise_()

        # Chọn dòng đầu tiên
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _reposition(self):
        """Căn chỉnh popup ngay bên dưới ô input."""
        inp = self.target_input
        # Map toạ độ gốc của ô input sang toạ độ màn hình
        global_pos = inp.mapToGlobal(QPoint(0, inp.height()))
        # Map lại về toạ độ của parent widget
        parent_pos = self.parent().mapFromGlobal(global_pos)
        self.move(parent_pos)
        self.setFixedWidth(inp.width() + 120)  # Rộng hơn ô input một chút

    def select_current(self):
        """Chọn item đang được highlight."""
        item = self.list_widget.currentItem()
        if item:
            self._on_item_clicked(item)

    def move_selection(self, direction):
        """Di chuyển chọn lên/xuống trong list. direction=-1 (lên), +1 (xuống)."""
        count = self.list_widget.count()
        if count == 0:
            return
        cur = self.list_widget.currentRow()
        new_row = max(0, min(count - 1, cur + direction))
        self.list_widget.setCurrentRow(new_row)

    def _on_item_clicked(self, item):
        product = item.data(Qt.UserRole)
        self.hide()
        if self.on_select_callback and product:
            self.on_select_callback(product)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.select_current()
        elif event.key() == Qt.Key_Up:
            self.move_selection(-1)
        elif event.key() == Qt.Key_Down:
            self.move_selection(1)
        else:
            super().keyPressEvent(event)

class AddToCartDialog(QDialog):
    def __init__(self, parent=None, product_info=None):
        super().__init__(parent)
        self.product_info = product_info or {}
        self.setWindowTitle("Thêm vào đơn hàng")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.lbl_name = QLabel(self.product_info.get("name", "---"))
        self.lbl_name.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
        self.lbl_unit = QLabel(self.product_info.get("unit", "---"))
        
        self.txt_qty = QLineEdit("1")
        self.txt_price = QLineEdit(str(self.product_info.get("price", "0")))
        self.lbl_total = QLabel("0")
        self.lbl_total.setStyleSheet("font-weight: bold; color: red;")
        
        self.txt_qty.textChanged.connect(self.calc_total)
        self.txt_price.textChanged.connect(self.calc_total)
        lbl_qty_text = "Trọng lượng thực tế:" if self.product_info.get("unit") == "Cân" else "Số lượng:"
        
        form.addRow("Sản phẩm:", self.lbl_name)
        form.addRow("Đơn vị tính:", self.lbl_unit)
        form.addRow(lbl_qty_text, self.txt_qty)
        form.addRow("Số lượng:", self.txt_qty)
        form.addRow("Đơn giá:", self.txt_price)
        form.addRow("Thành tiền:", self.lbl_total)
        
        layout.addLayout(form)
        
        btn_add = QPushButton("Thêm vào giỏ hàng")
        btn_add.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 6px;")
        btn_add.clicked.connect(self.accept)
        layout.addWidget(btn_add)
        
        self.calc_total()
        
    def calc_total(self):
        try:
            qty = float(self.txt_qty.text().replace(',', '') or 0)
            price = float(self.txt_price.text().replace(',', '') or 0)
            total = qty * price
            self.lbl_total.setText(f"{total:,.0f}")
        except:
            self.lbl_total.setText("0")

class ProductSelectDialog(QDialog):
    def __init__(self, parent=None, products=[]):
        super().__init__(parent)
        self.setWindowTitle("Chọn Sản Phẩm")
        self.setMinimumWidth(550)
        self.products = products
        self.selected_product = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mã vạch", "Tên sản phẩm", "ĐVT", "Giá bán"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self.select_product)
        layout.addWidget(self.table)
        
        # Load products
        for row in self.products:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(row["barcode"]))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(row["unit"]))
            self.table.setItem(r, 3, QTableWidgetItem(f"{row['price']:,.0f}"))
            
        btn_layout = QHBoxLayout()
        btn_select = QPushButton("Chọn Sản Phẩm (Click đúp)")
        btn_select.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 5px;")
        btn_select.clicked.connect(self.select_product)
        btn_layout.addWidget(btn_select)
        layout.addLayout(btn_layout)

    def select_product(self):
        selected = self.table.selectedItems()
        if selected:
            r = selected[0].row()
            self.selected_product = self.products[r]
            self.accept()
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn 1 sản phẩm!")

class POSView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        # Popup tìm kiếm sản phẩm (floating, non-modal)
        self.search_popup = ProductSearchPopup(
            parent_widget=self,
            target_input=self.txt_barcode,
            on_select_callback=self._on_search_popup_select
        )

        # Timer debounce 300ms – sau khi người dùng ngừng gõ mới query DB
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_realtime_search)

        # Install event filter trên ô barcode để bắt phím Up/Down/Esc
        self.txt_barcode.installEventFilter(self)
        
        # Cài đặt event filter toàn cục cho tab và bảng để bắt máy quét mã vạch giống hệt kho
        self.installEventFilter(self)
        if hasattr(self, 'table_cart'):
            self.table_cart.installEventFilter(self)

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ==========================================
        # PANEL TRÁI: GIỎ HÀNG & TÌM KIẾM SẢN PHẨM
        # ==========================================
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)

        # 1. Khu vực quét mã vạch / Tìm kiếm
        search_layout = QHBoxLayout()
        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Quét mã vạch hoặc nhập tên sản phẩm, nhấn Enter...")
        self.txt_barcode.setMinimumHeight(40)
        # Bắt sự kiện nhấn Enter: nếu popup đang mở – chọn item đầu tiên; ngược lại tìm và thêm
        self.txt_barcode.returnPressed.connect(self.search_and_add_product)
        # Debounce 300ms sau mỗi lần gõ phím
        self.txt_barcode.textChanged.connect(self.on_barcode_text_changed)
        
        btn_search = QPushButton("Tìm Và Thêm")
        btn_search.setMinimumHeight(40)
        btn_search.clicked.connect(self.search_and_add_product)
        
        search_layout.addWidget(QLabel("Mã vạch (F2):"))
        search_layout.addWidget(self.txt_barcode)
        search_layout.addWidget(btn_search)
        left_layout.addLayout(search_layout)

        # 2. Bảng Giỏ hàng (Mặt hàng)
        self.table_cart = QTableWidget(0, 6)
        self.table_cart.setHorizontalHeaderLabels(["Mã SP", "Tên sản phẩm", "ĐVT", "Số lượng", "Đơn giá", "Thành tiền"])
        # Căn chỉnh kích thước cột tự động
        header = self.table_cart.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Tên SP co giãn
        left_layout.addWidget(self.table_cart)

        # ==========================================
        # PANEL PHẢI: THÔNG TIN KHÁCH HÀNG & THANH TOÁN
        # ==========================================
        right_panel = QFrame()
        right_panel.setFixedWidth(350)
        right_layout = QVBoxLayout(right_panel)

        # 1. Group Khách hàng
        group_customer = QGroupBox("Thông tin Khách Hàng")
        layout_customer = QVBoxLayout()
        
        search_cust_layout = QHBoxLayout()
        self.txt_search_cust = QLineEdit()
        self.txt_search_cust.setPlaceholderText("Nhập SĐT / Tên KH")
        self.btn_search_cust = QPushButton("Tìm khách hàng")
        self.btn_search_cust.clicked.connect(self.open_customer_search)
        
        self.btn_refresh_cust = QPushButton("🔄")
        self.btn_refresh_cust.setToolTip("Làm mới thông tin khách hàng")
        self.btn_refresh_cust.clicked.connect(self.refresh_customer_data)
        
        search_cust_layout.addWidget(self.txt_search_cust)
        search_cust_layout.addWidget(self.btn_search_cust)
        search_cust_layout.addWidget(self.btn_refresh_cust)
        layout_customer.addLayout(search_cust_layout)

        form_cust = QFormLayout()
        self.lbl_cust_name = QLabel("---")
        self.lbl_cust_phone = QLabel("---")
        self.lbl_cust_address = QLabel("")
        self.lbl_old_debt = QLabel("0 đ")
        self.lbl_old_debt.setStyleSheet("color: red; font-weight: bold;")
        
        form_cust.addRow("Tên KH:", self.lbl_cust_name)
        form_cust.addRow("Số ĐT:", self.lbl_cust_phone)
        form_cust.addRow("Nợ cũ:", self.lbl_old_debt)
        # Giấu nhãn địa chỉ, chỉ dùng để lưu trữ ngầm truyền lúc in bill
        self.lbl_cust_address.hide()
        layout_customer.addWidget(self.lbl_cust_address)
        layout_customer.addLayout(form_cust)
        
        group_customer.setLayout(layout_customer)
        right_layout.addWidget(group_customer)

        # 2. Group Thanh toán
        group_payment = QGroupBox("Thanh Toán")
        layout_payment = QFormLayout()

        self.lbl_subtotal = QLabel("0 đ")
        self.txt_discount = QLineEdit("0")
        self.txt_discount.textChanged.connect(lambda: self.format_money_input(self.txt_discount))
        
        self.lbl_total_payment = QLabel("0 đ")
        self.lbl_total_payment.setStyleSheet("color: blue; font-size: 18px; font-weight: bold;")
        
        self.txt_amount_paid = QLineEdit("0")
        self.txt_amount_paid.textChanged.connect(lambda: self.format_money_input(self.txt_amount_paid))
        
        self.lbl_change = QLabel("0 đ")
        
        self.lbl_new_debt = QLabel("0 đ")
        self.lbl_new_debt.setStyleSheet("color: red; font-weight: bold;")

        layout_payment.addRow("Tổng tiền hàng:", self.lbl_subtotal)
        layout_payment.addRow("Giảm giá (-):", self.txt_discount)
        layout_payment.addRow("Khách cần trả:", self.lbl_total_payment)
        layout_payment.addRow("Khách đưa:", self.txt_amount_paid)
        layout_payment.addRow("Tiền trả lại:", self.lbl_change)
        layout_payment.addRow("Ghi nợ mới:", self.lbl_new_debt)
        
        group_payment.setLayout(layout_payment)
        right_layout.addWidget(group_payment)

        # Khoảng trống đẩy nút xuống dưới cùng
        right_layout.addStretch()

        # 3. Nút hành động
        self.btn_checkout = QPushButton("Xác nhận Và In Bill (F12)")
        self.btn_checkout.setMinimumHeight(60)
        self.btn_checkout.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; font-weight: bold;")
        self.btn_checkout.clicked.connect(self.process_checkout)
        
        self.btn_cancel = QPushButton("Hủy đơn")
        self.btn_cancel.setMinimumHeight(40)
        self.btn_cancel.clicked.connect(self.clear_cart)

        right_layout.addWidget(self.btn_checkout)
        right_layout.addWidget(self.btn_cancel)

        # Add left and right panels to main layout
        main_layout.addWidget(left_panel, stretch=7) # Bên trái chiếm 7 phần
        main_layout.addWidget(right_panel, stretch=3) # Bên phải chiếm 3 phần

    def refresh_customer_data(self):
        cust_phone = self.lbl_cust_phone.text()
        if cust_phone and cust_phone != "---":
            data = CustomerController.get_all_customers(cust_phone)
            for row in data:
                if row["phone"] == cust_phone:
                    self.lbl_cust_name.setText(row["name"])
                    self.lbl_cust_address.setText(row["address"])
                    self.lbl_old_debt.setText(f"{int(row['debt']):,} VNĐ")
                    break
            self.update_totals()

    def open_customer_search(self):
        kw = self.txt_search_cust.text().strip()
        dialog = CustomerSearchDialog(self, search_kw=kw)
        if dialog.exec_() and dialog.selected_customer:
            cust = dialog.selected_customer
            self.lbl_cust_name.setText(cust["name"])
            self.lbl_cust_phone.setText(cust["phone"])
            self.lbl_cust_address.setText(cust["address"])
            self.lbl_old_debt.setText(f"{cust['debt']} VNĐ")
            self.txt_search_cust.setText(cust["phone"])
            self.update_totals()

    def on_barcode_text_changed(self, text):
        """Khi người dùng gõ phím, khởi động debounce 300ms để tìm kiếm và hiển thị popup."""
        if text.strip():
            self.search_timer.start(1500)  # debounce 300ms
        else:
            self.search_timer.stop()
            self.search_popup.hide()

    def eventFilter(self, obj, event):
        """Chặn phím Up/Down/Esc từ ô barcode để điều hướng popup, và tiếp nhận ký tự quét mã vạch."""
        from PyQt5.QtCore import QEvent, Qt
        from PyQt5.QtWidgets import QLineEdit, QTextEdit, QApplication
        
        if event.type() == QEvent.KeyPress:
            # 1. Đoạn xử lý điều hướng cho popup (khi con trỏ nằm ở txt_barcode)
            if obj is self.txt_barcode:
                key = event.key()
                if getattr(self, 'search_popup', None) and self.search_popup.isVisible():
                    if key == Qt.Key_Down:
                        self.search_popup.move_selection(1)
                        return True
                    elif key == Qt.Key_Up:
                        self.search_popup.move_selection(-1)
                        return True
                    elif key == Qt.Key_Escape:
                        self.search_popup.hide()
                        return True
            
            # 2. Đoạn xử lý máy quét (từ kho chuyển sang)
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, (QLineEdit, QTextEdit)):
                if focus_widget != getattr(self, 'txt_barcode', None):
                    return super().eventFilter(obj, event)
            
            if event.text().isprintable() and len(event.text()) > 0:
                if focus_widget != getattr(self, 'txt_barcode', None):
                    self.txt_barcode.setFocus()
                    self.txt_barcode.keyPressEvent(event)
                    return True

        return super().eventFilter(obj, event)

    def _do_realtime_search(self):
        """Thực hiện query DB và cập nhật popup (gọi từ timer sau debounce)."""
        kw = self.txt_barcode.text().strip()
        if not kw:
            self.search_popup.hide()
            return
        products = ProductController.get_all_products(keyword=kw)
        self.search_popup.show_results(products)

    def _on_search_popup_select(self, product):
        """Callback khi người dùng chọn một sản phẩm từ popup."""
        # Chuẩn hóa key 'price' cho AddToCartDialog
        if "unit_price" in product and "price" not in product:
            product["price"] = float(product["unit_price"])
        self.show_add_to_cart_dialog(product)

    def search_and_add_product(self):
        """Khi nhấn Enter: nếu popup đang mở thì chọn item, ngược lại tìm và thêm luôn."""
        # Nếu popup đang hiển thị – chọn item hiện tại
        if self.search_popup.isVisible():
            self.search_timer.stop()
            self.search_popup.select_current()
            return
        # Không có popup: tìm kiếm thường (fallback cho mã vạch quét)
        self.search_timer.stop()
        self.perform_search_product()

    def perform_search_product(self):
        """Hàm tìm sản phẩm từ DB bằng prefix và hiển thị popup"""
        kw = self.txt_barcode.text().strip()
        if not kw: return

        # Tìm từ CSDL thực tế (sử dụng format prefix = kw%)
        products = ProductController.get_all_products(keyword=kw)
        
        if not products:
            QMessageBox.warning(self, "Không tìm thấy", f"Không tìm thấy sản phẩm nào khớp với: {kw}")
            return
            
        selected_prod = None
        if len(products) == 1:
            # Nếu chỉ tìm thấy đúng 1 sản phẩm -> tự động chọn
            selected_prod = products[0]
        else:
            # Nếu có nhiều kết quả -> hiển thị bảng yêu cầu chọn
            # Convert định dạng giá để AddToCartDialog có thể dùng
            formatted_products = []
            for p in products:
                formatted_products.append({
                    "barcode": p["barcode"],
                    "name": p["name"],
                    "unit": p["unit"],
                    "price": float(p["unit_price"])
                })
                
            dialog = ProductSelectDialog(self, formatted_products)
            if dialog.exec_() and dialog.selected_product:
                selected_prod = dialog.selected_product

        if selected_prod:
            # Nếu kết quả từ get_all_products, convert lại key "price" cho popup
            if "unit_price" in selected_prod and "price" not in selected_prod:
                selected_prod["price"] = float(selected_prod["unit_price"])
                
            self.show_add_to_cart_dialog(selected_prod)
            
    def show_add_to_cart_dialog(self, product_info):
        dialog = AddToCartDialog(self, product_info)
        if dialog.exec_():
            qty = dialog.txt_qty.text()
            price = dialog.txt_price.text()
            total = dialog.lbl_total.text()
            
            row_position = self.table_cart.rowCount()
            self.table_cart.insertRow(row_position)

            self.table_cart.setItem(row_position, 0, QTableWidgetItem(product_info["barcode"]))
            self.table_cart.setItem(row_position, 1, QTableWidgetItem(product_info["name"]))
            self.table_cart.setItem(row_position, 2, QTableWidgetItem(product_info["unit"]))
            self.table_cart.setItem(row_position, 3, QTableWidgetItem(qty))
            self.table_cart.setItem(row_position, 4, QTableWidgetItem(price))
            self.table_cart.setItem(row_position, 5, QTableWidgetItem(total))

            self.update_totals()

            # Xóa input để quét lần tới
            self.txt_barcode.clear()

    def format_money_input(self, line_edit):
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
            
        self.update_totals()

    def update_totals(self):
        try:
            subtotal = sum(float(self.table_cart.item(i, 5).text().replace(',', '')) for i in range(self.table_cart.rowCount()) if self.table_cart.item(i, 5))
            self.lbl_subtotal.setText(f"{subtotal:,.0f} đ")
            
            discount = float(self.txt_discount.text().replace(',', '') or 0)
            
            old_debt_text = self.lbl_old_debt.text().replace(' VNĐ', '').replace(',', '')
            old_debt = float(old_debt_text) if old_debt_text.replace('.', '', 1).isdigit() else 0
            
            # Tổng tiền sau khi giảm giá (không được âm)
            total_after_discount = max(0, subtotal - discount)
            
            total_payment = total_after_discount + old_debt
            self.lbl_total_payment.setText(f"{total_payment:,.0f} đ")
            
            amount_paid = float(self.txt_amount_paid.text().replace(',', '') or 0)
            
            if amount_paid > total_payment:
                change = amount_paid - total_payment
                new_debt = 0
            else:
                change = 0
                new_debt = total_payment - amount_paid
                
            self.lbl_change.setText(f"{change:,.0f} đ")
            self.lbl_new_debt.setText(f"{new_debt:,.0f} đ")
        except Exception as e:
            print("Error updating totals:", e)

    def clear_cart(self):
        self.table_cart.setRowCount(0)
        self.lbl_cust_name.setText("---")
        self.lbl_cust_phone.setText("---")
        self.lbl_old_debt.setText("0 VNĐ")
        self.txt_search_cust.clear()
        self.txt_discount.setText("0")
        self.txt_amount_paid.setText("0")
        self.lbl_change.setText("0 đ")
        self.update_totals()

    def process_checkout(self):
        if self.table_cart.rowCount() == 0:
            QMessageBox.warning(self, "Lỗi", "Giỏ hàng đang trống!")
            return

        # Yêu cầu bắt buộc phải có khách hàng
        cust_phone = self.lbl_cust_phone.text()
        if cust_phone == "---" or not cust_phone:
            QMessageBox.warning(self, "Lỗi", "Vui lòng Chọn/Tìm khách hàng để ghi nhận lịch sử giao dịch!")
            return

        self.update_totals()
        
        # Thông tin khách
        cust_name = self.lbl_cust_name.text()
            
        now = datetime.datetime.now()
        invoice_no = f"HD{now.strftime('%y%m%d%H%M%S')}"
        
        # 1. Thu thập dữ liệu để lưu DB
        db_invoice_data = {
            "invoice_number": invoice_no,
            "customer_phone": cust_phone,
            "subtotal": float(self.lbl_subtotal.text().replace(' đ', '').replace(',', '') or 0),
            "discount": float(self.txt_discount.text().replace(',', '') or 0),
            "old_debt": float(self.lbl_old_debt.text().replace(' VNĐ', '').replace(',', '') or 0),
            "total_payment": float(self.lbl_total_payment.text().replace(' đ', '').replace(',', '') or 0),
            "amount_paid": float(self.txt_amount_paid.text().replace(',', '') or 0),
            "new_debt": float(self.lbl_new_debt.text().replace(' đ', '').replace(',', '') or 0),
        }
        
        db_items_data = []
        for i in range(self.table_cart.rowCount()):
            db_items_data.append({
                "barcode": self.table_cart.item(i, 0).text(),
                "name": self.table_cart.item(i, 1).text(),
                "quantity": float(self.table_cart.item(i, 3).text() or 0),
                "unit_price": float(self.table_cart.item(i, 4).text().replace(',', '') or 0),
                "total": float(self.table_cart.item(i, 5).text().replace(',', '') or 0),
            })
            
        # 2. Xử lý qua Controller (Transaction)
        success, msg = InvoiceController.create_invoice(db_invoice_data, db_items_data)
        if not success:
            QMessageBox.warning(self, "Lỗi thanh toán", msg)
            return

        # 3. Thu thập dữ liệu để In Bill
        bill_data = {
            "invoice_no": invoice_no,
            "date": now.strftime('%d/%m/%Y %H:%M'),
            "cus_name": cust_name,
            "cus_phone": cust_phone,
            "cus_address": self.lbl_cust_address.text(),
            "items": [],
            "subtotal": self.lbl_subtotal.text().replace(' đ', ''),
            "discount": self.txt_discount.text(),
            "old_debt": self.lbl_old_debt.text().replace(' VNĐ', ''),
            "total_payment": self.lbl_total_payment.text().replace(' đ', ''),
            "amount_paid": self.txt_amount_paid.text(),
            "change": self.lbl_change.text().replace(' đ', ''),
            "new_debt": self.lbl_new_debt.text().replace(' đ', '')
        }
        
        for i in range(self.table_cart.rowCount()):
            bill_data["items"].append({
                "stt": i + 1,
                "name": self.table_cart.item(i, 1).text(),
                "qty": self.table_cart.item(i, 3).text(),
                "price": f"{float(self.table_cart.item(i, 4).text().replace(',', '')):,.0f}",
                "total": f"{float(self.table_cart.item(i, 5).text().replace(',', '')):,.0f}",
            })

        self.print_bill(bill_data)
        QMessageBox.information(self, "Thành công", msg)
        self.clear_cart()

    # def print_bill(self, data):
    #     dialog = QDialog(self)
    #     dialog.setWindowTitle("In Bill (Hóa Đơn)")
    #     dialog.resize(500, 700)
    #     layout = QVBoxLayout(dialog)
        
    #     html = f"""
    #     <html>
    #     <head>
    #     <style>
    #         body {{ font-family: Arial, sans-serif; font-size: 10pt; margin: 0; padding: 0; color: black; }}
    #         h2 {{ text-align: center; margin-bottom: 5px; font-size: 14pt; }}
    #         .header {{ width: 100%; margin-bottom: 10px; }}
    #         table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
    #         th, td {{ border-bottom: 1px dashed black; padding: 4px; text-align: right; }}
    #         th {{ font-weight: bold; text-align: center; }}
    #         tr td:nth-child(2) {{ text-align: left; }}
    #         .summary {{ float: right; width: 100%; margin-top: 10px; }}
    #         .summary tr td {{ border: none; padding: 2px; text-align: right; }}
    #         .summary tr td:first-child {{ text-align: right; font-weight: bold; }}
    #         .footer {{ text-align: center; margin-top: 15px; font-style: italic; width: 100%; float: left; font-size: 10pt; }}
    #     </style>
    #     </head>
    #     <body>
    #         <h2>HÓA ĐƠN BÁN HÀNG</h2>
    #         <div class="header">
    #             Khách hàng: {data['cus_name']}<br>
    #             {'Điện thoại: ' + data['cus_phone'] + '<br>' if data['cus_phone'] else ''}
    #             {'Đ/c: ' + data['cus_address'] + '<br>' if data['cus_address'] else 'Đ/c: <br>'}
    #             Số HĐ: {data['invoice_no']}<br>
    #             Ngày: {data['date']}<br>
    #         </div>
    #         <table>
    #             <tr><th>STT</th><th>Tên hàng</th><th>SL</th><th>Đơn giá</th><th>Thành tiền</th></tr>
    #     """
    #     for item in data['items']:
    #         html += f"<tr><td>{item['stt']}</td><td>{item['name']}</td><td>{item['qty']}</td><td>{item['price']}</td><td>{item['total']}</td></tr>"
            
    #     html += f"""
    #         </table>
    #         <table class="summary">
    #             <tr><td style="text-align:left;">Tổng cộng:</td><td>{data['subtotal']}</td></tr>
    #             <tr><td style="text-align:left;">Giảm giá :</td><td>{data['discount']}</td></tr>
    #             <tr><td style="text-align:left;">Nợ cũ:</td><td>{data['old_debt']}</td></tr>
    #             <tr><td style="text-align:left;">Tổng thanh toán:</td><td>{data['total_payment']}</td></tr>
    #             <tr><td style="text-align:left;">Tiền khách thanh toán:</td><td>{data['amount_paid']}</td></tr>
    #             <tr><td style="text-align:left;">Tiền trả lại:</td><td>{data['change']}</td></tr>
    #             <tr><td style="text-align:left;">Còn nợ lại:</td><td>{data['new_debt']}</td></tr>
    #         </table>
    #         <div class="footer"><br><br>Chân thành cám ơn quý khách !</div>
    #     </body>
    #     </html>
    #     """
    #     viewer = QTextBrowser()
    #     dialog.setStyleSheet("background-color: white;")
    #     viewer.setHtml(html)
    #     layout.addWidget(viewer)
        
    #     btn_print = QPushButton("In Hóa Đơn")
    #     btn_print.setStyleSheet("background-color: #007bff; color: white; font-size: 16px; padding: 10px;")
        
    #     def execute_print():
    #         import win32print
    #         from PyQt5.QtWidgets import QMessageBox

    #         # Tên Share của máy in trong Control Panel (Windows)
    #         printer_name = "HPRT HM-A300E(ESC)" 

    #         # 1. Các mã lệnh ESC/POS cơ bản (Mã Hex)
    #         ESC_INIT = b'\x1B\x40'          # Khởi tạo/Reset máy in
    #         ALIGN_CENTER = b'\x1B\x61\x01'  # Căn giữa
    #         ALIGN_LEFT = b'\x1B\x61\x00'    # Căn trái
    #         ALIGN_RIGHT = b'\x1B\x61\x02'   # Căn phải
    #         CUT_PAPER = b'\x1D\x56\x41\x10' # Lệnh cắt giấy tự động

    #         def remove_accents(input_str):
    #             s = unicodedata.normalize('NFKD', str(input_str))
    #             s = s.encode('ascii', 'ignore').decode('utf-8')
    #             return s.replace('đ', 'd').replace('Đ', 'D')
            
    #         # Hàm chuyển đổi Text thành dạng Byte để gửi cho máy in
    #         def encode_text(text):
    #             clean_text = remove_accents(text)
    #             return clean_text.encode('ascii', errors='ignore')

    #         # 2. Xây dựng nội dung hóa đơn (Cộng gộp thành 1 chuỗi Bytes dài)
    #         raw_data = b''
    #         raw_data += ESC_INIT

    #         # Header
    #         raw_data += ALIGN_CENTER
    #         raw_data += encode_text("HOA DON BAN HANG\n")
    #         raw_data += encode_text("--------------------------------\n")

    #         # Thông tin khách
    #         raw_data += ALIGN_LEFT
    #         raw_data += encode_text(f"Khach hang: {data['cus_name']}\n")
    #         if data['cus_phone']:
    #             raw_data += encode_text(f"Dien thoai: {data['cus_phone']}\n")
    #         if data['cus_address']:
    #             raw_data += encode_text(f"Dia chi: {data['cus_address']}\n")
    #         raw_data += encode_text(f"So HD: {data['invoice_no']}\n")
    #         raw_data += encode_text(f"Ngay: {data['date']}\n")
    #         raw_data += encode_text("--------------------------------\n")

    #         # Tiêu đề bảng
    #         raw_data += encode_text(f"{'Ten hang':<14} {'SL':>4} {'Gia':>9} {'Tong':>11}\n")
    #         raw_data += encode_text("--------------------------------\n")

    #         # Danh sách sản phẩm
    #         for item in data['items']:
    #             full_name = remove_accents(item['name'])
    #             qty = str(item['qty'])
    #             price = str(item['price']).replace(',', '.')
    #             total = str(item['total']).replace(',', '.')

    #             name_lines = textwrap.wrap(full_name, width=14)

    #             if not name_lines:
    #                 name_lines = [""]

    #             first_line = f"{name_lines[0]:<14} {qty:>4} {price:>9} {total:>11}\n"
    #             raw_data += encode_text(first_line)

    #             for extra_name in name_lines[1:]:
    #                 raw_data += encode_text(f"{extra_name:<14}\n")

    #         raw_data += encode_text("--------------------------------\n")

    #         # Phần tính tiền
    #         raw_data += ALIGN_LEFT
    #         raw_data += encode_text(f"{'Tong cong:':<18}{data['subtotal']:>14}\n")
    #         raw_data += encode_text(f"{'Giam gia:':<18}{data['discount']:>14}\n")
    #         raw_data += encode_text(f"{'No cu:':<18}{data['old_debt']:>14}\n")
    #         raw_data += encode_text(f"{'Tong thanh toan:':<18}{data['total_payment']:>14}\n")
    #         raw_data += encode_text(f"{'Khach thanh toan:':<18}{data['amount_paid']:>14}\n")
    #         raw_data += encode_text(f"{'Tien tra lai:':<18}{data['change']:>14}\n")
    #         raw_data += encode_text(f"{'Con no lai:':<18}{data['new_debt']:>14}\n")
            
    #         raw_data += encode_text("\n") # Xuống dòng
            
    #         # Footer
    #         raw_data += ALIGN_CENTER
    #         raw_data += encode_text("Chan thanh cam on quy khach!\n")
    #         raw_data += encode_text("\n\n\n\n") # Đẩy giấy lên một chút trước khi cắt

    #         # Lệnh cắt giấy
    #         raw_data += CUT_PAPER

    #         # 3. Mở cổng kết nối và bắn thẳng Data xuống máy in
    #         try:
    #             hPrinter = win32print.OpenPrinter(printer_name)
    #             try:
    #                 # Tạo một Job in ấn định dạng thô (RAW)
    #                 hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS Invoice", None, "RAW"))
    #                 win32print.StartPagePrinter(hPrinter)
    #                 win32print.WritePrinter(hPrinter, raw_data)
    #                 win32print.EndPagePrinter(hPrinter)
    #                 win32print.EndDocPrinter(hPrinter)
    #             finally:
    #                 win32print.ClosePrinter(hPrinter)
                
    #             # In xong thì đóng form
    #             dialog.accept() 
                
    #         except Exception as e:
    #             QMessageBox.critical(None, "Lỗi in ấn", f"Không thể kết nối với Windows Spooler:\n{str(e)}")

    #     btn_print.clicked.connect(execute_print)
    #     layout.addWidget(btn_print)
    #     dialog.exec_()

    def print_bill(self, data):
        dialog = QDialog(self)
        dialog.setWindowTitle("In Bill (Hóa Đơn)")
        dialog.resize(500, 700)
        layout = QVBoxLayout(dialog)
        
        # 1. HTML được cập nhật với tiêu đề CĂN GIỮA và Font to hơn từ ảnh mẫu
        html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 20px; margin: 0; padding: 0; color: black; }}
            
            /* CSS MỚI CHO TIÊU ĐỀ: Căn giữa tất cả */
            .header {{
                text-align: center;
                width: 100%;
                margin-bottom: 20px;
                line-height: 1.3;
            }}
            .header-line1 {{ margin: 0; font-size: 22px; font-weight: normal; }}
            .header-line2 {{ margin: 3px 0; font-size: 32px; font-weight: bold; }}
            .header-details {{ margin-top: 5px; font-size: 19px; text-align: left}}
            
            /* CSS CHO TIÊU ĐỀ CHÍNH HÓA ĐƠN */
            .invoice-title {{
                text-align: center;
                margin: 0;
                font-size: 26px;
                font-weight: bold;
                border-bottom: 1px dashed black;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
            th, td {{ border-bottom: 1px dashed black; padding: 8px 2px; text-align: center; }}
            th {{ font-weight: bold; text-align: center; }}
            tr td:nth-child(2) {{ text-align: left; }}
            .summary {{ float: right; width: 100%; margin-top: 15px; }}
            .summary tr td {{ border: none; padding: 4px 2px; text-align: right; }}
            .summary tr td:first-child {{ text-align: right; font-weight: bold; width: 50%; }}
            .footer {{ text-align: center; margin-top: 20px; font-style: italic; width: 100%; float: left; font-size: 18px; }}
        </style>
        </head>
        <body>
            
            <div class="header">
                <div class="header-line1">NỮ TRANG BẠC CAO CẤP</div>
                <div class="header-line2">PHIẾU TẠM TÍNH</div>
                <div class="header-details">
                    Tên KH: {data['cus_name']}<br>
                    Số ĐT: {data['cus_phone'] + '<br>' if data['cus_phone'] else ''}
                    Địa Chỉ: {data['cus_address'] + '<br>' if data['cus_address'] else 'Đ/c: <br>'}
                    Số HĐ: {data['invoice_no']}<br>
                    Ngày: {data['date']}<br>
                </div>
            </div>
            
            <div class="invoice-title">***************************</div>
            
            <table width="100%">
                <tr>
                    <th width="8%">STT</th>
                    <th width="42%">Tên hàng</th>
                    <th width="10%">SL</th>
                    <th width="20%">Giá</th>
                    <th width="20%">Tổng</th>
                </tr>
        """
        
        # HTML <table> tự động ngắt dòng thông minh, không cần textwrap của Python nữa!
        for item in data['items']:
            html += f"<tr><td>{item['stt']}</td><td>{item['name']}</td><td>{item['qty']}</td><td>{item['price']}</td><td>{item['total']}</td></tr>"
            
        html += f"""
            </table>
            <table class="summary" width="50%">
                <tr><td width="60%">Tổng cộng:</td><td width="40%">{data['subtotal']}</td></tr>
                <tr><td>Giảm giá :</td><td>{data['discount']}</td></tr>
                <tr><td>Nợ cũ:</td><td>{data['old_debt']}</td></tr>
                <tr><td>Tổng thanh toán:</td><td>{data['total_payment']}</td></tr>
                <tr><td>Khách thanh toán:</td><td>{data['amount_paid']}</td></tr>
                <tr><td>Tiền trả lại:</td><td>{data['change']}</td></tr>
                <tr><td>Còn nợ lại:</td><td>{data['new_debt']}</td></tr>
            </table>
            <div class="footer"><br><br>Chân thành cám ơn quý khách !</div>
        </body>
        </html>
        """
        viewer = QTextBrowser()
        dialog.setStyleSheet("background-color: white;")
        viewer.setHtml(html)
        layout.addWidget(viewer)
        
        # Phần nút in và hàm execute_print (giữ nguyên logic in ảnh)
        btn_print = QPushButton("In Hóa Đơn")
        btn_print.setStyleSheet("background-color: #007bff; color: white; font-size: 16px; padding: 10px;")
        
        def execute_print():
            import win32print
            from PyQt5.QtGui import QImage, QPainter
            from PyQt5.QtWidgets import QMessageBox

            # Tên máy in của bạn (giữ nguyên tên máy in bạn đang dùng)
            printer_name = "HPRT HM-A300E(ESC)" 

            try:
                # 1. LẤY GIAO DIỆN HTML VÀ ÉP RA THÀNH ẢNH (Image)
                doc = viewer.document().clone()
                doc.setDocumentMargin(0)
                
                # Ép chiều ngang bằng đúng chuẩn 80mm (576 pixel)
                printer_width_px = 576
                doc.setTextWidth(printer_width_px)
                
                # Tính toán chiều cao tự động theo nội dung
                doc_height_px = int(doc.size().height())
                
                img = QImage(printer_width_px, doc_height_px, QImage.Format_Mono)
                img.fill(1) # Nền trắng
                
                painter = QPainter(img)
                doc.drawContents(painter)
                painter.end()

                # 2. CHUYỂN ĐỔI ẢNH THÀNH MÃ LỆNH ESC/POS (Y chang in mã vạch)
                bytes_width = (printer_width_px + 7) // 8
                xL = bytes_width % 256
                xH = bytes_width // 256
                yL = doc_height_px % 256
                yH = doc_height_px // 256
                
                ESC_INIT = b'\x1B\x40'
                GS_V_0 = b'\x1D\x76\x30\x00' + bytes([xL, xH, yL, yH])
                
                raster_data = bytearray()
                for y_idx in range(doc_height_px):
                    scanline_str = img.constScanLine(y_idx).asstring(img.bytesPerLine())
                    line_data = bytearray(scanline_str[:bytes_width])
                    for j in range(len(line_data)):
                        line_data[j] = ~line_data[j] & 0xFF
                    raster_data.extend(line_data)
                
                # Lệnh cắt giấy: Tự động đẩy lên trước khi cắt
                CUT_PAPER = b'\x1D\x56\x42\x00'
                
                # 3. GHÉP DỮ LIỆU (Thêm vài dòng trắng đẩy giấy lên trước khi cắt)
                # Đổi thành 3 dòng trắng để khớp với mã vạch
                raw_data = ESC_INIT + GS_V_0 + raster_data + b"\n\n\n" + CUT_PAPER

                # 4. GỬI XUỐNG MÁY IN
                hPrinter = win32print.OpenPrinter(printer_name)
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS Invoice Image", None, "RAW"))
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, raw_data)
                    win32print.EndPagePrinter(hPrinter)
                    win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
                
                dialog.accept() 
                
            except Exception as e:
                QMessageBox.critical(None, "Lỗi in ấn", f"Không thể in hóa đơn:\n{str(e)}")

        btn_print.clicked.connect(execute_print)
        layout.addWidget(btn_print)
        dialog.exec_()