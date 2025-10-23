import library.config as cf
from library.lark import Lark
from library.helper import Helper
import logging
from typing import Tuple, Dict, Any, Optional
import time
import json
from random import randrange
import requests
import logging
import re
class Shopee:
    def __init__(self, shop_name: str):
        self.shop_name = shop_name
        self.lark_helper = Lark()
        self.cookies_dict: Dict[str, str] = {}
        self.headers_dict: Dict[str, str] = {}
        self.SPC_CDS: str = ""
        self._get_shopee_curl_data()
        # self._validate_and_init_cookies()
    
    # def _validate_and_init_cookies(self) -> None:
    #     curl_data = self._get_shopee_curl_data()
    #     headers_array = curl_data['headers']
    #     cookies_array = Helper.parse_cookies_string_into_dict(curl_data['cookies'])
    #     spc_cds = cookies_array['SPC_CDS']
    #     self.headers_dict = headers_array
    #     self.cookies_dict = cookies_array
    #     self.curl_data = curl_data
    #     self.cookies_dict['SPC_CDS'] = spc_cds
    #     print(self.cookies_dict)
    #     print(self.headers_dict)
    def _get_shopee_curl_data(self) -> None:
        record_id = cf.PEEKIE_RECORD_ID.get(self.shop_name)
        record_info = self.lark_helper.get_lark_base_record(cf.PEEKIE_BASE_ID, cf.PEEKIE_TABLE_ID, record_id, 'body')
        data_json = json.loads(record_info)
        self.headers_dict = data_json['headers']
        self.cookies_dict = data_json['headers']['Cookie']
        self.get_spc_cds()
    def get_spc_cds(self) -> str:
        match = re.search(r"SPC_CDS=([^;]+)", self.cookies_dict)
        self.SPC_CDS = match.group(1) if match else None
    def get_mass_shipment_filter_meta(self):
        url = "https://banhang.shopee.vn/api/v3/order/get_mass_shipment_filter_meta"
        params = {
            "SPC_CDS": self.SPC_CDS
        }
        payload = {
            "last_selected_filter":0,
            "tab":300,
            "all_shipping_methods":[50018,50029,50022,50034,50012,29,50021,50023,30,50020,50026,50031,50036,15,14,50032,0],
            "shipping_method":14,
            "ofg_process_status":1,
            "pre_order":2,
            "entity_type":1,
            "need_merged_list": False,
            "shipping_urgency":1,"process_status":1
        }
        response = requests.post(url, params=params, headers=self.headers_dict, json=payload)
        return response
    def search_mass_shipment_index(self, shipping_method: int, shipping_urgency: int):
        url = "https://banhang.shopee.vn/api/v3/order/search_mass_shipment_index"
        params = {
            "SPC_CDS": self.SPC_CDS
        }
        payload = {
            "mass_shipment_tab":301,
            "pagination":{
                "from_page_number":1,
                "page_number":1,
                "page_size":200
            },
            "filter":{
                "shipping_method":shipping_method,
                "is_single_item":0,
                "pre_order":2,
                "shipping_urgency_filter":{
                    "shipping_urgency":shipping_urgency
                    },
                "product_location_ids":[""],
                "process_status":0,
                "ofg_process_status":0},
            "sort":{
                "sort_type":2,
                "ascending":True
                },
            "entity_type":1}
        response = requests.post(url, params=params, headers=self.headers_dict, json=payload)
        return response
    def get_mass_shipment_card_list_v2(self, package_param_list):
        url = "https://banhang.shopee.vn/api/v3/order/get_mass_shipment_card_list_v2"
        params = {
            "SPC_CDS": self.SPC_CDS
        }
        payload = {
            "mass_shipment_tab":301,
            "package_param_list": package_param_list,
            "need_count_down_desc": False
        }
        response = requests.post(url, params=params, headers=self.headers_dict, json=payload)
        return response
    
    def get_report_status(self, report_id):
        url = "https://banhang.shopee.vn/api/v3/settings/get_report/"
        params = {
            "SPC_CDS": self.SPC_CDS,
            "SPC_CDS_VER": 2,
            "report_id": report_id
        }
        response = requests.get(url, params=params, headers=self.headers_dict)
        return response.json()['data']['status']
    
    def get_content_report(self, report_id, report_file_name):
        url = "https://banhang.shopee.vn/api/v3/settings/download_report/"
        params = {
            "SPC_CDS": self.SPC_CDS,
            "SPC_CDS_VER": 2,
            "report_id": report_id
        }
        response = requests.get(url, params=params, headers=self.headers_dict)
        with open(f"orders_shopee/{report_file_name}", "wb") as f:
            f.write(response.content)
        return f"orders_shopee/{report_file_name}"
    
    def get_order_report(self, start_date, end_date):
        url = "https://banhang.shopee.vn/api/v3/order/request_order_report"
        params = {
            "SPC_CDS": self.SPC_CDS,
            "SPC_CDS_VER": 2,
            "start_date": start_date,
            "end_date": end_date,
            "language": "vn",
            "screening_condition": "order_creation_date",
            "parcel_level_filter": 0
        }
        response = requests.get(url, params=params, headers=self.headers_dict)
        report_id = response.json()['data']['report_id']
        report_file_name = response.json()['data']['report_file_name']
        
        while self.get_report_status(report_id) == 1:
            print("Waiting for report to be completed")
            time.sleep(2)
        return self.get_content_report(report_id, report_file_name)