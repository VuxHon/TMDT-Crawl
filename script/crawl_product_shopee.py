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

last_cursor = None
SOURCE = "DUNI_SHOPEE"
shopee = Shopee(SOURCE)
pg = Postgres()
pg.connect()
while last_cursor != '':
    try:
        response = shopee.get_products(last_cursor=last_cursor)
        products = response['data']['products']
        last_cursor = response['data']['page_info']['cursor']
        for product in products:
            logging.info(f"Inserting/Updating product: id: {product['id']} name: {product['name']} cover_image: {product.get('cover_image', 'N/A')}")
            query = """
                INSERT INTO ecom_products (id, name, cover_image, shop_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    cover_image = EXCLUDED.cover_image,
                    shop_name = EXCLUDED.shop_name
            """
            # Build cover image URL
            cover_image = product.get('cover_image', '')
            if cover_image.startswith('http'):
                cover_image_url = cover_image
            else:
                cover_image_url = f"https://cf.shopee.vn/file/{cover_image}"
            
            params = (product['id'], product['name'], cover_image_url, SOURCE)
            try:
                pg.execute(query, params)
                logging.info(f"Successfully inserted/updated product: {product['id']}")
            except Exception as e:
                logging.error(f"Error inserting/updating product {product['id']}: {e}")
                continue  # Continue with next product
            
            for sku in product.get('model_list', []):
                # Use ON CONFLICT for upsert
                # Build image URL - check if it already has full URL or just path
                sku_image = sku.get('image', '')
                if sku_image.startswith('http'):
                    image_url = sku_image
                else:
                    image_url = f"https://cf.shopee.vn/file/{sku_image}"
                
                insert_sku_query = """
                    INSERT INTO ecom_sku_products (product_id, id, name, image)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (product_id, id) DO UPDATE SET
                        name = EXCLUDED.name,
                        image = EXCLUDED.image
                """
                try:
                    pg.execute(insert_sku_query, (product['id'], sku['id'], sku.get('name', ''), image_url))
                    logging.info(f"Inserted/Updated product: {product['id']} sku: {sku['id']} image: {image_url}")
                except Exception as e:
                    logging.error(f"Error inserting/updating SKU {sku['id']} for product {product['id']}: {e}")
                    continue  # Continue with next SKU
            pg.commit()
    
    except Exception as e:
        logging.error(f"Error processing page {last_cursor}: {e}")
        continue  # Continue with next page
pg.disconnect()
logging.info("All pages processed")