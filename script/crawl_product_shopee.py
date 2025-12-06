import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
logging.basicConfig(level=logging.INFO)
from library.shopeev2 import Shopee
from datetime import datetime
from datetime import timedelta
from library.helper import Helper
from library.postgres import Postgres
import json

SOURCE = "DUNI_SHOPEE"
shopee = Shopee(SOURCE)
pg = Postgres()
pg.connect()
products = shopee.get_products(page_number=1)['data']['products']
for product in products:
    logging.info(f"Inserting/Updating product: id: {product['id']} name: {product['name']} cover_image: {product['cover_image']}")
    query = """
        INSERT INTO ecom_products (id, name, cover_image)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            cover_image = EXCLUDED.cover_image
    """
    params = (product['id'], product['name'], f"https://cf.shopee.vn/{product['cover_image']}", SOURCE)
    pg.execute(query, params)
    for sku in product['model_list']:
        # Check if SKU already exists
        check_query = """
            SELECT id FROM ecom_sku_products 
            WHERE product_id = %s AND id = %s
        """
        existing_sku = pg.fetch_one(check_query, (product['id'], sku['id']))
        
        if existing_sku:
            # Update existing SKU
            update_query = """
                UPDATE ecom_sku_products 
                SET name = %s, image = %s
                WHERE product_id = %s AND id = %s
            """
            pg.execute(update_query, (sku['name'], f"https://cf.shopee.vn/{sku['image']}", product['id'], sku['id']))
            logging.info(f"Updated product: {product['id']} sku: {sku['id']}")
        else:
            # Insert new SKU
            insert_query = """
                INSERT INTO ecom_sku_products (product_id, id, name, image)
                VALUES (%s, %s, %s, %s)
            """
            pg.execute(insert_query, (product['id'], sku['id'], sku['name'], f"https://cf.shopee.vn/{sku['image']}"))
            logging.info(f"Inserted product: {product['id']} sku: {sku['id']}")
    logging.info(f"Inserted/Updated product: {product['id']}")

pg.commit()
pg.disconnect()