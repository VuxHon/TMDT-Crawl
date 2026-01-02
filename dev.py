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
import re

db = Postgres()
TYPE = ['OVS', 'HD', 'HDZ', 'BBT', 'SWT', 'PL', 'SHZ', 'POLO', 'BX', 'BOXY']
COLOR = ['Trăng', 'Trắg', 'Trg', 'Đen', 'Xanh', 'Be', 'Xám', 'Trắng', 'Nâu', 'Hồng', 'Đỏ']
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

def clean_variation_sku(sku_name):
    
    # bỏ TYPE (không phân biệt hoa thường):
    for type in TYPE:
        sku_name = re.sub(re.escape(type), '', sku_name, flags=re.IGNORECASE)
    # bỏ COLOR (không phân biệt hoa thường):
    for color in COLOR:
        sku_name = re.sub(re.escape(color), '', sku_name, flags=re.IGNORECASE)
    # bỏ sau dấu phẩy
    sku_name = sku_name.split(',')[0]
    
    # bỏ dấu '-'
    sku_name = sku_name.replace('-', '')
    
    # remove duplicate spaces
    sku_name = ' '.join(sku_name.split())
    
    # remove leading and trailing spaces
    sku_name = sku_name.strip()
    
    return sku_name

def label_variation_sku():
    query = """
        select distinct name from ecom_sku_products
        where name is not null
    """
    result = db.fetch_all(query)
    sku_names = []
    for row in result:
        sku_names.append(row['name'])
    for sku_name in sku_names:
        clean_variation_sku_name = clean_variation_sku(sku_name)
        query = """
            update ecom_sku_products
            set label_variation = %s
            where name = %s
        """
        params = (clean_variation_sku_name, sku_name)
        db.execute(query, params)
        db.commit()
        logging.info(f"Updated {sku_name} to {clean_variation_sku_name}")
def test_clean_variation_sku():
    query = """
        select distinct name from ecom_sku_products
        where name is not null
    """
    result = db.fetch_all(query)
    sku_name = []
    for row in result:
        sku_name.append(row['name'])
    for sku_name in sku_name:
        clean_variation_sku_name = clean_variation_sku(sku_name)
        # ví dụ
        with open("output.txt", "a", encoding="utf-8", newline="\n") as f:
            f.write(clean_variation_sku_name + "\n")
        logging.info(f"Updated {sku_name} to {clean_variation_sku_name}")

def re_label_variation_sku():
    query = """
        select distinct label_variation from ecom_sku_products
        where label_variation is not null
    """
    result = db.fetch_all(query)
    label_variations = []
    for row in result:
        label_variations.append(row['label_variation'])
    for label_variation in label_variations:
        label_variation_name = label_variation.split(' ')
        if len(label_variation_name) > 1:
            sku_update = label_variation.replace(' ', '')
            query = """
                update ecom_sku_products
                set label_variation = %s
                where label_variation = %s
            """
            params = (label_variation, sku_update)
            db.execute(query, params)
            db.commit()
            logging.info(f"Updated {sku_update} to {label_variation}")

def get_label_variation():
    query = """
        select distinct label_variation from ecom_sku_products
        where label_variation is not null
    """
    result = db.fetch_all(query)
    label_variations = []
    for row in result:
        print(row['label_variation'])

def get_sku_have_two_color():
    query = """
        select distinct name, label_variation from ecom_sku_products
        where name is not null
    """
    result = db.fetch_all(query)
    sku_names = []
    label_variations = []
    for row in result:
        sku_names.append(row['name'])
        label_variations.append(row['label_variation'])
    for sku_name, label_variation in zip(sku_names, label_variations):
        color_count = 0
        for color in COLOR:
            if color.lower() in sku_name.lower():
                color_count += 1
        if color_count >= 2:
            is_has_color = False
            for color in COLOR:
                if color.lower() in label_variation.lower():
                    is_has_color = True
            if not is_has_color:
                print(f"{sku_name}: clean_variation_sku_name = {clean_variation_sku(sku_name)}")
                with open("output.txt", "a", encoding="utf-8", newline="\n") as f:
                    f.write(f"{sku_name}: clean_variation_sku_name = {clean_variation_sku(sku_name)}\n")

get_sku_have_two_color()