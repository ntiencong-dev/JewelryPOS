"""
conftest.py – Pytest fixtures dùng chung cho toàn bộ test suite JewelryPOS.

Chiến lược đúng:
- Dùng SQLite in-memory thay cho PostgreSQL.
- Patch get_session() TẠI TỪNG CONTROLLER MODULE (không phải db_core)
  vì controllers đã import local reference: `from src.database.db_core import get_session`
- Override session.close() thành no-op để controller's finally block
  không đóng session trước khi fixture cleanup.
"""
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Đảm bảo root project trong sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Patch biến môi trường TRƯỚC KHI import bất kỳ module src nào
os.environ["DB_USER"] = "test"
os.environ["DB_PASS"] = "test"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "jewelry_pos_test"

# Import Base SAU khi set env vars
from src.database.db_core import Base  # noqa: E402


# ---------------------------------------------------------------------------
# SQLite in-memory engine – tạo 1 lần cho cả session pytest
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def sqlite_engine():
    """Tạo SQLite in-memory engine và tạo tất cả bảng."""
    # Import models để đăng ký với Base.metadata
    import src.models.product   # noqa: F401
    import src.models.customer  # noqa: F401
    import src.models.invoice   # noqa: F401

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="session")
def SessionFactory(sqlite_engine):
    return sessionmaker(bind=sqlite_engine)


@pytest.fixture()
def db_session(SessionFactory):
    """
    Session SQLite thuần (dùng cho test Models trực tiếp).
    Mỗi test nhận session mới, rollback sau khi chạy xong.
    """
    session = SessionFactory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def patched_session(db_session, monkeypatch):
    """
    Fixture QUAN TRỌNG cho Controller tests:

    1. Patch get_session() trong TỪNG controller module (vì controllers
       đã `from src.database.db_core import get_session` – tạo local binding,
       nên patch db_core không ảnh hưởng).

    2. Ghi đè session.close() = no-op để controller's finally block
       không đóng session sớm (sẽ cleanup trong fixture teardown).
    """
    import src.controllers.product_controller as pc
    import src.controllers.customer_controller as cc
    import src.controllers.invoice_controller as ic

    # Patch get_session tại từng module controller
    monkeypatch.setattr(pc, "get_session", lambda: db_session)
    monkeypatch.setattr(cc, "get_session", lambda: db_session)
    monkeypatch.setattr(ic, "get_session", lambda: db_session)

    # Prevent controllers' finally: session.close() từ đóng session sớm
    original_close = db_session.close
    db_session.close = lambda: None  # no-op trong suốt test

    yield db_session

    # Restore close rồi thực sự cleanup
    db_session.close = original_close


# ---------------------------------------------------------------------------
# Helper functions tạo dữ liệu mẫu
# ---------------------------------------------------------------------------
from src.models.product import Product   # noqa: E402
from src.models.customer import Customer  # noqa: E402


def make_product(session, barcode="TEST-001", name="Nhẫn vàng 18k",
                 unit="Chỉ", weight=1.5, base_price=500000,
                 labor_cost=50000, stone_cost=0, cost_price=800000,
                 unit_price=1000000, stock_qty=10.0):
    p = Product(
        barcode=barcode, name=name, unit=unit,
        weight=weight, base_price=base_price,
        labor_cost=labor_cost, stone_cost=stone_cost,
        cost_price=cost_price, unit_price=unit_price,
        stock_qty=stock_qty, min_stock_level=5.0,
        note="", is_deleted=False,
    )
    session.add(p)
    session.commit()
    return p


def make_customer(session, phone="0901234567", name="Nguyễn Văn A",
                  address="123 Lý Thường Kiệt", total_debt=0.0):
    c = Customer(
        phone=phone, name=name, address=address,
        total_debt=total_debt, is_deleted=False,
    )
    session.add(c)
    session.commit()
    return c
