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
        date_return = None
        return_attributes = order['header']['attribute_list'].get('return_attributes', [])
        if not order['reverse_logistics_info']['tracking_numbers'][0]:
            logging.info(f"No tracking numbers for order: {order['order_sn']} order_id: {order['order_id']}")
            continue
        for return_attribute in return_attributes:
            if return_attribute['key'] == 'return_by_date':
                date_return = datetime.fromtimestamp(int(return_attribute['value']))
                break
        if date_return is None:
            date_return = datetime.fromtimestamp(int(order['forward_logistics_info']['latest_logistics_status_update_time']))    
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
        logging.info(f"Inserting/Updating order return: {order['order_sn']} order_id: {order['order_id']} date_return: {date_return}")
        pg.execute(query, params)
        for product_item in order['product_items']:
            query = """
                INSERT INTO orders_sku_return_refund (return_sn, sku_id, returned_amount, order_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (order_id, sku_id) DO UPDATE SET
                    returned_amount = EXCLUDED.returned_amount,
                    return_sn = EXCLUDED.return_sn
            """
            params = (order['return_sn'], product_item['model']['id'], product_item['returned_amount'], order['order_id'])
            logging.info(f"Inserting/Updating order return sku: {product_item['model']['id']} return_amount: {product_item['returned_amount']}")
            pg.execute(query, params)

for page_number in range(1, 20):
    process_order_return(case_tab=0, page_number=page_number)
pg.commit()
pg.disconnect()