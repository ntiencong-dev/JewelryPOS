from src.database.db_core import get_session
from src.models.customer import Customer

class CustomerController:
    @staticmethod
    def get_all_customers(keyword=""):
        session = get_session()
        try:
            query = session.query(Customer).filter(Customer.is_deleted == False)
            
            if keyword:
                query = query.filter(
                    (Customer.phone.ilike(f"%{keyword}%")) |
                    (Customer.name.ilike(f"%{keyword}%"))
                )
            customers = query.order_by(Customer.id.desc()).all()
            result = []
            for c in customers:
                result.append({
                    "phone": c.phone,
                    "name": c.name,
                    "address": c.address or "",
                    "debt": str(c.total_debt)
                })
            return result
        finally:
            session.close()

    @staticmethod
    def add_customer(customer_data):
        session = get_session()
        try:
            # Kiểm tra SĐT
            exists = session.query(Customer).filter(Customer.phone == customer_data['phone']).first()
            if exists:
                return False, "Số điện thoại này đã tồn tại trong hệ thống!"

            new_cust = Customer(
                name=customer_data['name'],
                phone=customer_data['phone'],
                address=customer_data.get('address', '')
            )
            session.add(new_cust)
            session.commit()
            return True, "Thêm khách hàng thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_customer(phone):
        session = get_session()
        try:
            cust = session.query(Customer).filter(Customer.phone == phone).first()
            if not cust:
                return False, "Khách hàng không tồn tại!"

            # --- SOFT DELETE TRICK ---
            cust.is_deleted = True
            
            session.commit()
            return True, "Xóa (ẩn) khách hàng thành công!"
            
        except Exception as e:
            session.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            session.close()