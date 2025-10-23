import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library.tiktok import Tiktok
from datetime import datetime
from datetime import timedelta
from library.helper import Helper

end = datetime.now()
start = end.replace(hour=0, minute=0, second=0) - timedelta(days=7)
tiktok = Tiktok()
print(tiktok.get_income_export(str(Helper.to_unix_timestamp(start)), str(Helper.to_unix_timestamp(end))))