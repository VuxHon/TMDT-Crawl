import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.tiktok import Tiktok
from datetime import datetime
from datetime import timedelta
from library.helper import Helper
import logging
import time
logging.basicConfig(level=logging.INFO)
time_delta = 175
end = datetime.now().replace(hour=23, minute=59, second=59) - timedelta(days=time_delta)
start = datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=time_delta + 25)
tiktok = Tiktok()
logging.info(tiktok.get_income_export(str(Helper.to_unix_timestamp(start)), str(Helper.to_unix_timestamp(end))))
logging.info(tiktok.get_order_export(str(Helper.to_unix_timestamp(start)), str(Helper.to_unix_timestamp(end)), f"{format(start, '%Y%m%d')}_{format(end, '%Y%m%d')}"))
# logging.info(tiktok.get_aff_orders(str(Helper.to_unix_timestamp_milliseconds(start)), str(Helper.to_unix_timestamp_milliseconds(end))))