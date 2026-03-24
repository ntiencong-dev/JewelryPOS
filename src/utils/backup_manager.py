import json
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from PyQt5.QtWidgets import QMessageBox

from src.database.db_core import get_session
from src.models import Product, Customer, Invoice, InvoiceItem

def serialize_row(obj):
    row_dict = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            row_dict[column.name] = value.isoformat()
        elif isinstance(value, Decimal):
            row_dict[column.name] = float(value)
        else:
            row_dict[column.name] = value
    return row_dict

def export_database_to_json(filepath):
    session = get_session()
    try:
        data = {
            'products': [serialize_row(x) for x in session.query(Product).all()],
            'customers': [serialize_row(x) for x in session.query(Customer).all()],
            'invoices': [serialize_row(x) for x in session.query(Invoice).all()],
            'invoice_items': [serialize_row(x) for x in session.query(InvoiceItem).all()]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True, "Xuất dữ liệu thành công!"
    except Exception as e:
        return False, f"Lỗi khi xuất dữ liệu: {str(e)}"
    finally:
        session.close()

def restore_database_from_json(filepath):
    session = get_session()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not all(k in data for k in ['products', 'customers', 'invoices', 'invoice_items']):
            return False, "File backup không hợp lệ hoặc thiếu dữ liệu."

        # Xóa dữ liệu cũ theo thứ tự ràng buộc khóa ngoại (Foreign Key)
        session.query(InvoiceItem).delete()
        session.query(Invoice).delete()
        session.query(Customer).delete()
        session.query(Product).delete()
        session.flush()

        # Hàm parse lại datetime
        def parse_dates(row, date_fields):
            for field in date_fields:
                if row.get(field):
                    try:
                        row[field] = datetime.fromisoformat(row[field])
                    except:
                        pass
            return row

        # Insert Products
        products = [parse_dates(r, ['created_at', 'updated_at']) for r in data['products']]
        if products:
            session.bulk_insert_mappings(Product, products)
        
        # Insert Customers
        customers = [parse_dates(r, ['created_at']) for r in data['customers']]
        if customers:
            session.bulk_insert_mappings(Customer, customers)
        
        # Insert Invoices
        invoices = [parse_dates(r, ['sale_date']) for r in data['invoices']]
        if invoices:
            session.bulk_insert_mappings(Invoice, invoices)
        
        # Insert InvoiceItems
        if data['invoice_items']:
            session.bulk_insert_mappings(InvoiceItem, data['invoice_items'])

        session.commit()

        # Reset sequences in Postgres so next inserts don't fail with duplicate IDs
        tables = ['products', 'customers', 'invoices', 'invoice_items']
        for table in tables:
            try:
                session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {table};"))
            except Exception as seq_err:
                print(f"Warning: Could not reset sequence for {table}: {seq_err}")
                session.rollback() # sequence set val might fail if table is empty

        session.commit()
        return True, "Phục hồi dữ liệu thành công!"
    except Exception as e:
        session.rollback()
        return False, f"Lỗi khi phục hồi dữ liệu: {str(e)}"
    finally:
        session.close()
