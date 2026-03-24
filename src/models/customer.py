from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database.db_core import Base

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, index=True)
    address = Column(String(500))
    total_debt = Column(Numeric(15, 2), default=0.0)  # Tổng công nợ hiện tại
    created_at = Column(DateTime, default=datetime.now)

    # Quan hệ 1-N với Hóa đơn
    invoices = relationship("Invoice", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(name='{self.name}', phone='{self.phone}', debt={self.total_debt})>"