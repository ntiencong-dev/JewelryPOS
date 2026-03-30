from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSplitter, QGroupBox, QFormLayout, QDialog, QMessageBox, QTextEdit,
    QAbstractItemView
)
from PyQt5.QtCore import Qt

from src.controllers.customer_controller import CustomerController
from src.controllers.invoice_controller import InvoiceController

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer_data = customer_data
        self.action_type = None  # Thêm biến này để phân biệt hành động (update hay delete)
        if self.customer_data:
            self.setWindowTitle("Sửa thông tin Khách hàng")
        else:
            self.setWindowTitle("Thêm thông tin Khách hàng")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_name = QLineEdit()
        self.txt_phone = QLineEdit()
        self.txt_address = QTextEdit()
        self.txt_address.setMaximumHeight(80)
        
        if self.customer_data:
            self.txt_name.setText(self.customer_data.get("name", ""))
            self.txt_phone.setText(self.customer_data.get("phone", ""))
            self.txt_phone.setReadOnly(True)  # Không cho sửa SĐT vì là khóa chính
            self.txt_address.setPlainText(self.customer_data.get("address", ""))

        form_layout.addRow("Tên khách hàng (*):", self.txt_name)
        form_layout.addRow("Số điện thoại (*):", self.txt_phone)
        form_layout.addRow("Địa chỉ:", self.txt_address)

        layout.addLayout(form_layout)

        # Nút hành động
        btn_layout = QHBoxLayout()
        if not self.customer_data:
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


        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setStyleSheet("padding: 6px;")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def on_save(self):
        self.action_type = "save"
        self.accept()
        
    def on_update(self):
        self.action_type = "update"
        self.accept()
        
    def on_delete(self):
        reply = QMessageBox.question(self, 'Xác nhận xóa', 'Bạn có chắc chắn muốn xóa khách hàng này?', 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.action_type = "delete"
            self.accept()


class InvoiceDetailDialog(QDialog):
    """Cửa sổ chi tiết hóa đơn"""
    def __init__(self, invoice_info, parent=None):
        super().__init__(parent)
        self.invoice_info = invoice_info
        self.setWindowTitle(f"Chi tiết biên lai: {invoice_info['invoice_number']}")
        self.setMinimumWidth(650)
        self.setMinimumHeight(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header info
        info_layout = QHBoxLayout()
        lbl_id = QLabel(f"<b>Mã HD:</b> <font color='blue'>{self.invoice_info['invoice_number']}</font>")
        lbl_date = QLabel(f"<b>Ngày bán:</b> {self.invoice_info['date']}")
        info_layout.addWidget(lbl_id)
        info_layout.addStretch()
        info_layout.addWidget(lbl_date)
        layout.addLayout(info_layout)
        
        # Table
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Sản phẩm", "SL", "Đơn giá", "Thành tiền"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(table)
        
        for idx, item in enumerate(self.invoice_info['items']):
            table.insertRow(idx)
            table.setItem(idx, 0, QTableWidgetItem(item['product_name']))
            table.setItem(idx, 1, QTableWidgetItem(str(item['quantity'])))
            table.setItem(idx, 2, QTableWidgetItem(f"{int(item['unit_price']):,}"))
            table.setItem(idx, 3, QTableWidgetItem(f"{int(item['total']):,}"))
            
        # Summary
        summary_layout = QFormLayout()
        lbl_subtotal = QLabel(f"{int(self.invoice_info['subtotal']):,} đ")
        lbl_discount = QLabel(f"{int(self.invoice_info['discount']):,} đ")
        lbl_total = QLabel(f"<font color='red' size='4'><b>{int(self.invoice_info['total_payment']):,} đ</b></font>")
        
        lbl_paid = QLabel(f"{int(self.invoice_info['amount_paid']):,} đ")
        lbl_new_debt = QLabel(f"{int(self.invoice_info['new_debt']):,} đ")
        
        summary_layout.addRow("<b>Tổng tiền hàng:</b>", lbl_subtotal)
        summary_layout.addRow("<b>Giảm giá:</b>", lbl_discount)
        summary_layout.addRow("<b>Tổng cộng:</b>", lbl_total)
        summary_layout.addRow("<b>Khách đã trả:</b>", lbl_paid)
        summary_layout.addRow("<b>Dư nợ hiện tại:</b>", lbl_new_debt)
        summary_layout.setLabelAlignment(Qt.AlignRight)
        
        frame = QGroupBox()
        frame.setLayout(summary_layout)
        layout.addWidget(frame)
        
        # Close button
        btn_close = QPushButton("Đóng")
        btn_close.setMinimumHeight(40)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Sử dụng QSplitter để chia đôi màn hình có thể kéo giãn
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ==========================================
        # PANEL TRÁI: DANH SÁCH KHÁCH HÀNG
        # ==========================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Thanh tìm kiếm & Nút thêm KH
        top_left_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm SĐT hoặc Tên khách...")
        self.txt_search.setMinimumHeight(35)
        
        self.btn_search = QPushButton("Tìm")
        self.btn_search.setMinimumHeight(35)
        self.btn_search.clicked.connect(self.load_data)
        self.txt_search.returnPressed.connect(self.load_data)
        
        self.btn_add_customer = QPushButton("➕ Thêm KH")
        self.btn_add_customer.setMinimumHeight(35)
        self.btn_add_customer.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        self.btn_add_customer.clicked.connect(self.show_add_customer_dialog)
        
        self.btn_edit_customer = QPushButton("✏️ Sửa KH")
        self.btn_edit_customer.setMinimumHeight(35)
        self.btn_edit_customer.setStyleSheet("background-color: #ffc107; font-weight: bold;")
        self.btn_edit_customer.clicked.connect(self.on_edit_button_clicked)
        
        self.btn_refresh = QPushButton("🔄 Làm mới")
        self.btn_refresh.setMinimumHeight(35)
        self.btn_refresh.clicked.connect(self.load_data)

        top_left_layout.addWidget(self.txt_search)
        top_left_layout.addWidget(self.btn_search)
        top_left_layout.addWidget(self.btn_add_customer)
        top_left_layout.addWidget(self.btn_edit_customer)
        top_left_layout.addWidget(self.btn_refresh)
        left_layout.addLayout(top_left_layout)

        # Bảng danh sách khách hàng
        self.table_customers = QTableWidget(0, 4)
        self.table_customers.setHorizontalHeaderLabels(["SĐT", "Tên KH", "Địa Chỉ", "Tổng Công Nợ"])
        self.table_customers.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_customers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_customers.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Bắt sự kiện chọn dòng để hiển thị lịch sử bên phải
        self.table_customers.itemSelectionChanged.connect(self.on_customer_selected)
        # Bắt sự kiện double click để sửa
        self.table_customers.itemDoubleClicked.connect(self.on_customer_double_clicked)

        left_layout.addWidget(self.table_customers)

        # ==========================================
        # PANEL PHẢI: CHI TIẾT & LỊCH SỬ GIAO DỊCH
        # ==========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Group 1: Thông tin chi tiết
        group_details = QGroupBox("Thông tin chi tiết Khách Hàng")
        details_layout = QVBoxLayout()
        
        form_details = QFormLayout()
        self.lbl_detail_name = QLabel("---")
        self.lbl_detail_phone = QLabel("---")
        self.lbl_detail_addr = QLabel("---")
        
        self.lbl_detail_debt = QLabel("0 đ")
        self.lbl_detail_debt.setStyleSheet("color: red; font-size: 18px; font-weight: bold;")

        form_details.addRow("Tên KH:", self.lbl_detail_name)
        form_details.addRow("Số ĐT:", self.lbl_detail_phone)
        form_details.addRow("Địa chỉ:", self.lbl_detail_addr)
        form_details.addRow("ĐANG NỢ:", self.lbl_detail_debt)
        
        details_layout.addLayout(form_details)

        # Nút Trả Nợ (Thu tiền nợ từ hóa đơn cũ)
        self.btn_pay_debt = QPushButton("💰 Thu Tiền Nợ")
        self.btn_pay_debt.setMinimumHeight(40)
        self.btn_pay_debt.setStyleSheet("background-color: #ffc107; font-weight: bold; font-size: 14px;")
        self.btn_pay_debt.setEnabled(False) # Sẽ bật khi chọn KH có nợ
        details_layout.addWidget(self.btn_pay_debt)

        group_details.setLayout(details_layout)
        right_layout.addWidget(group_details)

        # Group 2: Lịch sử Giao dịch
        group_history = QGroupBox("Lịch sử Mua Hàng & Trả Nợ")
        history_layout = QVBoxLayout()

        self.table_history = QTableWidget(0, 5)
        self.table_history.setHorizontalHeaderLabels(["Ngày", "Mã HĐ / Phiếu", "Tổng Giá Trị", "Đã Trả", "Nợ / Dư"])
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_history.itemDoubleClicked.connect(self.on_history_double_clicked)
        history_layout.addWidget(self.table_history)

        group_history.setLayout(history_layout)
        right_layout.addWidget(group_history, stretch=1)

        # Add vào Splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 750]) # Tỷ lệ chia màn hình

        main_layout.addWidget(splitter)
        
        # Load dữ liệu thực từ DataBase
        self.load_data()

    def load_data(self):
        """Lấy dữ liệu khách hàng từ Database"""
        kw = self.txt_search.text().strip()
        data = CustomerController.get_all_customers(kw)
        
        self.table_customers.setRowCount(0)
        for row_idx, item in enumerate(data):
            self.table_customers.insertRow(row_idx)
            self.table_customers.setItem(row_idx, 0, QTableWidgetItem(item['phone']))
            self.table_customers.setItem(row_idx, 1, QTableWidgetItem(item['name']))
            self.table_customers.setItem(row_idx, 2, QTableWidgetItem(item['address']))
            
            # Đổi màu hiển thị đỏ nếu có nợ
            debt_val = item['debt']
            parsed_debt = float(debt_val)
            
            debt_item = QTableWidgetItem(f"{parsed_debt:,}")
            if parsed_debt > 0.0:
                debt_item.setForeground(Qt.red)
            self.table_customers.setItem(row_idx, 3, debt_item)

    def on_customer_selected(self):
        """Khi click vào 1 dòng khách hàng -> đổi thông tin chi tiết"""
        selected_items = self.table_customers.selectedItems()
        if not selected_items: return
        
        row = selected_items[0].row()
        phone = self.table_customers.item(row, 0).text()
        name = self.table_customers.item(row, 1).text()
        address = self.table_customers.item(row, 2).text()
        debt = self.table_customers.item(row, 3).text()
        

        # Update view
        self.lbl_detail_name.setText(name)
        self.lbl_detail_phone.setText(phone)
        self.lbl_detail_addr.setText(address)
        self.lbl_detail_debt.setText(f"{debt} VNĐ")

        # Bật tắt nút Thu nợ
        self.btn_pay_debt.setEnabled(debt != "0")

        # Load lịch sử giao dịch
        history = InvoiceController.get_customer_history(phone)
        self.table_history.setRowCount(0)
        
        for idx, row_data in enumerate(history):
            self.table_history.insertRow(idx)
            self.table_history.setItem(idx, 0, QTableWidgetItem(row_data["date"]))
            self.table_history.setItem(idx, 1, QTableWidgetItem(row_data["invoice_number"]))
            self.table_history.setItem(idx, 2, QTableWidgetItem(f"{int(row_data['total_payment']):,}"))
            self.table_history.setItem(idx, 3, QTableWidgetItem(f"{int(row_data['amount_paid']):,}"))
            
            debt_item = QTableWidgetItem(f"{int(row_data['new_debt']):,}")
            if int(row_data['new_debt']) > 0:
                debt_item.setForeground(Qt.red)
            self.table_history.setItem(idx, 4, debt_item)

    def on_history_double_clicked(self, item):
        row = item.row()
        invoice_number = self.table_history.item(row, 1).text()
        
        invoice_info = InvoiceController.get_invoice_details(invoice_number)
        if invoice_info:
            dialog = InvoiceDetailDialog(invoice_info, self)
            dialog.exec_()
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể lấy thông tin chi tiết hóa đơn!")

    def on_edit_button_clicked(self):
        selected_items = self.table_customers.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Chú ý", "Vui lòng chọn một khách hàng để sửa!")
            return
            
        row = selected_items[0].row()
        phone = self.table_customers.item(row, 0).text()
        name = self.table_customers.item(row, 1).text()
        address = self.table_customers.item(row, 2).text()
        
        customer_data = {"phone": phone, "name": name, "address": address}
        self.show_edit_customer_dialog(customer_data)

    def on_customer_double_clicked(self, item):
        row = item.row()
        phone = self.table_customers.item(row, 0).text()
        name = self.table_customers.item(row, 1).text()
        address = self.table_customers.item(row, 2).text()
        
        customer_data = {"phone": phone, "name": name, "address": address}
        self.show_edit_customer_dialog(customer_data)

    def show_edit_customer_dialog(self, customer_data):
        dialog = CustomerDialog(self, customer_data=customer_data)
        if dialog.exec_():
            if dialog.action_type == "update":
                name = dialog.txt_name.text().strip()
                addr = dialog.txt_address.toPlainText().strip()
                
                if not name:
                    QMessageBox.warning(self, "Lỗi Input", "Tên là bắt buộc!")
                    return
                    
                update_data = {
                    "name": name,
                    "address": addr
                }
                
                success, msg = CustomerController.update_customer(customer_data['phone'], update_data)
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.load_data() # Reload
                    # Xóa form thông tin chi tiết đang hiển thị
                    self.lbl_detail_name.setText("---")
                    self.lbl_detail_phone.setText("---")
                    self.lbl_detail_addr.setText("---")
                    self.lbl_detail_debt.setText("0 VNĐ")
                    self.table_history.setRowCount(0)
                else:
                    QMessageBox.warning(self, "Lỗi", msg)
                    
            elif dialog.action_type == "delete":
                success, msg = CustomerController.delete_customer(customer_data['phone'])
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.load_data() # Reload
                    
                    # Reset lại bảng thông tin chi tiết
                    self.lbl_detail_name.setText("---")
                    self.lbl_detail_phone.setText("---")
                    self.lbl_detail_addr.setText("---")
                    self.lbl_detail_debt.setText("0 VNĐ")
                    self.table_history.setRowCount(0)
                else:
                    QMessageBox.warning(self, "Lỗi", msg)

    def show_add_customer_dialog(self):
        dialog = CustomerDialog(self)
        if dialog.exec_():
            name = dialog.txt_name.text().strip()
            phone = dialog.txt_phone.text().strip()
            addr = dialog.txt_address.toPlainText().strip()
            
            if not name or not phone:
                QMessageBox.warning(self, "Lỗi Input", "Tên và SĐT là bắt buộc!")
                return
                
            cust_data = {
                "name": name,
                "phone": phone,
                "address": addr
            }
            
            success, msg = CustomerController.add_customer(cust_data)
            if success:
                QMessageBox.information(self, "Thành công", msg)
                self.load_data() # Reload
            else:
                QMessageBox.warning(self, "Lỗi", msg)