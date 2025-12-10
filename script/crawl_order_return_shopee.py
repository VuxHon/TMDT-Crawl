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
def process_order_return(case_tab, page_number):
    order_return = shopee.get_order_return(page_number=page_number, page_size=40, case_tab=case_tab)['data']['exceptional_case_list']
    for order in order_return:
        return_attributes = order['header']['attribute_list'].get('return_attributes', [])
        if not order['reverse_logistics_info']['tracking_numbers'][0] or order['return_id'] is None:
            logging.info(f"No tracking numbers for order: {order['order_sn']} order_id: {order['order_id']} entity_type: {order['entity_type']}")
            continue
        logging.info(f"Getting order return detail for order: {order['order_sn']} order_id: {order['order_id']} return_id: {order['return_id']}")
                
        date_return = None
        if case_tab == 1:
            try:
                return_detail_response = shopee.get_order_return_detail(order['return_id'])
                if not return_detail_response or 'data' not in return_detail_response:
                    logging.warning(f"Invalid response for return detail: {order['return_id']}")
                    continue
                
                return_header = return_detail_response['data'].get('return_header', {})
                if not return_header or 'attribute_list' not in return_header:
                    logging.warning(f"Missing return_header or attribute_list for return_id: {order['return_id']}")
                    continue
                
                attribute_list = return_header['attribute_list'].get('return_attributes', [])
                logging.info(f"attribute_list: {attribute_list}")
                for attribute in attribute_list:
                    if attribute['key'] == 'offer_due_date':
                        logging.info(f"attribute: {attribute}")
                        date_return = datetime.fromtimestamp(int(attribute['value']))  
                        break
            except (KeyError, TypeError) as e:
                logging.error(f"Error getting order return detail for return_id {order['return_id']}: {e}")
                continue
        
        if date_return is None:
            date_return = datetime.fromtimestamp(order['forward_logistics_info']['latest_logistics_status_update_time'])
            logging.info(f"date_return: {date_return}")
        query = """
            INSERT INTO ecom_orders_return_refund (order_id, order_sn, return_sn, 
            tracking_numbers, refund_amount, 
            request_reason_text, status_text, 
            request_solution_text, reverse_logistics_info, 
            forward_logistics_info, date_return, platform, shop_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO UPDATE SET
                order_sn = EXCLUDED.order_sn,
                return_sn = EXCLUDED.return_sn,
                tracking_numbers = EXCLUDED.tracking_numbers,
                refund_amount = EXCLUDED.refund_amount,
                request_reason_text = EXCLUDED.request_reason_text,
                status_text = EXCLUDED.status_text,
                request_solution_text = EXCLUDED.request_solution_text,
                reverse_logistics_info = EXCLUDED.reverse_logistics_info,
                forward_logistics_info = EXCLUDED.forward_logistics_info,
                date_return = EXCLUDED.date_return,
                platform = EXCLUDED.platform,
                shop_name = EXCLUDED.shop_name
        """
        params = (order['order_id'],order['order_sn'], 
                  order['return_sn'], order['reverse_logistics_info']['tracking_numbers'][0], 
                  int(order['display_refund_amount'].replace('.00', '')), order['request_reason_text'], 
                  order['header']['status_text'], order['request_solution_text'], 
                  order['reverse_logistics_info']['aggregated_logistics_status_text'], order['forward_logistics_info']['aggregated_logistics_status_text'], 
                  date_return, 'Shopee', SOURCE)
        logging.info(f"Inserting/Updating order return: {order['order_sn']} tracking_numbers: {order['reverse_logistics_info']['tracking_numbers'][0]} date_return: {date_return}")
        try:
            pg.execute(query, params)
            logging.info(f"Successfully inserted/updated order return: {order['order_sn']}")
        except Exception as e:
            logging.error(f"Error inserting/updating order return {order['order_sn']}: {e}")
            pg.rollback()  # Rollback to reset transaction state
            continue  # Skip this order and continue with next
        
        for product_item in order['product_items']:
            # ON CONFLICT will update all specified columns with new values from EXCLUDED
            query = """
                INSERT INTO ecom_orders_sku_return_refund (return_sn, sku_id, returned_amount, order_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, sku_id) DO UPDATE SET
                    returned_amount = EXCLUDED.returned_amount,
                    return_sn = EXCLUDED.return_sn
            """
            params = (order['return_sn'], product_item['model']['id'], product_item['returned_amount'], order['order_id'])
            logging.info(f"Inserting/Updating order return sku: {product_item['model']['id']} return_amount: {product_item['returned_amount']}")
            try:
                pg.execute(query, params)
                logging.info(f"Successfully inserted/updated order return sku: {product_item['model']['id']}")
            except Exception as e:
                logging.error(f"Error inserting/updating order return sku {product_item['model']['id']}: {e}")
                pg.rollback()  # Rollback to reset transaction state
                continue  # Continue with next SKU

def delete_order_canceled(page_number):
    order_return = shopee.get_order_return(page_number=page_number, page_size=40, case_tab=0)['data']['exceptional_case_list']
    order_sn = [order['order_sn'] for order in order_return if order['header']['status_text'] == 'Yêu cầu bị huỷ'] # Tối ưu hóa việc lấy order_sn
    if len(order_sn) == 0:
        logging.info(f"No order canceled found for page: {page_number}")
        return
    # Tạo chuỗi placeholder: (%s, %s, %s, ...)
    placeholders = ', '.join(['%s'] * len(order_sn)) 
    
    query = f"""
        DELETE FROM ecom_orders_return_refund WHERE order_sn IN ({placeholders})
    """
    
    logging.info(f"Deleting order canceled: {order_sn}")
    
    # Truyền danh sách order_sn vào hàm execute như một tham số tuple
    pg.execute(query, tuple(order_sn)) # Hoặc pg.execute(query, order_sn) tùy vào thư viện

for page_number in range(1, 20):
    try:
        logging.info(f"Processing page {page_number}, case_tab=1")
        process_order_return(case_tab=1, page_number=page_number)
        pg.commit()  # Commit after each page to ensure data is saved
        logging.info(f"Committed page {page_number}, case_tab=1")
    except Exception as e:
        logging.error(f"Error processing page {page_number}, case_tab=1: {e}")
        pg.rollback()  # Rollback on error
    
    try:
        logging.info(f"Processing page {page_number}, case_tab=3")
        process_order_return(case_tab=3, page_number=page_number)
        pg.commit()  # Commit after each page to ensure data is saved
        logging.info(f"Committed page {page_number}, case_tab=3")
    except Exception as e:
        logging.error(f"Error processing page {page_number}, case_tab=3: {e}")
        pg.rollback()  # Rollback on error
    
    # delete_order_canceled(page_number=page_number)

pg.disconnect()
logging.info("All pages processed and committed")