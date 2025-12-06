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

SOURCE = "DUNI_TIKTOK"
tiktok = Tiktok(SOURCE)
pg = Postgres()
pg.connect()

def bulk_insert_product(_number_page=1):
    for page in range(1, _number_page):
        products = tiktok.get_products(page=page)['products']
        for product in products:
            image = product['images'][0]['url_list'][0]
            logging.info(f"Inserting/Updating product: id: {product['product_id']} name: {product['product_title']} cover_image: {image}")
            query = """
                INSERT INTO ecom_products (id, name, cover_image)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    cover_image = EXCLUDED.cover_image
            """
            params = (int(product['product_id']), product['product_title'], image)
            pg.execute(query, params)
            bulk_insert_sku(product['skus'])

def bulk_insert_sku(skus):
    for sku in skus:
        # Check if SKU already exists
        sku_name = ', '.join([s['value_name'] for s in sku['properties']])
        image = sku['images'][0]['url_list'][0]
        query = """
            INSERT INTO ecom_sku_products (product_id, id, name, image)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id, id) DO UPDATE SET
                name = EXCLUDED.name,
                image = EXCLUDED.image,
                product_id = EXCLUDED.product_id,
                id = EXCLUDED.id
        """
        params = (int(sku['product_id']), int(sku['sku_id']), sku_name, image)
        pg.execute(query, params)
        logging.info(f"Inserted/Updated product: {sku['product_id']} sku: {sku['sku_id']}")


bulk_insert_product(3)

pg.commit()
pg.disconnect()