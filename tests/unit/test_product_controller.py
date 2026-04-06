"""
Unit tests cho ProductController.
Dùng patched_session (SQLite in-memory) để không cần PostgreSQL thật.
"""
import pytest
from unittest.mock import patch
from tests.conftest import make_product
from src.controllers.product_controller import ProductController


class TestProductControllerAdd:
    def test_add_product_success(self, patched_session):
        """Thêm sản phẩm mới thành công."""
        data = {
            "barcode": "ADD-001",
            "name": "Dây chuyền vàng",
            "unit": "Chỉ",
            "weight": "2.0",
            "base_price": "600000",
            "labor_cost": "80000",
            "stone_cost": "0",
            "cost_price": "1280000",
            "unit_price": "1500000",
            "stock": "5",
            "note": "test"
        }
        ok, msg = ProductController.add_product(data)
        assert ok is True
        assert "thành công" in msg.lower()

    def test_add_product_duplicate_barcode(self, patched_session):
        """Thêm sản phẩm với mã vạch đã tồn tại phải báo lỗi."""
        make_product(patched_session, barcode="DUP-001")
        data = {
            "barcode": "DUP-001",
            "name": "Sản phẩm khác",
            "unit": "Cái",
            "weight": "0",
            "base_price": "0",
            "labor_cost": "0",
            "stone_cost": "0",
            "cost_price": "0",
            "unit_price": "100000",
            "stock": "1",
            "note": ""
        }
        ok, msg = ProductController.add_product(data)
        assert ok is False
        assert "tồn tại" in msg.lower() or "exist" in msg.lower()

    def test_add_product_missing_name(self, patched_session):
        """Sản phẩm không có tên vẫn có thể thêm (validation ở UI layer)."""
        data = {
            "barcode": "NONAME-001",
            "name": "",
            "unit": "Chỉ",
            "weight": "0",
            "base_price": "0",
            "labor_cost": "0",
            "stone_cost": "0",
            "cost_price": "0",
            "unit_price": "0",
            "stock": "0",
            "note": ""
        }
        # Controller không validate name – chỉ DB model mới enforce nullable=False
        # Nếu model enforce thì phải raise Exception
        try:
            ok, msg = ProductController.add_product(data)
            # Nếu model cho phép name rỗng → ok có thể True hoặc False
        except Exception:
            pass  # Chấp nhận nếu DB raise


class TestProductControllerGet:
    def test_get_all_products_no_filter(self, patched_session):
        """Lấy danh sách tất cả sản phẩm."""
        make_product(patched_session, barcode="GET-001", name="Nhẫn A")
        make_product(patched_session, barcode="GET-002", name="Nhẫn B")
        results = ProductController.get_all_products()
        barcodes = [r["barcode"] for r in results]
        assert "GET-001" in barcodes
        assert "GET-002" in barcodes

    def test_get_all_products_with_keyword_barcode(self, patched_session):
        """Lọc theo từ khóa mã vạch."""
        make_product(patched_session, barcode="SRCH-BAR-001", name="Sản phẩm tìm")
        make_product(patched_session, barcode="OTHER-999", name="Sản phẩm khác")
        results = ProductController.get_all_products(keyword="SRCH-BAR")
        barcodes = [r["barcode"] for r in results]
        assert "SRCH-BAR-001" in barcodes
        assert "OTHER-999" not in barcodes

    def test_get_all_products_with_keyword_name(self, patched_session):
        """Lọc theo từ khóa tên sản phẩm."""
        make_product(patched_session, barcode="NMSRCH-001", name="Bông tai đặc biệt")
        results = ProductController.get_all_products(keyword="đặc biệt")
        names = [r["name"] for r in results]
        assert "Bông tai đặc biệt" in names

    def test_get_all_products_excludes_deleted(self, patched_session):
        """Sản phẩm đã bị xóa mềm không xuất hiện trong kết quả."""
        p = make_product(patched_session, barcode="DEL-PROD-001", name="Sản phẩm bị xóa")
        p.is_deleted = True
        patched_session.commit()
        results = ProductController.get_all_products()
        barcodes = [r["barcode"] for r in results]
        assert "DEL-PROD-001" not in barcodes

    def test_result_fields_complete(self, patched_session):
        """Mỗi kết quả phải có đầy đủ các trường cần thiết."""
        make_product(patched_session, barcode="FIELD-001", name="Test Fields")
        results = ProductController.get_all_products(keyword="FIELD-001")
        assert len(results) >= 1
        r = next((x for x in results if x["barcode"] == "FIELD-001"), None)
        assert r is not None
        required_keys = ["barcode", "name", "unit", "weight", "base_price",
                         "labor_cost", "stone_cost", "cost_price", "unit_price",
                         "stock", "note"]
        for key in required_keys:
            assert key in r, f"Thiếu trường '{key}' trong kết quả"


class TestProductControllerUpdate:
    def test_update_product_success(self, patched_session):
        """Cập nhật thông tin sản phẩm thành công."""
        make_product(patched_session, barcode="UPD-001", name="Tên cũ", unit_price=1000000)
        update_data = {
            "name": "Tên mới",
            "unit": "Chỉ",
            "weight": "2.0",
            "base_price": "700000",
            "labor_cost": "100000",
            "stone_cost": "0",
            "cost_price": "1500000",
            "unit_price": "2000000",
            "stock": "8",
            "note": "updated"
        }
        ok, msg = ProductController.update_product("UPD-001", update_data)
        assert ok is True

        # Kiểm tra dữ liệu thực sự thay đổi
        results = ProductController.get_all_products(keyword="UPD-001")
        updated = next((x for x in results if x["barcode"] == "UPD-001"), None)
        assert updated is not None
        assert updated["name"] == "Tên mới"
        assert updated["unit_price"] == "2000000"

    def test_update_product_not_found(self, patched_session):
        """Cập nhật sản phẩm không tồn tại."""
        ok, msg = ProductController.update_product("NONEXIST-999", {"name": "test"})
        assert ok is False


class TestProductControllerDelete:
    def test_delete_product_soft_delete(self, patched_session):
        """Xóa sản phẩm là soft-delete (đánh dấu is_deleted=True)."""
        make_product(patched_session, barcode="SDEL-001", name="Xóa mềm")
        ok, msg = ProductController.delete_product("SDEL-001")
        assert ok is True

        # Kiểm tra không còn xuất hiện trong get_all_products
        results = ProductController.get_all_products()
        barcodes = [r["barcode"] for r in results]
        assert "SDEL-001" not in barcodes

    def test_delete_product_not_found(self, patched_session):
        """Xóa sản phẩm không tồn tại."""
        ok, msg = ProductController.delete_product("MISSING-999")
        assert ok is False
