import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.database.db_core import get_engine, Base
# Import model để Base ghi nhận tạo bảng
from src.models import Product, Customer, Invoice, InvoiceItem

def create_database_if_not_exists():
    def get_base_dir():
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

    load_dotenv(dotenv_path=os.path.join(get_base_dir(), 'config', '.env'))
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    db_name = os.getenv("DB_NAME", "jewelry_pos")
    
    try:
        # Cố gắng kết nối vào database mặc định 'postgres' để kiểm tra và tạo db mới
        conn = psycopg2.connect(dbname='postgres', user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Kiểm tra db tồn tại chưa
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{db_name}' chưa tồn tại. Đang tiến hành tạo mới...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Đã tạo database '{db_name}' thành công!")
        else:
            print(f"✅ Database '{db_name}' đã sẵn sàng.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra/tạo database: {e}")

def init_database():
    create_database_if_not_exists()
    print("Đang khởi tạo cấu trúc Cấu hình Database...")
    engine = get_engine()
    
    try:
        # Tạo toàn bộ table dựa trên schema của models
        Base.metadata.create_all(bind=engine)
        print("✅ Đã khởi tạo thành công các bảng: Products, Customers, Invoices, InvoiceItems!")
    except Exception as e:
        print(f"Chi tiết lỗi: {e}")

if __name__ == "__main__":
    init_database()