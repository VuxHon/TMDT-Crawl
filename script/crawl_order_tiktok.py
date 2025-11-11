import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.tiktok import Tiktok
from library.postgres import Postgres
from datetime import datetime
from datetime import timedelta
from library.helper import Helper
import logging
import time

logging.basicConfig(level=logging.INFO)

# Kết nối database
pg = Postgres()
pg.connect()

# Lấy dữ liệu từ API
time_delta = 0
end = datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=time_delta)
start = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=time_delta + 1)
tiktok = Tiktok()

response = tiktok.post_overview_stat(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
logging.info(f"API Response: {response}")

# Parse và lưu dữ liệu vào database
if response.get('code') == 0 and 'data' in response and 'chart' in response['data']:
    chart = response['data']['chart']
    categories = chart.get('categories', [])  # Danh sách dates
    series = chart.get('series', [])  # Danh sách các metrics
    
    # Tạo dictionary để map name -> data
    series_dict = {}
    for s in series:
        series_dict[s['name']] = s['data']
    
    # Xử lý từng date
    insert_count = 0
    update_count = 0
    
    for idx, date_str in enumerate(categories):
        try:
            # Parse date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Lấy giá trị cho từng metric
            cost = float(series_dict.get('cost', [0])[idx]) if idx < len(series_dict.get('cost', [])) else None
            onsite_roi2_shopping_sku = int(float(series_dict.get('onsite_roi2_shopping_sku', [0])[idx])) if idx < len(series_dict.get('onsite_roi2_shopping_sku', [])) else None
            cost_per_onsite_roi2_shopping_sku = float(series_dict.get('cost_per_onsite_roi2_shopping_sku', [0])[idx]) if idx < len(series_dict.get('cost_per_onsite_roi2_shopping_sku', [])) else None
            onsite_roi2_shopping_value = float(series_dict.get('onsite_roi2_shopping_value', [0])[idx]) if idx < len(series_dict.get('onsite_roi2_shopping_value', [])) else None
            onsite_roi2_shopping = float(series_dict.get('onsite_roi2_shopping', [0])[idx]) if idx < len(series_dict.get('onsite_roi2_shopping', [])) else None
            
            # Kiểm tra xem date đã tồn tại chưa
            check_query = "SELECT date FROM tiktok_ads_stat WHERE date = %s"
            existing = pg.fetch_one(check_query, (date_obj,))
            
            if existing:
                # Update nếu đã tồn tại
                update_query = """
                UPDATE tiktok_ads_stat 
                SET cost = %s,
                    onsite_roi2_shopping_sku = %s,
                    cost_per_onsite_roi2_shopping_sku = %s,
                    onsite_roi2_shopping_value = %s,
                    onsite_roi2_shopping = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
                """
                pg.execute(update_query, (
                    cost,
                    onsite_roi2_shopping_sku,
                    cost_per_onsite_roi2_shopping_sku,
                    onsite_roi2_shopping_value,
                    onsite_roi2_shopping,
                    date_obj
                ))
                update_count += 1
            else:
                # Insert nếu chưa tồn tại
                insert_query = """
                INSERT INTO tiktok_ads_stat 
                (date, cost, onsite_roi2_shopping_sku, cost_per_onsite_roi2_shopping_sku, 
                 onsite_roi2_shopping_value, onsite_roi2_shopping)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                pg.execute(insert_query, (
                    date_obj,
                    cost,
                    onsite_roi2_shopping_sku,
                    cost_per_onsite_roi2_shopping_sku,
                    onsite_roi2_shopping_value,
                    onsite_roi2_shopping
                ))
                insert_count += 1
                
        except Exception as e:
            logging.error(f"Error processing date {date_str}: {e}")
            continue
    
    pg.commit()
    logging.info(f"Data processing completed: {insert_count} inserted, {update_count} updated")
else:
    logging.error("Invalid response format or no chart data found")

pg.disconnect()
logging.info("Database connection closed")

logging.info(tiktok.get_income_export(str(Helper.to_unix_timestamp(start)), str(Helper.to_unix_timestamp(end))))
logging.info(tiktok.get_order_export(str(Helper.to_unix_timestamp(start)), str(Helper.to_unix_timestamp(end)), f"{format(start, '%Y%m%d')}_{format(end, '%Y%m%d')}"))
logging.info(tiktok.get_aff_orders(str(Helper.to_unix_timestamp_milliseconds(start)), str(Helper.to_unix_timestamp_milliseconds(end))))