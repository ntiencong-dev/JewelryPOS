# Export tất cả các model để khi khởi tạo database SQLAlchemy có thể nhận diện được
from .product import Product
from .customer import Customer
from .invoice import Invoice, InvoiceItem

__all__ = ["Product", "Customer", "Invoice", "InvoiceItem"]