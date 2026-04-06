"""
Unit tests cho InvoiceController.
"""
import pytest
from tests.conftest import make_product, make_customer
from src.controllers.invoice_controller import InvoiceController


def _make_invoice_data(invoice_no="HD001", phone="0910000001",
                       subtotal=500000, discount=0, old_debt=0,
                       total_payment=500000, amount_paid=500000, new_debt=0):
    return {
        "invoice_number": invoice_no,
        "customer_phone": phone,
        "subtotal": subtotal,
        "discount": discount,
        "old_debt": old_debt,
        "total_payment": total_payment,
        "amount_paid": amount_paid,
        "new_debt": new_debt,
    }


def _make_items_data(barcode="INV-PROD-001", name="Nhẫn", qty=1.0, price=500000):
    return [{"barcode": barcode, "name": name, "quantity": qty,
             "unit_price": price, "total": qty * price}]


class TestInvoiceControllerCreateInvoice:
    def test_create_invoice_success(self, patched_session):
        """Tạo hóa đơn thành công với đầy đủ dữ liệu."""
        make_product(patched_session, barcode="INV-P001", unit_price=500000, stock_qty=10)
        make_customer(patched_session, phone="0910000001")

        inv_data = _make_invoice_data("HD-CREATE-001", "0910000001",
                                      subtotal=500000, total_payment=500000,
                                      amount_paid=500000)
        items = _make_items_data("INV-P001", qty=1.0, price=500000)
        ok, msg = InvoiceController.create_invoice(inv_data, items)
        assert ok is True
        assert "thành công" in msg.lower()

    def test_create_invoice_deducts_stock(self, patched_session):
        """Tạo hóa đơn phải trừ tồn kho sản phẩm."""
        from src.models.product import Product
        make_product(patched_session, barcode="INV-P002", stock_qty=10.0)
        make_customer(patched_session, phone="0910000002")

        inv_data = _make_invoice_data("HD-STOCK-001", "0910000002",
                                      subtotal=1000000, total_payment=1000000,
                                      amount_paid=1000000)
        items = _make_items_data("INV-P002", qty=3.0, price=1000000)
        InvoiceController.create_invoice(inv_data, items)

        prod = patched_session.query(Product).filter_by(barcode="INV-P002").first()
        assert float(prod.stock_qty) == pytest.approx(7.0, abs=0.001)

    def test_create_invoice_updates_customer_debt(self, patched_session):
        """Tạo hóa đơn phải cập nhật nợ mới của khách hàng."""
        from src.models.customer import Customer
        make_product(patched_session, barcode="INV-P003", stock_qty=10.0)
        make_customer(patched_session, phone="0910000003", total_debt=0)

        inv_data = _make_invoice_data("HD-DEBT-001", "0910000003",
                                      subtotal=500000, total_payment=500000,
                                      amount_paid=300000, new_debt=200000)
        items = _make_items_data("INV-P003", qty=1.0, price=500000)
        InvoiceController.create_invoice(inv_data, items)

        cust = patched_session.query(Customer).filter_by(phone="0910000003").first()
        assert float(cust.total_debt) == pytest.approx(200000.0, abs=1.0)

    def test_create_invoice_customer_not_found(self, patched_session):
        """Tạo hóa đơn với khách hàng không tồn tại phải báo lỗi."""
        inv_data = _make_invoice_data("HD-NOCU-001", "0999999999")
        items = _make_items_data("ANY-BAR")
        ok, msg = InvoiceController.create_invoice(inv_data, items)
        assert ok is False
        assert "khách hàng" in msg.lower()

    def test_create_invoice_product_not_found(self, patched_session):
        """Tạo hóa đơn với sản phẩm không tồn tại phải báo lỗi."""
        make_customer(patched_session, phone="0910000004")
        inv_data = _make_invoice_data("HD-NOPROD-001", "0910000004")
        items = _make_items_data("GHOST-BARCODE-999")
        ok, msg = InvoiceController.create_invoice(inv_data, items)
        assert ok is False

    def test_create_invoice_no_stock_deduction_for_cong_unit(self, patched_session):
        """Sản phẩm loại 'Công' không bị trừ tồn kho."""
        from src.models.product import Product
        make_product(patched_session, barcode="INV-CONG-001",
                     unit="Công", stock_qty=0.0)
        make_customer(patched_session, phone="0910000005")

        inv_data = _make_invoice_data("HD-CONG-001", "0910000005",
                                      subtotal=200000, total_payment=200000,
                                      amount_paid=200000)
        items = [{"barcode": "INV-CONG-001", "name": "Công thợ",
                  "quantity": 1.0, "unit_price": 200000, "total": 200000}]
        ok, msg = InvoiceController.create_invoice(inv_data, items)
        assert ok is True
        prod = patched_session.query(Product).filter_by(barcode="INV-CONG-001").first()
        assert float(prod.stock_qty) == pytest.approx(0.0, abs=0.001)


class TestInvoiceControllerGetHistory:
    def test_get_customer_history_empty(self, patched_session):
        """Khách hàng chưa có hóa đơn trả về list rỗng."""
        make_customer(patched_session, phone="0911000001")
        result = InvoiceController.get_customer_history("0911000001")
        assert isinstance(result, list)

    def test_get_customer_history_not_found(self, patched_session):
        """Khách hàng không tồn tại trả về list rỗng."""
        result = InvoiceController.get_customer_history("0000000000")
        assert result == []

    def test_get_customer_history_after_purchase(self, patched_session):
        """Sau khi tạo hóa đơn, lịch sử phải có ít nhất 1 bản ghi."""
        make_product(patched_session, barcode="INV-P010", stock_qty=5.0)
        make_customer(patched_session, phone="0911000002")
        inv_data = _make_invoice_data("HD-HIS-001", "0911000002",
                                      subtotal=500000, total_payment=500000,
                                      amount_paid=500000)
        items = _make_items_data("INV-P010")
        InvoiceController.create_invoice(inv_data, items)
        result = InvoiceController.get_customer_history("0911000002")
        assert len(result) >= 1
        assert result[0]["invoice_number"] == "HD-HIS-001"


class TestInvoiceControllerGetDetails:
    def test_get_invoice_details_not_found(self, patched_session):
        """Hóa đơn không tồn tại trả về None."""
        result = InvoiceController.get_invoice_details("GHOST-INVOICE")
        assert result is None

    def test_get_invoice_details_success(self, patched_session):
        """Lấy chi tiết hóa đơn đã tạo thành công."""
        make_product(patched_session, barcode="INV-P020", stock_qty=5.0)
        make_customer(patched_session, phone="0912000001")
        inv_data = _make_invoice_data("HD-DET-001", "0912000001",
                                      subtotal=750000, total_payment=750000,
                                      amount_paid=750000)
        items = [{"barcode": "INV-P020", "name": "Lắc tay",
                  "quantity": 1.5, "unit_price": 500000, "total": 750000}]
        InvoiceController.create_invoice(inv_data, items)
        result = InvoiceController.get_invoice_details("HD-DET-001")
        assert result is not None
        assert result["invoice_number"] == "HD-DET-001"
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name"] == "Lắc tay"
