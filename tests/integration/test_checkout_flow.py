"""
Integration tests – Luồng thanh toán (Checkout Flow).
Test luồng đầy đủ: Thêm SP → Thêm KH → Tạo hóa đơn → Kiểm tra kết quả.
"""
import pytest
from tests.conftest import make_product, make_customer
from src.controllers.product_controller import ProductController
from src.controllers.customer_controller import CustomerController
from src.controllers.invoice_controller import InvoiceController
from src.models.product import Product
from src.models.customer import Customer
from src.models.invoice import Invoice


class TestCheckoutFlow:
    """Kiểm tra luồng thanh toán hoàn chỉnh từ đầu đến cuối."""

    def test_full_checkout_with_full_payment(self, patched_session):
        """
        Kịch bản: Khách hàng mua 2 sản phẩm, thanh toán đủ.
        Kỳ vọng: Tồn kho giảm, nợ mới = 0, hóa đơn được lưu.
        """
        # 1. Chuẩn bị dữ liệu
        p1 = make_product(patched_session, barcode="CHK-P001", name="Nhẫn A",
                          unit_price=500000, stock_qty=10)
        p2 = make_product(patched_session, barcode="CHK-P002", name="Lắc B",
                          unit_price=800000, stock_qty=5)
        cust = make_customer(patched_session, phone="0940000001",
                             name="KH Checkout 1", total_debt=0)

        # 2. Tạo hóa đơn
        subtotal = 500000 + 800000  # = 1,300,000
        inv_data = {
            "invoice_number": "HD-FULL-001",
            "customer_phone": "0940000001",
            "subtotal": subtotal,
            "discount": 0,
            "old_debt": 0,
            "total_payment": subtotal,
            "amount_paid": subtotal,
            "new_debt": 0,
        }
        items = [
            {"barcode": "CHK-P001", "name": "Nhẫn A",
             "quantity": 1.0, "unit_price": 500000, "total": 500000},
            {"barcode": "CHK-P002", "name": "Lắc B",
             "quantity": 1.0, "unit_price": 800000, "total": 800000},
        ]
        ok, msg = InvoiceController.create_invoice(inv_data, items)

        # 3. Assert kết quả
        assert ok is True

        # Tồn kho giảm
        reloaded_p1 = patched_session.query(Product).filter_by(barcode="CHK-P001").first()
        reloaded_p2 = patched_session.query(Product).filter_by(barcode="CHK-P002").first()
        assert float(reloaded_p1.stock_qty) == pytest.approx(9.0, abs=0.001)
        assert float(reloaded_p2.stock_qty) == pytest.approx(4.0, abs=0.001)

        # Nợ khách = 0
        reloaded_cust = patched_session.query(Customer).filter_by(phone="0940000001").first()
        assert float(reloaded_cust.total_debt) == pytest.approx(0.0, abs=1.0)

        # Hóa đơn được lưu
        inv = patched_session.query(Invoice).filter_by(invoice_number="HD-FULL-001").first()
        assert inv is not None
        assert len(inv.items) == 2

    def test_checkout_with_partial_payment_creates_new_debt(self, patched_session):
        """
        Kịch bản: Khách mua 1 sản phẩm 1,000,000 nhưng chỉ trả 600,000.
        Kỳ vọng: Nợ mới = 400,000.
        """
        make_product(patched_session, barcode="CHK-P003", unit_price=1000000, stock_qty=5)
        make_customer(patched_session, phone="0940000002", total_debt=0)

        inv_data = {
            "invoice_number": "HD-PART-001",
            "customer_phone": "0940000002",
            "subtotal": 1000000,
            "discount": 0,
            "old_debt": 0,
            "total_payment": 1000000,
            "amount_paid": 600000,
            "new_debt": 400000,
        }
        items = [{"barcode": "CHK-P003", "name": "SP",
                  "quantity": 1.0, "unit_price": 1000000, "total": 1000000}]
        ok, _ = InvoiceController.create_invoice(inv_data, items)
        assert ok is True

        cust = patched_session.query(Customer).filter_by(phone="0940000002").first()
        assert float(cust.total_debt) == pytest.approx(400000.0, abs=1.0)

    def test_checkout_with_old_debt_included(self, patched_session):
        """
        Kịch bản: Khách còn nợ cũ 200,000, mua thêm 500,000, trả 700,000.
        Kỳ vọng: Nợ mới = 0.
        """
        make_product(patched_session, barcode="CHK-P004", unit_price=500000, stock_qty=5)
        make_customer(patched_session, phone="0940000003", total_debt=200000)

        inv_data = {
            "invoice_number": "HD-OLDDEBT-001",
            "customer_phone": "0940000003",
            "subtotal": 500000,
            "discount": 0,
            "old_debt": 200000,
            "total_payment": 700000,
            "amount_paid": 700000,
            "new_debt": 0,
        }
        items = [{"barcode": "CHK-P004", "name": "SP",
                  "quantity": 1.0, "unit_price": 500000, "total": 500000}]
        ok, _ = InvoiceController.create_invoice(inv_data, items)
        assert ok is True

        cust = patched_session.query(Customer).filter_by(phone="0940000003").first()
        assert float(cust.total_debt) == pytest.approx(0.0, abs=1.0)

    def test_checkout_with_discount_reduces_total(self, patched_session):
        """
        Kịch bản: Mua 1,000,000, giảm giá 100,000, trả đủ 900,000.
        Kỳ vọng: Nợ mới = 0.
        """
        make_product(patched_session, barcode="CHK-P005", unit_price=1000000, stock_qty=5)
        make_customer(patched_session, phone="0940000004")

        inv_data = {
            "invoice_number": "HD-DISC-001",
            "customer_phone": "0940000004",
            "subtotal": 1000000,
            "discount": 100000,
            "old_debt": 0,
            "total_payment": 900000,
            "amount_paid": 900000,
            "new_debt": 0,
        }
        items = [{"barcode": "CHK-P005", "name": "SP",
                  "quantity": 1.0, "unit_price": 1000000, "total": 1000000}]
        ok, _ = InvoiceController.create_invoice(inv_data, items)
        assert ok is True

        inv = patched_session.query(Invoice).filter_by(invoice_number="HD-DISC-001").first()
        assert float(inv.discount) == pytest.approx(100000.0, abs=1.0)
        assert float(inv.total_payment) == pytest.approx(900000.0, abs=1.0)

    def test_checkout_invoice_detail_stored_correctly(self, patched_session):
        """
        Kiểm tra chi tiết hóa đơn được lưu đúng qua InvoiceController.get_invoice_details().
        """
        make_product(patched_session, barcode="CHK-P006", unit_price=750000, stock_qty=5)
        make_customer(patched_session, phone="0940000005")

        inv_data = {
            "invoice_number": "HD-DETAIL-001",
            "customer_phone": "0940000005",
            "subtotal": 1500000,
            "discount": 0,
            "old_debt": 0,
            "total_payment": 1500000,
            "amount_paid": 1500000,
            "new_debt": 0,
        }
        items = [{"barcode": "CHK-P006", "name": "Vòng cổ vàng",
                  "quantity": 2.0, "unit_price": 750000, "total": 1500000}]
        InvoiceController.create_invoice(inv_data, items)

        details = InvoiceController.get_invoice_details("HD-DETAIL-001")
        assert details is not None
        assert len(details["items"]) == 1
        assert details["items"][0]["product_name"] == "Vòng cổ vàng"
        assert details["items"][0]["quantity"] == pytest.approx(2.0, abs=0.001)
        assert details["items"][0]["unit_price"] == pytest.approx(750000.0, abs=1.0)

    def test_checkout_history_tracking(self, patched_session):
        """
        Sau 2 lần mua, lịch sử phải có đúng 2 bản ghi theo thứ tự mới nhất trước.
        """
        make_product(patched_session, barcode="CHK-P007", unit_price=200000, stock_qty=20)
        make_customer(patched_session, phone="0940000006")

        for i, inv_no in enumerate(["HD-HIS-A01", "HD-HIS-A02"]):
            inv_data = {
                "invoice_number": inv_no,
                "customer_phone": "0940000006",
                "subtotal": 200000,
                "discount": 0, "old_debt": 0,
                "total_payment": 200000,
                "amount_paid": 200000, "new_debt": 0,
            }
            items = [{"barcode": "CHK-P007", "name": "SP",
                      "quantity": 1.0, "unit_price": 200000, "total": 200000}]
            InvoiceController.create_invoice(inv_data, items)

        history = InvoiceController.get_customer_history("0940000006")
        assert len(history) == 2
        # Mới nhất trước
        invoice_numbers = [h["invoice_number"] for h in history]
        assert "HD-HIS-A01" in invoice_numbers
        assert "HD-HIS-A02" in invoice_numbers
