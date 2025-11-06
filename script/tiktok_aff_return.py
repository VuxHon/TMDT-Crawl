import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import requests

from library.tiktok import Tiktok
from datetime import datetime
from datetime import timedelta
from library.helper import Helper
import logging
logging.basicConfig(level=logging.INFO)
end = datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=0)
start = end.replace(hour=0, minute=0, second=0) - timedelta(days=30)
page = 1
tiktok = Tiktok()
order_aff_success = tiktok.get_order_aff_success(str(Helper.to_unix_timestamp_milliseconds(start)), str(Helper.to_unix_timestamp_milliseconds(end)), page)
order_aff_success_list = []
logging.info(order_aff_success)
if order_aff_success['total_count'] is not None and order_aff_success['total_count'] > 0:
    while (page-1)*100 < order_aff_success['total_count']:
        for order in order_aff_success['orders']:
            order_aff_success_list.append(order['main_order_id'])
        logging.info(f"success in page: {page}")
        logging.info(f"total count: {order_aff_success['total_count']}")
        page += 1
        if page*100 >= order_aff_success['total_count']:
            order_aff_success = tiktok.get_order_aff_success(str(Helper.to_unix_timestamp_milliseconds(start)), str(Helper.to_unix_timestamp_milliseconds(end)), page)
        else:
            break
else:
    logging.info("No order found")

order_aff_success_list_fuzzy = []

for order_id in order_aff_success_list:
    resp = tiktok.get_search_fuzzy(order_id).json()
    if resp.get('data', {}).get('fuzzy_details', []):
        order_aff_success_list_fuzzy.append(resp.get('data', {}).get('fuzzy_details', [])[0].get('fuzzy_field_value'))
        
output = []

for order_id in order_aff_success_list_fuzzy:
    statement_info = tiktok.get_statement_info(order_id)
    if statement_info['data']['total_record'] > 0:
        for order_record in statement_info['data']['order_records']:
            if int(order_record['settlement_amount']['amount']) >= 0:
                statement_detail_id = order_record['statement_detail_id']
                statement_transaction_detail = tiktok.get_statement_transaction_detail(statement_detail_id)
                fee_list = statement_transaction_detail['data']['order_record']['out_come']['fee_list']
                for fee_item in fee_list:
                    if fee_item['type'] == 'affiliate_ads_commission' or fee_item['type'] == 'affiliate_commission_before_pit':
                        output.append({
                            'order_id': order_id,
                            'fee_amount': int(fee_item['amount']['amount'])
                        })
                        break
                if len(output) > 0:
                    break
    else:
        logging.info("No statement found")  
        
with open(f'output_{str(Helper.to_unix_timestamp(start))}_{str(Helper.to_unix_timestamp(end))}.json', 'w') as f:
    json.dump(output, f)
    
#write json as excel
import pandas as pd
df = pd.DataFrame(output)
df.to_excel(f'tiktok_aff_return/output_{str(Helper.to_unix_timestamp(start))}_{str(Helper.to_unix_timestamp(end))}.xlsx', index=False)