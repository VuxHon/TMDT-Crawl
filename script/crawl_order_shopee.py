import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.shopeev2 import Shopee
from datetime import datetime
from datetime import timedelta
from library.helper import Helper

# human date: YYYY-MM-DD
start_date = datetime.now() - timedelta(days=7)
start_date = start_date.strftime("%Y-%m-%d")
end_date = datetime.now().strftime("%Y-%m-%d")
print(start_date, end_date)

shopee = Shopee("DUNI_SHOPEE")
print(shopee.get_order_report(start_date, end_date))