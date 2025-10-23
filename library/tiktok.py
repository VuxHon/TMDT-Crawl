import requests
import library.config as cf
from library.lark import Lark
from library.helper import Helper
import logging
from typing import Tuple, Dict, Any, Optional
import time
from random import randrange
import logging
import os
def create_curl_request(url, payload, headers):
    curl_request = f"curl -X POST '{url}' -H '{headers}' -d '{payload}'"
    return curl_request
class Tiktok:
    def __init__(self):
        self.lark_helper = Lark()
        self.headers = None
        self.params = None
        self._init_headers()
    def _init_headers(self):
        curl_data = self.lark_helper.get_lark_base_record(cf.PEEKIE_BASE_ID, cf.PEEKIE_TABLE_ID, cf.PEEKIE_RECORD_ID["DUNI_TIKTOK"], "body")
        object_curl_data = Helper.decode_curl_data_from_lark(curl_data)
        self.headers = object_curl_data['headers']
        url = object_curl_data['url']
        self.params = Helper.get_url_params(url)
    def get_order_info_by_tracking_number(self, tracking_number):
        tracking = []
        tracking.append(tracking_number)
        url = f"https://seller-vn.tiktok.com/api/fulfillment/order/list"
        params = {
            "aid": "4068",
        }
        payload = {
            "sort_info": "6",
            "search_condition": {
                "condition_list": {
                    "global_search_id": {"value": tracking}
                }
            },
            "count": 20,
            "pagination_type": 0,
            "offset": 0,
            "search_cursor": "",
            "extra_data_list": [
                "48_hours_dispatch_tag",
                "split_combine_tag_v1",
                "free_sample_tag_v1",
                "hazmat_order_tag",
                "made_to_order_tag",
                "pre_order_tag",
                "pre_sell_tag",
                "zero_lottery_tag",
                "gift_insurance_tag",
                "internal_purchase_tag",
                "replacement_order_tag_v1",
                "risk_order_tag_v1",
                "combo_sku_tag",
                "refundable_sample_tag",
                "split_package_type_tag",
                "two_day_delivery"
            ]
        }
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        return response
    def get_order_uncompleted(self):
        url = "https://seller-vn.tiktok.com/api/fulfillment/order/list"
        params = {
            "aid": "4068",
        }
        payload = {
            "sort_info": "1",
            "search_condition": {
                "condition_list": {
                "order_status": {
                    "value": [
                    "2"
                    ]
                },
                "search_tab": {
                    "value": [
                    "101"
                    ]
                }
                }
            },
            "count": 50,
            "pagination_type": 0,
            "offset": 0,
            "search_cursor": "",
            "extra_data_list": [
                "48_hours_dispatch_tag",
                "split_combine_tag_v1",
                "free_sample_tag_v1",
                "hazmat_order_tag",
                "made_to_order_tag",
                "pre_order_tag",
                "pre_sell_tag",
                "zero_lottery_tag",
                "gift_insurance_tag",
                "internal_purchase_tag",
                "replacement_order_tag_v1",
                "risk_order_tag_v1",
                "combo_sku_tag",
                "refundable_sample_tag",
                "split_package_type_tag",
                "two_day_delivery",
                "DT_order"
            ]
        }
        response = requests.post(url, headers=self.headers, params=params, json=payload)
        return response
    def get_buyer_contact_info(self, order_id: str):
        url = "https://seller-vn.tiktok.com/api/fulfillment/orders/buyer_contact_info/get"
        payload = {
            "main_order_id": order_id,
            "contact_info_type": 2
        }
        response = requests.post(url, headers=self.headers, params=self.params, json=payload)
        return response
    
    def get_file_key(self, export_task_id):
        url = "https://seller-vn.tiktok.com/api/fulfillment/order/export_record/get?aid=4068"
        response = requests.post(url, headers=self.headers, json={})
        export_records = response.json()['data']['export_records']
        for export_record in export_records:
            if export_record['export_task_id'] == export_task_id:
                if export_record['file_key'] != "":
                    return export_record['file_key']
                else:
                    logging.info("File key is empty, waiting for 2 seconds")
                    time.sleep(2)
                    return self.get_file_key(export_task_id)
                break
        return None
    
    def get_url_download(self, export_task_id, file_key):
        url = "https://seller-vn.tiktok.com/api/fulfillment/order/download?aid=4068"
        payload = {
            "export_task_id" : export_task_id,
            "file_key": file_key
        }    
        respone = requests.post(url, headers=self.headers, json=payload)
        return respone.json()['data']['download_url']
    
    def dowload_content(self, download_url):
        respone = requests.get(url=download_url, headers=self.headers)
        return respone
    
    def get_order_export(self, time_start, time_end, file_name):
        url = "https://seller-vn.tiktok.com/api/fulfillment/order/export?aid=4068"
        payload = {
            "search_condition": {
                "condition_list": {
                    "time_order_created": {
                        "value": [
                            time_start,
                            time_end
                        ]
                    }
                }
            },
            "sort_info": "6",
            "file_name": f"{file_name}.csv",
            "file_type": 2
        }
        get_order_export_response = requests.post(url, headers=self.headers, json=payload)
        export_task_id = get_order_export_response.json()['data']['export_task_id']
        file_key = self.get_file_key(export_task_id)
        download_url = self.get_url_download(export_task_id,file_key)
        content = self.dowload_content(download_url)
        with open(f"orders_tiktok/{file_name}.csv", "wb") as f:
            f.write(content.content)
        return f"orders_tiktok/{file_name}.csv"
    
    def get_export_history_aff_orders(self):
        url = "https://affiliate.tiktok.com/api/v1/affiliate/export_history?user_language=vi-VN&shop_region=VN"
        response = requests.get(url, headers=self.headers).json()
        task = response['tasks'][0]
        if task['is_finished'] == False:
            logging.info(f"Task is not finished, waiting for 2 seconds, task_id: {task['task_id']}")
            time.sleep(2)
            return self.get_export_history_aff_orders()
        else:
            return task['task_id']
    
    def export_link_aff_orders(self, task_id):
        url = f"https://affiliate.tiktok.com/api/v1/affiliate/export_link?user_language=vi-VN&shop_region=VN&task_id={task_id}"
        response = requests.get(url, headers=self.headers).json()
        return response['links'][0]
    
    def get_aff_orders(self, time_start, time_end):
        url ="https://affiliate.tiktok.com/api/v1/affiliate/export_order_v2?user_language=vi-VN&shop_region=VN"
        payload = {
            "conditions": {
                "time_period": {
                    "beginning_time": time_start,
                    "ending_time": time_end
                },
                "filter_type": 0,
                "file_format": 0,
                "bill_type": 1,
                "product_id": ""
            }
        }
        aff_export_order_response = requests.post(url, headers=self.headers, json=payload).json()
        if aff_export_order_response['message'] != "success":
            return aff_export_order_response
        task_id = self.get_export_history_aff_orders()
        export_link = self.export_link_aff_orders(task_id)
        content = self.dowload_content(export_link)
        with open(f"orders_aff_tiktok/aff_orders_{time.time()}.csv", "wb") as f:
            f.write(content.content)
        return f"orders_aff_tiktok/aff_orders_{time.time()}.csv"
    
    def get_income_export_file_id(self):
        url = "https://seller-vn.tiktok.com/api/v2/pay/settlement/file/list"
        response = requests.get(url, headers=self.headers).json()
        file = response['data']['files'][0]
        if file['status'] != 2:
            logging.info(f"File is not finished, waiting for 2 seconds, file_id: {file['file_id']}")
            time.sleep(2)
            return self.get_income_export_file_id()
        else:
            return file['file_id']
        
    def get_income_export_url(self, file_id):
        url = f"https://seller-vn.tiktok.com/api/v1/pay/settlement/file/download?file_id={file_id}"
        response = requests.get(url, headers=self.headers).json()
        download_url = response['data']['url']
        # Ensure the URL has a proper protocol scheme and hostname
        if not download_url.startswith(('http://', 'https://')):
            # The URL appears to be a relative path, so we need to construct the full URL
            if download_url.startswith('/'):
                download_url = 'https://seller-vn.tiktok.com' + download_url
            else:
                download_url = 'https://seller-vn.tiktok.com/' + download_url
        return download_url
        
    def get_income_export(self, begin_date, end_date):
        logging.info(f"Begin date: {begin_date}, End date: {end_date}")
        url = "https://seller-vn.tiktok.com/api/v2/pay/settlement/file/export"
        payload = {
            "period": {
                "begin_date":begin_date,
                "end_date":end_date,
                "time_type":1
                },
            "file_type":1,
            "statement_version":0
            }
        response = requests.post(url, headers=self.headers, json=payload).json()
        if response['message'] == "Please wait while we prepare your files for download":
            logging.info(f"Please wait while we prepare your files for download, waiting for 5 seconds")
            time.sleep(5)
            return self.get_income_export(begin_date, end_date)
        file_id = self.get_income_export_file_id()
        download_url = self.get_income_export_url(file_id)
        logging.info(download_url)
        content = self.dowload_content(download_url)
        os.makedirs("income", exist_ok=True)
        with open(f"income_tiktok/income_{time.time()}.csv", "wb") as f:
            f.write(content.content)
        return f"income_tiktok/income_{time.time()}.csv"