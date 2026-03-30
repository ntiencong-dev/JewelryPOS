from src.database.db_core import get_session
from src.models.product import Product

class ProductController:
    @staticmethod
    def get_all_products(keyword=""):
        session = get_session()
        try:
            query = session.query(Product)
            if keyword:
                query = query.filter(
                    (Product.barcode.ilike(f"{keyword}%")) |
                    (Product.name.ilike(f"%{keyword}%"))
                )
            products = query.order_by(Product.id.desc()).all()
            result = []
            for p in products:
                result.append({
                    "barcode": p.barcode,
                    "name": p.name,
                    "unit": p.unit,
                    "weight": str(p.weight),
                    "base_price": str(int(p.base_price)),
                    "labor_cost": str(int(p.labor_cost)),
                    "stone_cost": str(int(p.stone_cost)),
                    "price": float(p.unit_price),
                    "cost_price": str(int(p.cost_price)),
                    "unit_price": str(int(p.unit_price)),
                    "stock": str(int(p.stock_qty)),
                    "min_stock": str(int(p.min_stock_level)),
                    "note": p.note or ""
                })
            return result
        finally:
            session.close()

    @staticmethod
    def search_by_barcode_prefix(prefix=""):
        session = get_session()
        try:
            query = session.query(Product)
            if prefix:
                query = query.filter(
                    (Product.barcode.ilike(f"{prefix}%")) |
                    (Product.name.ilike(f"%{prefix}%"))
                )
            products = query.order_by(Product.id.desc()).all()
            result = []
            for p in products:
                result.append({
                    "barcode": p.barcode,
                    "name": p.name,
                    "unit": p.unit,
                    "cost_price": str(int(p.cost_price)),
                    "unit_price": str(int(p.unit_price)),
                    "stock": str(int(p.stock_qty)),
                    "min_stock": str(int(p.min_stock_level))
                })
            return result
        finally:
            session.close()

    @staticmethod
    def add_product(product_data):
        session = get_session()
        try:
            exists = session.query(Product).filter(Product.barcode == product_data['barcode']).first()
            if exists:
                return False, "Mã vạch này đã tồn tại trong hệ thống!"

            new_prod = Product(
                barcode=product_data['barcode'],
                name=product_data['name'],
                unit=product_data['unit'],
                weight=float(product_data.get('weight', 0)),
                base_price=float(product_data.get('base_price', 0)),
                labor_cost=float(product_data.get('labor_cost', 0)),
                stone_cost=float(product_data.get('stone_cost', 0)),
                cost_price=float(product_data.get('cost_price', 0)),
                unit_price=float(product_data.get('unit_price', 0)),
                stock_qty=float(product_data.get('stock', 0)),
                min_stock_level=5.0,
                note=product_data.get('note', "")
            )
            session.add(new_prod)
            session.commit()
            return True, "Thêm sản phẩm thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def update_product(barcode, update_data):
        session = get_session()
        try:
            prod = session.query(Product).filter(Product.barcode == barcode).first()
            if not prod:
                return False, "Sản phẩm không tồn tại!"
            
            prod.name = update_data.get('name', prod.name)
            prod.unit = update_data.get('unit', prod.unit)
            prod.weight = float(update_data.get('weight', prod.weight))
            prod.base_price = float(update_data.get('base_price', prod.base_price))
            prod.labor_cost = float(update_data.get('labor_cost', prod.labor_cost))
            prod.stone_cost = float(update_data.get('stone_cost', prod.stone_cost))
            prod.cost_price = float(update_data.get('cost_price', prod.cost_price))
            prod.unit_price = float(update_data.get('unit_price', prod.unit_price))
            prod.stock_qty = float(update_data.get('stock', prod.stock_qty))
            prod.note = update_data.get('note', prod.note)
            
            session.commit()
            return True, "Cập nhật sản phẩm thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            session.close()

    @staticmethod
    def delete_product(barcode):
        session = get_session()
        try:
            prod = session.query(Product).filter(Product.barcode == barcode).first()
            if not prod:
                return False, "Sản phẩm không tồn tại!"
            
            session.delete(prod)
            session.commit()
            return True, "Xóa sản phẩm thành công!"
        except Exception as e:
            session.rollback()
            return False, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            session.close()