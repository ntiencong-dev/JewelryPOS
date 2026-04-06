"""
Unit tests cho SQLAlchemy Models.
Kiểm tra model fields, defaults, và relationships.
"""
import pytest
from datetime import datetime
from src.models.product import Product
from src.models.customer import Customer
from src.models.invoice import Invoice, InvoiceItem


class TestProductModel:
    def test_product_creation_with_defaults(self, db_session):
        """Tạo Product với giá trị mặc định."""
        p = Product(
            barcode="MODEL-001",
            name="Test Nhẫn",
            unit="Chỉ",
            unit_price=500000
        )
        db_session.add(p)
        db_session.commit()

        saved = db_session.query(Product).filter_by(barcode="MODEL-001").first()
        assert saved is not None
        assert saved.name == "Test Nhẫn"
        assert float(saved.weight) == pytest.approx(0.0, abs=0.001)
        assert float(saved.base_price) == pytest.approx(0.0, abs=0.001)
        assert float(saved.stock_qty) == pytest.approx(0.0, abs=0.001)
        assert float(saved.min_stock_level) == pytest.approx(5.0, abs=0.001)
        assert saved.is_deleted is False

    def test_product_is_deleted_default_false(self, db_session):
        """is_deleted mặc định phải là False."""
        p = Product(barcode="MODEL-002", name="P2", unit="Cái", unit_price=100000)
        db_session.add(p)
        db_session.commit()
        saved = db_session.query(Product).filter_by(barcode="MODEL-002").first()
        assert saved.is_deleted is False

    def test_product_soft_delete(self, db_session):
        """Soft delete bằng cách đặt is_deleted=True."""
        p = Product(barcode="MODEL-003", name="P3", unit="Cái", unit_price=100000)
        db_session.add(p)
        db_session.commit()
        p.is_deleted = True
        db_session.commit()
        saved = db_session.query(Product).filter_by(barcode="MODEL-003").first()
        assert saved.is_deleted is True

    def test_product_repr(self, db_session):
        """__repr__ phải trả về chuỗi hợp lệ."""
        p = Product(barcode="MODEL-004", name="P4", unit="Chỉ", unit_price=50000)
        repr_str = repr(p)
        assert "MODEL-004" in repr_str
        assert "P4" in repr_str

    def test_product_barcode_unique(self, db_session):
        """Barcode phải là unique."""
        p1 = Product(barcode="UNIQ-001", name="P1", unit="Cái", unit_price=100000)
        p2 = Product(barcode="UNIQ-001", name="P2", unit="Cái", unit_price=200000)
        db_session.add(p1)
        db_session.commit()
        db_session.add(p2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()


class TestCustomerModel:
    def test_customer_creation(self, db_session):
        """Tạo Customer cơ bản."""
        c = Customer(
            name="Nguyễn Thị C",
            phone="0920000001",
            address="789 Trần Phú"
        )
        db_session.add(c)
        db_session.commit()

        saved = db_session.query(Customer).filter_by(phone="0920000001").first()
        assert saved is not None
        assert saved.name == "Nguyễn Thị C"
        assert float(saved.total_debt) == pytest.approx(0.0, abs=0.01)
        assert saved.is_deleted is False

    def test_customer_phone_unique(self, db_session):
        """Phone phải là unique."""
        c1 = Customer(name="C1", phone="0920000010")
        c2 = Customer(name="C2", phone="0920000010")
        db_session.add(c1)
        db_session.commit()
        db_session.add(c2)
        with pytest.raises(Exception):
            db_session.commit()
        db_session.rollback()

    def test_customer_debt_default_zero(self, db_session):
        """Nợ mặc định phải là 0."""
        c = Customer(name="C3", phone="0920000020")
        db_session.add(c)
        db_session.commit()
        saved = db_session.query(Customer).filter_by(phone="0920000020").first()
        assert float(saved.total_debt) == pytest.approx(0.0, abs=0.01)

    def test_customer_repr(self):
        """__repr__ phải chứa phone và name."""
        c = Customer(name="Test", phone="0920000030")
        r = repr(c)
        assert "Test" in r
        assert "0920000030" in r


class TestInvoiceModel:
    def test_invoice_creation(self, db_session):
        """Tạo Invoice cơ bản."""
        # Tạo customer trước
        c = Customer(name="KH Invoice", phone="0930000001")
        db_session.add(c)
        db_session.commit()

        inv = Invoice(
            invoice_number="INV-MODEL-001",
            customer_id=c.id,
            subtotal=1000000,
            discount=0,
            old_debt=0,
            total_payment=1000000,
            amount_paid=1000000,
            new_debt=0
        )
        db_session.add(inv)
        db_session.commit()

        saved = db_session.query(Invoice).filter_by(invoice_number="INV-MODEL-001").first()
        assert saved is not None
        assert float(saved.total_payment) == pytest.approx(1000000.0, abs=1.0)

    def test_invoice_item_relationship(self, db_session):
        """Invoice phải có relationship với InvoiceItem."""
        c = Customer(name="KH Rel", phone="0930000002")
        p = Product(barcode="REL-P001", name="P Rel", unit="Chỉ", unit_price=50000)
        db_session.add_all([c, p])
        db_session.commit()

        inv = Invoice(
            invoice_number="INV-REL-001",
            customer_id=c.id,
            subtotal=50000, discount=0, old_debt=0,
            total_payment=50000, amount_paid=50000, new_debt=0
        )
        db_session.add(inv)
        db_session.flush()

        item = InvoiceItem(
            invoice_id=inv.id, product_id=p.id,
            product_name="P Rel", quantity=1.0,
            unit_price=50000, total=50000
        )
        db_session.add(item)
        db_session.commit()

        saved_inv = db_session.query(Invoice).filter_by(invoice_number="INV-REL-001").first()
        assert len(saved_inv.items) == 1
        assert saved_inv.items[0].product_name == "P Rel"
