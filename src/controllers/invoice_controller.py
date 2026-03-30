from src.database.db_core import get_session
from src.models.invoice import Invoice, InvoiceItem
from src.models.customer import Customer
from src.models.product import Product
from datetime import datetime

class InvoiceController:
    @staticmethod
    def create_invoice(invoice_data, items_data):
        """
        Creates an invoice, saves invoice items, deducts product stock,
        and updates customer debt inside a single transaction.
        
        invoice_data structure:
        {
            "invoice_number": str,
            "customer_phone": str, (to lookup customer id)
            "subtotal": float,
            "discount": float,
            "old_debt": float,
            "total_payment": float,
            "amount_paid": float,
            "new_debt": float
        }
        
        items_data structure: list of dicts
        [
            {
                "barcode": str,
                "name": str,
                "quantity": float,
                "unit_price": float,
                "total": float
            }
        ]
        """
        session = get_session()
        try:
            # 1. Tìm Customer dựa trên số điện thoại
            customer_phone = invoice_data.get("customer_phone")
            customer = session.query(Customer).filter(Customer.phone == customer_phone).first()
            
            if not customer:
                return False, "Không tìm thấy khách hàng. Đơn hàng phải có khách hàng!"

            # 2. Tạo Hóa đơn
            new_invoice = Invoice(
                invoice_number=invoice_data["invoice_number"],
                customer_id=customer.id,
                sale_date=datetime.now(),
                subtotal=invoice_data["subtotal"],
                discount=invoice_data["discount"],
                old_debt=invoice_data["old_debt"],
                total_payment=invoice_data["total_payment"],
                amount_paid=invoice_data["amount_paid"],
                new_debt=invoice_data["new_debt"]
            )
            session.add(new_invoice)
            session.flush() # Lấy new_invoice.id

            # 3. Tạo Chi tiết hóa đơn và trừ tồn kho
            for item in items_data:
                # Lấy product_id
                product = session.query(Product).filter(Product.barcode == item["barcode"]).first()
                if not product:
                    # Chuyện gì xảy ra nếu sản phẩm không tồn tại trong CSDL nữa? -> Bỏ qua mã lỗi xử lý cơ bản
                    session.rollback()
                    return False, f"Không tìm thấy sản phẩm có mã {item['barcode']} trong CSDL."
                
                # Trừ tồn kho
                if product.unit != "Công":
                    product.stock_qty = float(product.stock_qty) - float(item["quantity"])

                # Tạo item
                new_item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    product_id=product.id,
                    product_name=item["name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total=item["total"]
                )
                session.add(new_item)

            # 4. Cập nhật nợ mới cho khách hàng
            customer.total_debt = invoice_data["new_debt"]

            session.commit()
            return True, "Thanh toán thành công và đã lưu lịch sử giao dịch!"

        except Exception as e:
            session.rollback()
            return False, f"Lỗi chức năng thanh toán: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def get_customer_history(customer_phone):
        session = get_session()
        try:
            customer = session.query(Customer).filter(Customer.phone == customer_phone).first()
            if not customer:
                return []
            
            invoices = session.query(Invoice).filter(Invoice.customer_id == customer.id).order_by(Invoice.sale_date.desc()).all()
            
            result = []
            for inv in invoices:
                result.append({
                    "date": inv.sale_date.strftime("%d/%m/%Y %H:%M"),
                    "invoice_number": inv.invoice_number,
                    "total_payment": float(inv.total_payment),
                    "amount_paid": float(inv.amount_paid),
                    "new_debt": float(inv.new_debt)
                })
            
            return result
        finally:
            session.close()

    @staticmethod
    def get_invoice_details(invoice_number):
        session = get_session()
        try:
            invoice = session.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
            if not invoice:
                return None
            
            result = {
                "invoice_number": invoice.invoice_number,
                "date": invoice.sale_date.strftime("%d/%m/%Y %H:%M"),
                "subtotal": float(invoice.subtotal),
                "discount": float(invoice.discount),
                "total_payment": float(invoice.total_payment),
                "amount_paid": float(invoice.amount_paid),
                "new_debt": float(invoice.new_debt),
                "items": []
            }
            for item in invoice.items:
                result["items"].append({
                    "product_name": item.product_name,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "total": float(item.total)
                })
            return result
        finally:
            session.close()
