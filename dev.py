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
failed_delivery = tiktok.get_order_failed_delivery(offset=0)['data']['main_orders'][0]
logging.info(f"Failed delivery: {json.dumps(failed_delivery, indent=4)}")