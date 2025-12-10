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

def get_components_data(blocks, name):
    for block in blocks:
        if block['name'] == name:
            return block
    return None

def insert_product_sku(main_order_id):
    order_detail = tiktok.get_order_detail(main_order_id)
    sku_module = order_detail['data']['main_order'][0]['sku_module']
    for product in sku_module:
        product_id = int(product['product_id'])
        product_name = product['product_name']
        product_image_url = product['product_image']['url_list'][0] if product['product_image']['url_list'] else None
        insert_product_query = """
            INSERT INTO ecom_products (id, name, cover_image, shop_name)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                cover_image = EXCLUDED.cover_image,
                shop_name = EXCLUDED.shop_name
        """
        logging.info(f"Inserting product: {product_id} name: {product_name} cover_image: {product_image_url}")
        pg.execute(insert_product_query, (product_id, product_name, product_image_url, SOURCE))
        pg.commit()
        sku_id = int(product['sku_id'])
        sku_name = product['sku_name']
        sku_image_url = product_image_url
        insert_sku_query = """
            INSERT INTO ecom_sku_products (product_id, id, name, image)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (product_id, id) DO UPDATE SET
                name = EXCLUDED.name,
                image = EXCLUDED.image
        """
        logging.info(f"Inserting sku: {sku_id} name: {sku_name} image: {sku_image_url}")
        pg.execute(insert_sku_query, (product_id, sku_id, sku_name, sku_image_url))
        pg.commit()

def process_order_return(offset):
    order_return = tiktok.get_order_return_list(offset=offset)['data']['cards']
    date_return = None
    for order in order_return:
        # Extract date_return safely
        date_return = None
        try:
            header_right_block = get_components_data(order['card']['blocks'], 'header_right_block')
            if header_right_block and 'content' in header_right_block:
                header_right_time_block = get_components_data(header_right_block['content'], 'header_right_time')
                if header_right_time_block and 'starling_keys' in header_right_time_block:
                    header_right_time = header_right_time_block['starling_keys'][0]
                    date_return = datetime.fromtimestamp(int(header_right_time.split('.')[0]))
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logging.warning(f"Could not extract date_return: {e}")
        
        return_logistics_info = tiktok.get_return_logistics_info(order['biz_data']['reverse_main_order_id'])
        query = """
            INSERT INTO ecom_orders_return_refund (order_id, order_sn, return_sn, 
            tracking_numbers, refund_amount, 
            request_reason_text, status_text, 
            request_solution_text, reverse_logistics_info,
            date_return, platform, shop_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO UPDATE SET
                order_sn = EXCLUDED.order_sn,
                return_sn = EXCLUDED.return_sn,
                tracking_numbers = EXCLUDED.tracking_numbers,
                refund_amount = EXCLUDED.refund_amount,
                request_reason_text = EXCLUDED.request_reason_text,
                status_text = EXCLUDED.status_text,
                request_solution_text = EXCLUDED.request_solution_text,
                reverse_logistics_info = EXCLUDED.reverse_logistics_info,
                date_return = EXCLUDED.date_return,
                platform = EXCLUDED.platform,
                shop_name = EXCLUDED.shop_name
        """
        # Extract values safely
        main_order_id = order['biz_data']['main_order_id']
        return_sn = order['biz_data']['reverse_main_order_id']
        tracking_no = return_logistics_info.get('tracking_no') if return_logistics_info else None
        return_price_str = order['biz_data'].get('return_price', '0').replace('₫', '').replace('.', '')
        refund_amount = int(return_price_str) if return_price_str else 0
        
        reason_block = get_components_data(order['card']['blocks'], 'reason_block')
        request_reason = reason_block['title']['text']['content'] if reason_block else None
        
        status_block = get_components_data(order['card']['blocks'], 'status_block')
        status_text = None
        if status_block and 'title' in status_block and 'text' in status_block['title']:
            if 'dynamic_express' in status_block['title']['text']:
                status_text = status_block['title']['text']['dynamic_express']['items'][0]['message_content']
        
        reason_tags_list = get_components_data(order['card']['blocks'], 'reason_tags_list')
        request_solution = None
        if reason_tags_list and 'text' in reason_tags_list:
            if 'dynamic_express' in reason_tags_list['text']:
                request_solution = reason_tags_list['text']['dynamic_express']['items'][0]['message_content']
        
        reverse_logistics_status = return_logistics_info.get('status') if return_logistics_info else None
        
        params = (int(main_order_id), str(main_order_id), 
                  return_sn, tracking_no, 
                  refund_amount, request_reason, 
                  status_text, request_solution, 
                  reverse_logistics_status,
                  date_return, 'TiktokShop', SOURCE)
        logging.info(f"Inserting/Updating order return: {params}")
        pg.execute(query, params)
        
        # Extract products safely
        product_detail_card = get_components_data(order.get('linked_cards', []), 'product_detail_card')
        if product_detail_card and 'blocks' in product_detail_card:
            products = product_detail_card['blocks'][0]['content'][0]['skus']['data']
        else:
            products = []
        
        for product in products:
            sku_id = int(product['sku_id'])
            logging.info(f"Processing order return sku: {sku_id} return_amount: {product['quantity']}")
            
            # Check if sku_id exists in ecom_sku_products
            check_sku_query = """
                SELECT id FROM ecom_sku_products WHERE id = %s
            """
            existing_sku = pg.fetch_one(check_sku_query, (sku_id,))
            
            if not existing_sku:
                insert_product_sku(main_order_id)
                        
            # Insert/Update order return SKU
            query = """
                INSERT INTO ecom_orders_sku_return_refund (return_sn, sku_id, returned_amount, order_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, sku_id) DO UPDATE SET
                    returned_amount = EXCLUDED.returned_amount,
                    return_sn = EXCLUDED.return_sn
            """
            params = (return_sn, sku_id, product['quantity'], int(main_order_id))
            try:
                pg.execute(query, params)
                logging.info(f"Inserted/Updated order return sku: {sku_id} return_amount: {product['quantity']}")
            except Exception as e:
                logging.error(f"Error inserting/updating order return sku {sku_id}: {e}")
                raise

