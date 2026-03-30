from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Boolean
from datetime import datetime
from src.database.db_core import Base

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(100), unique=True, nullable=False, index=True) 
    name = Column(String(255), nullable=False)
    unit = Column(String(50)) 
    
    # Các trường cấu thành Giá Vốn
    weight = Column(Numeric(10, 3), default=0.0)      # Khối lượng
    base_price = Column(Numeric(15, 2), default=0.0)  # Đơn giá (Vật tư)
    labor_cost = Column(Numeric(15, 2), default=0.0)  # Tiền công
    stone_cost = Column(Numeric(15, 2), default=0.0)  # Tiền hột
    cost_price = Column(Numeric(15, 2), default=0.0)  # Giá vốn (Được tự động tính)
    
    unit_price = Column(Numeric(15, 2), nullable=False) # Giá bán lẻ
    stock_qty = Column(Numeric(10, 3), default=0.0) 
    min_stock_level = Column(Numeric(10, 3), default=5.0) 
    
    note = Column(Text, nullable=True) # Cột ghi chú mới
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Product(barcode='{self.barcode}', name='{self.name}', stock={self.stock_qty})>"