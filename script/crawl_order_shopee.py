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

shopee = Shopee("DUNI_SHOPEE")
pg = Postgres()
pg.connect()

# human date: YYYY-MM-DD
start_date = datetime.now() - timedelta(days=30)
start_date = start_date.strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")
logging.info(shopee.get_order_report(start_date, end_date))

pg = Postgres()
pg.connect()

date_now = datetime.now()
start_date = date_now - timedelta(days=7)

# Loop through each day
while start_date < date_now:
    start_time = Helper.to_unix_timestamp(start_date)
    end_date = start_date + timedelta(days=1)
    end_time = Helper.to_unix_timestamp(end_date) - 1
    
    shopee_ads_stat = shopee.get_ads_stat(start_time, end_time)
    
    # Check if data exists and has report_by_time
    if shopee_ads_stat.get('code') == 0 and 'data' in shopee_ads_stat and 'report_by_time' in shopee_ads_stat['data']:
        report_by_time = shopee_ads_stat['data']['report_by_time']
        
        # Loop through each time period in report_by_time
        for time_period in report_by_time:
            key = int(time_period['key'])  # Convert key to BIGINT
            metrics = time_period.get('metrics', {})
            
            # Prepare INSERT ... ON CONFLICT DO UPDATE query
            query = """
                INSERT INTO shopee_ads_stat (
                    "key", broad_cir, broad_gmv, broad_order, broad_order_amount, broad_roi,
                    checkout, checkout_rate, click, cost, cpc, cpdc, cr, ctr,
                    direct_cr, direct_cir, direct_gmv, direct_order, direct_order_amount, direct_roi,
                    impression, avg_rank, product_click, product_impression, product_ctr,
                    location_in_ads, reach, page_views, unique_visitors, view, cpm, unique_click_user
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT ("key") DO UPDATE SET
                    broad_cir = EXCLUDED.broad_cir,
                    broad_gmv = EXCLUDED.broad_gmv,
                    broad_order = EXCLUDED.broad_order,
                    broad_order_amount = EXCLUDED.broad_order_amount,
                    broad_roi = EXCLUDED.broad_roi,
                    checkout = EXCLUDED.checkout,
                    checkout_rate = EXCLUDED.checkout_rate,
                    click = EXCLUDED.click,
                    cost = EXCLUDED.cost,
                    cpc = EXCLUDED.cpc,
                    cpdc = EXCLUDED.cpdc,
                    cr = EXCLUDED.cr,
                    ctr = EXCLUDED.ctr,
                    direct_cr = EXCLUDED.direct_cr,
                    direct_cir = EXCLUDED.direct_cir,
                    direct_gmv = EXCLUDED.direct_gmv,
                    direct_order = EXCLUDED.direct_order,
                    direct_order_amount = EXCLUDED.direct_order_amount,
                    direct_roi = EXCLUDED.direct_roi,
                    impression = EXCLUDED.impression,
                    avg_rank = EXCLUDED.avg_rank,
                    product_click = EXCLUDED.product_click,
                    product_impression = EXCLUDED.product_impression,
                    product_ctr = EXCLUDED.product_ctr,
                    location_in_ads = EXCLUDED.location_in_ads,
                    reach = EXCLUDED.reach,
                    page_views = EXCLUDED.page_views,
                    unique_visitors = EXCLUDED.unique_visitors,
                    view = EXCLUDED.view,
                    cpm = EXCLUDED.cpm,
                    unique_click_user = EXCLUDED.unique_click_user
            """
            
            # Extract all metrics with None as default for missing values
            params = (
                key,
                metrics.get('broad_cir'),
                metrics.get('broad_gmv'),
                metrics.get('broad_order'),
                metrics.get('broad_order_amount'),
                metrics.get('broad_roi'),
                metrics.get('checkout'),
                metrics.get('checkout_rate'),
                metrics.get('click'),
                metrics.get('cost'),
                metrics.get('cpc'),
                metrics.get('cpdc'),
                metrics.get('cr'),
                metrics.get('ctr'),
                metrics.get('direct_cr'),
                metrics.get('direct_cir'),
                metrics.get('direct_gmv'),
                metrics.get('direct_order'),
                metrics.get('direct_order_amount'),
                metrics.get('direct_roi'),
                metrics.get('impression'),
                metrics.get('avg_rank'),
                metrics.get('product_click'),
                metrics.get('product_impression'),
                metrics.get('product_ctr'),
                metrics.get('location_in_ads'),
                metrics.get('reach'),
                metrics.get('page_views'),
                metrics.get('unique_visitors'),
                metrics.get('view'),
                metrics.get('cpm'),
                metrics.get('unique_click_user')
            )
            
            pg.execute(query, params)
            logging.info(f"Inserted/Updated key: {key} for date: {start_date.strftime('%Y-%m-%d')}")
        
        pg.commit()
        logging.info(f"Processed {len(report_by_time)} records for date: {start_date.strftime('%Y-%m-%d')}")
    else:
        logging.warning(f"No data found for date: {start_date.strftime('%Y-%m-%d')}")
    
    # Move to next day
    start_date = end_date

pg.disconnect()