def process_order_failed_delivery(offset):
    order_failed_delivery = tiktok.get_order_failed_delivery(offset=offset)['data']['main_orders']
    date_return = None
    for order in order_failed_delivery:
        # Extract date_return safely
        reverse_module = order.get('reverse_module', [])
        date_return = None
        if not reverse_module:
            date_return = datetime.fromtimestamp(int(order['trade_order_module']['create_time']))
        else:
            date_return = datetime.fromtimestamp(int(reverse_module[0]['refund_time']))
        query = """
            INSERT INTO ecom_orders_return_refund (order_id, order_sn, return_sn, 
            tracking_numbers, refund_amount, 
            request_reason_text, status_text, 
            request_solution_text, reverse_logistics_info,
            date_return, platform, shop_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO UPDATE SET
                order_sn = EXCLUDED.order_sn,
                return_sn = EXCLUDED.return_sn,
                tracking_numbers = EXCLUDED.tracking_numbers,
                refund_amount = EXCLUDED.refund_amount,
                request_reason_text = EXCLUDED.request_reason_text,
                status_text = EXCLUDED.status_text,
                request_solution_text = EXCLUDED.request_solution_text,
                reverse_logistics_info = EXCLUDED.reverse_logistics_info,
                date_return = EXCLUDED.date_return,
                platform = EXCLUDED.platform,
                shop_name = EXCLUDED.shop_name
        """
        # Extract values safely
        main_order_id = order['main_order_id']
        return_sn = reverse_module[0]['reverse_order_id'] if reverse_module else order['trade_order_module']['main_order_id']
        tracking_no = order['delivery_module'][0]['last_tracking_no']
        refund_amount = int(order['price_module']['grand_total']['price_val'])
        
        request_reason = 'Giao hàng không thành công'
        
        abnormal_pkg_module = order.get('abnormal_pkg_module', [])
        if not abnormal_pkg_module:
            status_text = 'Giao hàng không thành công'
            request_solution = None
            reverse_logistics_status = None
        else:
            status_text = abnormal_pkg_module[0]['abnormal_pkg_tag']
            request_solution = abnormal_pkg_module[0]['abnormal_pkg_status_text']
            reverse_logistics_status = abnormal_pkg_module[0]['abnormal_pkg_status_text']
        
        params = (int(main_order_id), str(main_order_id), 
                  return_sn, tracking_no, 
                  refund_amount, request_reason, 
                  status_text, request_solution, 
                  reverse_logistics_status,
                  date_return, 'TiktokShop', SOURCE)
        logging.info(f"Inserting/Updating order failed delivery: {params}")
        pg.execute(query, params)
        
        # Extract products safely
        product_detail_card = order['sku_module']
        for product in product_detail_card:
            sku_id = int(product['sku_id'])
            logging.info(f"Processing order failed delivery sku: {sku_id} return_amount: {product['quantity']}")
            
            # Check if sku_id exists in ecom_sku_products
            check_sku_query = f"""
                SELECT id FROM ecom_sku_products WHERE id = {sku_id}
            """
            existing_sku = pg.fetch_one(check_sku_query)
            if not existing_sku:
                insert_product_sku(order['main_order_id'])            
            # Insert/Update order return SKU
            query = """
                INSERT INTO ecom_orders_sku_return_refund (return_sn, sku_id, returned_amount, order_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, sku_id) DO UPDATE SET
                    returned_amount = EXCLUDED.returned_amount,
                    return_sn = EXCLUDED.return_sn
            """
            params = (return_sn, sku_id, product['quantity'], int(main_order_id))
            try:
                pg.execute(query, params)
                logging.info(f"Inserted/Updated order return sku: {sku_id} return_amount: {product['quantity']}")
            except Exception as e:
                logging.error(f"Error inserting/updating order return sku {sku_id}: {e}")
                raise

page = 5
offset = 0
retry_count = 0
while page > 0:
    try:
        process_order_return(offset)
        pg.commit()
        logging.info(f"committed order return with offset: {offset}")
        retry_count = 0
        offset += 50
        page -= 1
    except:
        logging.info(f"retry order return with offset: {offset}")
        retry_count += 1
        if retry_count > 5:
            logging.error(f"retry order return with offset: {offset} failed after 5 retries")
            offset += 50
            page -= 1
        else:
            pass
    
page = 5
offset = 0
retry_count = 0
while page > 0:
    try:
        process_order_failed_delivery(offset)
        pg.commit()
        logging.info(f"committed order failed delivery with offset: {offset}")
        retry_count = 0
        offset += 50
        page -= 1
    except Exception as e:
        logging.info(f"retry order failed delivery with offset: {offset}")
        logging.info(f"error: {e}")
        retry_count += 1
        if retry_count > 5:
            logging.error(f"retry order failed delivery with offset: {offset} failed after 5 retries")
            offset += 50
            page -= 1
        else:
            pass

pg.disconnect()