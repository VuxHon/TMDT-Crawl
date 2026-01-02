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
from library.sapo import Sapo
import json

db = Postgres()
def clean_sku_name(sku_name):
    # bỏ dấu các từ trong cụm dấu ngoặc
    sku_name = sku_name.replace('(', '').replace(')', '')
    return sku_name

def get_shop_sku_none_id():
    query = """
        select distinct ten_phan_loai_hang from orders_shopee_product
        where ten_phan_loai_hang is not null and sku_ecom_id is null
    """
    result = db.fetch_all(query)
    shop_sku_none_id = []
    for row in result:
        shop_sku_none_id.append(row['ten_phan_loai_hang'])
    return shop_sku_none_id

def get_id_sku_name():
    query = """
        select id, name from ecom_sku_products
        where name is not null
    """
    result = db.fetch_all(query)
    sku_name = {}
    for row in result:
        sku_name[row['name']] = row['id']
        
    return sku_name

def update_sku_ecom_id():
    shop_sku_none_id = get_shop_sku_none_id()
    id_sku_name = get_id_sku_name()
    for shop_sku_none_id in shop_sku_none_id:
        if shop_sku_none_id in id_sku_name or shop_sku_none_id.replace('- Basic', '') in id_sku_name:
            if shop_sku_none_id in id_sku_name:
                sku_ecom_id = id_sku_name[shop_sku_none_id]
            else:
                sku_ecom_id = id_sku_name[shop_sku_none_id.replace('- Basic', '')]
            query = """
                update orders_shopee_product
                set sku_ecom_id = %s
                where ten_phan_loai_hang = %s and sku_ecom_id is null
            """
            params = (sku_ecom_id, shop_sku_none_id)
            db.execute(query, params)
            db.commit()
            logging.info(f"Updated {shop_sku_none_id} to {sku_ecom_id}")
            
def update_sku_ecom_id_sapo(platform="Shopee"):
    if platform == "Shopee":
        connection_id = "108710"
    elif platform == "Tiktok":
        connection_id = "117719"
    else:
        raise ValueError(f"Platform {platform} không tồn tại")
    sapo = Sapo()
    sku_processed = []
    for page in range(1, 2):
        orders_list = sapo.get_orders_list(page, connection_id)
        for order in orders_list['orders']:
            for product in order['products']:
                sku_name = product['variation_name']
                sku_ecom_id = int(product['variation_id'])
                if sku_name not in sku_processed:
                    sku_processed.append(sku_name)
                    query = """
                        update orders_shopee_product
                        set sku_ecom_id = %s
                        where ten_phan_loai_hang = %s
                    """
                    params = (sku_ecom_id, sku_name)
                    db.execute(query, params)
                    db.commit()
                    logging.info(f"Updated {sku_name} to {sku_ecom_id}")
update_sku_ecom_id_sapo(platform="Shopee")