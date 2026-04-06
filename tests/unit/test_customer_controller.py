"""
Unit tests cho CustomerController.
"""
import pytest
from tests.conftest import make_customer
from src.controllers.customer_controller import CustomerController


class TestCustomerControllerAdd:
    def test_add_customer_success(self, patched_session):
        """Thêm khách hàng mới thành công."""
        data = {
            "phone": "0901000001",
            "name": "Trần Thị B",
            "address": "456 Nguyễn Huệ"
        }
        ok, msg = CustomerController.add_customer(data)
        assert ok is True
        assert "thành công" in msg.lower()

    def test_add_customer_duplicate_phone(self, patched_session):
        """Thêm khách hàng với SĐT đã tồn tại phải báo lỗi."""
        make_customer(patched_session, phone="0901000002", name="KH A")
        data = {
            "phone": "0901000002",
            "name": "KH B trùng số",
            "address": ""
        }
        ok, msg = CustomerController.add_customer(data)
        assert ok is False
        assert "tồn tại" in msg.lower()

    def test_add_customer_no_address(self, patched_session):
        """Thêm khách hàng không có địa chỉ vẫn thành công."""
        data = {
            "phone": "0901000003",
            "name": "KH Không Địa Chỉ",
            "address": ""
        }
        ok, msg = CustomerController.add_customer(data)
        assert ok is True


class TestCustomerControllerGet:
    def test_get_all_customers_no_filter(self, patched_session):
        """Lấy tất cả khách hàng không bị xóa."""
        make_customer(patched_session, phone="0902000001", name="KH Test 1")
        make_customer(patched_session, phone="0902000002", name="KH Test 2")
        results = CustomerController.get_all_customers()
        phones = [r["phone"] for r in results]
        assert "0902000001" in phones
        assert "0902000002" in phones

    def test_get_all_customers_filter_by_phone(self, patched_session):
        """Lọc theo số điện thoại."""
        make_customer(patched_session, phone="0903000001", name="KH Lọc")
        results = CustomerController.get_all_customers("0903000001")
        assert len(results) >= 1
        assert results[0]["phone"] == "0903000001"

    def test_get_all_customers_filter_by_name(self, patched_session):
        """Lọc theo tên khách hàng."""
        make_customer(patched_session, phone="0904000001", name="Lê Thị Hoa")
        results = CustomerController.get_all_customers("Lê Thị Hoa")
        names = [r["name"] for r in results]
        assert "Lê Thị Hoa" in names

    def test_get_all_customers_excludes_deleted(self, patched_session):
        """Khách hàng đã xóa mềm không xuất hiện."""
        c = make_customer(patched_session, phone="0905000001", name="KH Đã Xóa")
        c.is_deleted = True
        patched_session.commit()
        results = CustomerController.get_all_customers()
        phones = [r["phone"] for r in results]
        assert "0905000001" not in phones

    def test_result_fields_complete(self, patched_session):
        """Kết quả phải chứa đủ các trường phone, name, address, debt."""
        make_customer(patched_session, phone="0906000001", name="KH Fields")
        results = CustomerController.get_all_customers("0906000001")
        assert len(results) >= 1
        r = results[0]
        for key in ["phone", "name", "address", "debt"]:
            assert key in r, f"Thiếu trường '{key}'"


class TestCustomerControllerDelete:
    def test_delete_customer_soft_delete(self, patched_session):
        """Xóa khách hàng là soft-delete."""
        make_customer(patched_session, phone="0907000001", name="KH Xóa")
        ok, msg = CustomerController.delete_customer("0907000001")
        assert ok is True
        # Kiểm tra không còn xuất hiện
        results = CustomerController.get_all_customers()
        phones = [r["phone"] for r in results]
        assert "0907000001" not in phones

    def test_delete_customer_not_found(self, patched_session):
        """Xóa khách hàng không tồn tại."""
        ok, msg = CustomerController.delete_customer("0000000000")
        assert ok is False
        assert "không tồn tại" in msg.lower()
