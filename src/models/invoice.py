from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.db_core import Base

class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True) # Có thể null nếu khách vãng lai không ghi nợ
    
    sale_date = Column(DateTime, default=datetime.now)
    
    # Chi tiết thanh toán & Công nợ theo yêu cầu phân tích
    subtotal = Column(Numeric(15, 2), default=0.0)      # Tổng cộng (Tiền hàng)
    discount = Column(Numeric(15, 2), default=0.0)      # Giảm giá
    old_debt = Column(Numeric(15, 2), default=0.0)      # Nợ cũ (Tại thời điểm mua)
    total_payment = Column(Numeric(15, 2), default=0.0) # Tổng thanh toán = (Subtotal - Discount) + old_debt
    amount_paid = Column(Numeric(15, 2), default=0.0)   # Tiền khách đưa thực tế
    new_debt = Column(Numeric(15, 2), default=0.0)      # Công nợ mới phát sinh/còn lại
    
    # Quan hệ
    customer = relationship("Customer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', total='{self.total_payment}')>"


class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Lưu lại snapshot thông tin sản phẩm lúc bán (tránh việc sửa tên/giá SP sau này làm sai lệch HĐ cũ)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 3), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total = Column(Numeric(15, 2), nullable=False) # Thành tiền = SL * Đơn giá

    # Quan hệ
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<InvoiceItem(name='{self.product_name}', qty={self.quantity}, total={self.total})>"