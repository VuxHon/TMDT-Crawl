import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
logging.basicConfig(level=logging.INFO)
from library.tiktok import Tiktok
from datetime import datetime
from datetime import timedelta
from library.helper import Helper
from library.postgres import Postgres
import json

db = Postgres()
TYPE = ['OVS', 'HD', 'HDZ', 'BBT', 'SWT', 'PL']
COLOR = ['Trăng', 'Trắg', 'Trg', 'Đen', 'Xanh', 'Be', 'Xám', 'Trắng', 'Nâu']
SIZE = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL']

def update_sku_inventory_type():
    for type in TYPE:
        for color in COLOR:
            for size in SIZE:
                sku_inventory_name = f"{type},{color},{size}"
                query_update = """
                    update ecom_sku_products
                        set sku_inventory_name = %s
                        where name like %s
                        and name ILIKE %s
                        and name like %s
                    """
                params = (sku_inventory_name, f"%{type}%", f"%{color}%", f"%,{size}%")
                db.execute(query_update, params)
                db.commit()
                logging.info(f"Updated {sku_inventory_name}")

def update_sku_inventory_none_type():
    for color in COLOR:
        for size in SIZE:
            sku_inventory_name = f"OVS,{color},{size}"
            query_update = """
                update ecom_sku_products
                    set sku_inventory_name = %s
                    where name ILIKE %s
                    and name like %s
                    and sku_inventory_name is null
                """
            params = (sku_inventory_name, f"%{color}%", f"%, {size}%")
            db.execute(query_update, params)
            db.commit()
            logging.info(f"Updated {sku_inventory_name}")
            
# update_sku_inventory_type()
update_sku_inventory_none_type()