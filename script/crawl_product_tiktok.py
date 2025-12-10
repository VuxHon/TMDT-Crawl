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
        try:
            logging.info(f"Processing page {page}")
            response = tiktok.get_products(page=page)
            
            # Check if response is valid
            if not response:
                logging.warning(f"Empty response for page {page}")
                continue
            
            products = response.get('products', [])
            
            if not products:
                logging.info(f"No products found on page {page}")
                continue
            
            for product in products:
                try:
                    # Safely extract image
                    image = None
                    if product.get('images') and len(product['images']) > 0:
                        if product['images'][0].get('url_list') and len(product['images'][0]['url_list']) > 0:
                            image = product['images'][0]['url_list'][0]
                    
                    if not image:
                        logging.warning(f"No image found for product {product.get('product_id')}, using empty string")
                        image = ''
                    
                    product_id = int(product.get('product_id', 0))
                    product_title = product.get('product_title', '')
                    
                    # Validate product_id before inserting
                    if not product_id:
                        logging.warning(f"Invalid product_id: {product_id}, skipping product")
                        continue
                    
                    logging.info(f"Inserting/Updating product: id: {product_id} name: {product_title} cover_image: {image[:50] if image else 'N/A'}...")
                    query = """
                        INSERT INTO ecom_products (id, name, cover_image, shop_name)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            cover_image = EXCLUDED.cover_image,
                            shop_name = EXCLUDED.shop_name
                    """
                    params = (product_id, product_title, image, SOURCE)
                    pg.execute(query, params)
                    logging.info(f"Successfully inserted/updated product: {product_id}")
                    
                    # Insert SKUs
                    skus = product.get('skus', [])
                    if skus:
                        bulk_insert_sku(skus, product_id)
                    else:
                        logging.warning(f"No SKUs found for product {product_id}")
                        
                except Exception as e:
                    logging.error(f"Error processing product {product.get('product_id', 'unknown')}: {e}")
                    continue  # Continue with next product
            
            # Commit after each page to ensure data is saved
            pg.commit()
            logging.info(f"Committed page {page}")
            
        except Exception as e:
            logging.error(f"Error processing page {page}: {e}")
            pg.rollback()  # Rollback on error
            continue  # Continue with next page

def bulk_insert_sku(skus, product_id=None):
    for sku in skus:
        try:
            # Safely extract SKU name
            sku_name = ''
            if sku.get('properties'):
                sku_name = ', '.join([s.get('value_name', '') for s in sku['properties'] if s.get('value_name')])
            
            # Safely extract image
            image = None
            if sku.get('images') and len(sku['images']) > 0:
                if sku['images'][0].get('url_list') and len(sku['images'][0]['url_list']) > 0:
                    image = sku['images'][0]['url_list'][0]
            
            if not image:
                logging.warning(f"No image found for SKU {sku.get('sku_id')}, using empty string")
                image = ''
            
            sku_product_id = int(sku.get('product_id', product_id or 0))
            sku_id = int(sku.get('sku_id', 0))
            
            # Validate IDs before inserting
            if not sku_product_id or not sku_id:
                logging.warning(f"Invalid SKU data: product_id={sku_product_id}, sku_id={sku_id}, skipping")
                continue
            
            query = """
                INSERT INTO ecom_sku_products (product_id, id, name, image)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (product_id, id) DO UPDATE SET
                    name = EXCLUDED.name,
                    image = EXCLUDED.image
            """
            params = (sku_product_id, sku_id, sku_name, image)
            pg.execute(query, params)
            logging.info(f"Inserted/Updated product: {sku_product_id} sku: {sku_id}")
            
        except Exception as e:
            logging.error(f"Error inserting/updating SKU {sku.get('sku_id', 'unknown')}: {e}")
            continue  # Continue with next SKU


bulk_insert_product(10)

pg.disconnect()
logging.info("All pages processed")