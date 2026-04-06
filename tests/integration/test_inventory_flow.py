"""
Integration tests – Luồng Quản lý Kho (Inventory Flow).
Test luồng thêm, sửa, xóa sản phẩm và tìm kiếm.
"""
import pytest
from tests.conftest import make_product
from src.controllers.product_controller import ProductController
from src.models.product import Product


class TestInventoryFlow:
    """Kiểm tra luồng quản lý kho tích hợp."""

    def test_add_then_search_product(self, patched_session):
        """
        Kịch bản: Thêm sản phẩm → Tìm kiếm bằng tên → Phải tìm thấy.
        """
        data = {
            "barcode": "INVFLOW-001",
            "name": "Bông tai ngọc trai",
            "unit": "Đôi",
            "weight": "1.2",
            "base_price": "300000",
            "labor_cost": "50000",
            "stone_cost": "200000",
            "cost_price": "610000",
            "unit_price": "900000",
            "stock": "8",
            "note": "Hàng cao cấp"
        }
        ok, _ = ProductController.add_product(data)
        assert ok is True

        results = ProductController.get_all_products(keyword="ngọc trai")
        names = [r["name"] for r in results]
        assert "Bông tai ngọc trai" in names

    def test_add_then_update_product(self, patched_session):
        """
        Kịch bản: Thêm sản phẩm → Cập nhật giá bán → Kiểm tra giá mới.
        """
        make_product(patched_session, barcode="INVFLOW-002",
                     name="Nhẫn cũ", unit_price=500000)

        update_data = {
            "name": "Nhẫn cập nhật",
            "unit": "Chỉ",
            "weight": "1.5",
            "base_price": "500000",
            "labor_cost": "60000",
            "stone_cost": "0",
            "cost_price": "810000",
            "unit_price": "1200000",
            "stock": "5",
            "note": "Cập nhật giá mới"
        }
        ok, _ = ProductController.update_product("INVFLOW-002", update_data)
        assert ok is True

        results = ProductController.get_all_products(keyword="INVFLOW-002")
        updated = next((r for r in results if r["barcode"] == "INVFLOW-002"), None)
        assert updated is not None
        assert updated["name"] == "Nhẫn cập nhật"
        assert updated["unit_price"] == "1200000"

    def test_add_then_delete_product(self, patched_session):
        """
        Kịch bản: Thêm sản phẩm → Xóa → Sản phẩm không còn xuất hiện.
        """
        make_product(patched_session, barcode="INVFLOW-003", name="Sẽ bị xóa")

        ok, _ = ProductController.delete_product("INVFLOW-003")
        assert ok is True

        results = ProductController.get_all_products()
        barcodes = [r["barcode"] for r in results]
        assert "INVFLOW-003" not in barcodes

    def test_deleted_product_not_searchable(self, patched_session):
        """
        Sản phẩm đã xóa mềm không thể tìm thấy qua search.
        """
        p = make_product(patched_session, barcode="INVFLOW-004", name="Sản phẩm ẩn")
        p.is_deleted = True
        patched_session.commit()

        results = ProductController.get_all_products(keyword="INVFLOW-004")
        barcodes = [r["barcode"] for r in results]
        assert "INVFLOW-004" not in barcodes

    def test_search_returns_multiple_matching_products(self, patched_session):
        """
        Tìm từ khóa chung phải trả về nhiều kết quả.
        """
        make_product(patched_session, barcode="GRPSRCH-001", name="Nhẫn vàng 18k loại A")
        make_product(patched_session, barcode="GRPSRCH-002", name="Nhẫn vàng 18k loại B")
        make_product(patched_session, barcode="GRPSRCH-003", name="Nhẫn vàng 18k loại C")

        results = ProductController.get_all_products(keyword="Nhẫn vàng 18k")
        barcodes = [r["barcode"] for r in results]
        assert "GRPSRCH-001" in barcodes
        assert "GRPSRCH-002" in barcodes
        assert "GRPSRCH-003" in barcodes

    def test_update_stock_quantity(self, patched_session):
        """
        Cập nhật tồn kho của sản phẩm.
        """
        make_product(patched_session, barcode="INVFLOW-005", stock_qty=10.0)

        update_data = {
            "name": "SP5",
            "unit": "Chỉ",
            "weight": "1.0",
            "base_price": "500000",
            "labor_cost": "0",
            "stone_cost": "0",
            "cost_price": "500000",
            "unit_price": "700000",
            "stock": "25",
            "note": ""
        }
        ok, _ = ProductController.update_product("INVFLOW-005", update_data)
        assert ok is True

        prod = patched_session.query(Product).filter_by(barcode="INVFLOW-005").first()
        assert float(prod.stock_qty) == pytest.approx(25.0, abs=0.001)

    def test_barcode_search_prefix(self, patched_session):
        """
        Tìm theo prefix mã vạch phải trả về tất cả matching.
        """
        make_product(patched_session, barcode="PREFIX-A001", name="SP A001")
        make_product(patched_session, barcode="PREFIX-A002", name="SP A002")
        make_product(patched_session, barcode="NOPREFIX-001", name="SP No Match")

        results = ProductController.get_all_products(keyword="PREFIX-A")
        barcodes = [r["barcode"] for r in results]
        assert "PREFIX-A001" in barcodes
        assert "PREFIX-A002" in barcodes
        assert "NOPREFIX-001" not in barcodes

    def test_cost_price_fields_preserved(self, patched_session):
        """
        Các trường giá vốn (weight, base_price, labor_cost, stone_cost) được lưu đúng.
        """
        make_product(patched_session, barcode="INVFLOW-006",
                     weight=2.5, base_price=700000,
                     labor_cost=120000, stone_cost=50000,
                     cost_price=1870000)

        results = ProductController.get_all_products(keyword="INVFLOW-006")
        assert len(results) >= 1
        r = next(x for x in results if x["barcode"] == "INVFLOW-006")
        # Dùng float để tránh khác biệt format Decimal (SQLite: '2.500', PostgreSQL: '2.5')
        assert float(r["weight"]) == pytest.approx(2.5, abs=0.001)
        assert int(float(r["base_price"])) == 700000
        assert int(float(r["labor_cost"])) == 120000
        assert int(float(r["stone_cost"])) == 50000
        assert int(float(r["cost_price"])) == 1870000
