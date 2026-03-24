from sqlalchemy import Column, Integer, String, Numeric, DateTime
from datetime import datetime
from src.database.db_core import Base

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(100), unique=True, nullable=False, index=True) # Mã SKU / Barcode quét
    name = Column(String(255), nullable=False)
    unit = Column(String(50)) # Đơn vị tính: Chỉ, Phân, Gam, Cái...
    cost_price = Column(Numeric(15, 2), default=0.0) # Giá vốn (để tính lãi)
    unit_price = Column(Numeric(15, 2), nullable=False) # Giá bán lẻ
    stock_qty = Column(Numeric(10, 3), default=0.0) # Tồn kho (Numeric hỗ trợ số thập phân cho Gam/Chỉ)
    min_stock_level = Column(Numeric(10, 3), default=5.0) # Mức báo động sắp hết hàng
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Product(barcode='{self.barcode}', name='{self.name}', stock={self.stock_qty})>"