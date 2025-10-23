import requests
from library.lark import Lark
import library.config as cf
import json
from library.helper import Helper
import os
import sys
import io
import logging
class Sapo:
    def __init__(self):
        self.lark_helper = Lark()
        self.headers = None
        self._init_headers()
        
    def _init_headers(self):
        curl_data = self.lark_helper.get_lark_base_record(cf.PEEKIE_BASE_ID, cf.PEEKIE_TABLE_ID, cf.PEEKIE_RECORD_ID["SAPO"], "body")
        # Replace escaped double quotes with regular double quotes
        # json_string = curl_data.replace(r'\\"', '"').replace(r'\\', '')

        # Parse the JSON string into a Python dictionary
        json_object = Helper.decode_curl_data_from_lark(curl_data)
        self.headers = json_object['headers']
    def get_toship_orders_info(self, shop_id, platform="Shopee", page=1):
        url = "https://market-place.sapoapps.vn/v2/orders"
        if platform == "Shopee":
            channelOrderStatus = "PROCESSED,READY_TO_SHIP,RETRY_SHIP"
        elif platform == "Tiktok":
            channelOrderStatus = "AWAITING_SHIPMENT,AWAITING_COLLECTION"
        else:
            raise ValueError(f"Sàn {platform} không tồn tại")
        # https://market-place.sapoapps.vn/v2/orders?page=1&limit=20&connectionIds=108706,108710,108720,109488,135519&channelOrderStatus=PROCESSED,READY_TO_SHIP,RETRY_SHIP,UNPAID&sortBy=ISSUED_AT&orderBy=desc
        params = {
            "page" : page,
            "limit" : 250,
            "connectionIds" : shop_id,
            "channelOrderStatus" : channelOrderStatus,
            "sortBy" : "ISSUED_AT",
            "orderBy" : "desc"
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def get_order_info_by_tracking_number(self, tracking_number):
        url = f"https://market-place.sapoapps.vn/v2/orders"
        params = {
            "page" : 1,
            "limit" : 20,
            "connectionIds" : "108706,108710,135519,143370,117719,149073",
            "query" : tracking_number,
            "sortBy" : "ISSUED_AT",
            "orderBy" : "desc"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def get_order_processed_shopee(self, page=1):
        url = "https://market-place.sapoapps.vn/v2/orders"
        params = {
            "page" : page,
            "limit" : 250,
            "connectionIds" : "108706,108710,135519,143370,149073",
            "channelOrderStatus" : "PROCESSED",
            "sortBy" : "ISSUED_AT",
            "orderBy" : "desc"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def get_order_awaiting_collection_tiktok(self, page=1):
        url = "https://market-place.sapoapps.vn/v2/orders"
        params = {
            "page" : page,
            "limit" : 250,
            "connectionIds" : "117719",
            "channelOrderStatus" : "AWAITING_COLLECTION",
            "sortBy" : "ISSUED_AT",
            "orderBy" : "desc"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def count_order_processed_shopee(self):
        url = "https://market-place.sapoapps.vn/v2/orders/order-counter"
        params = {
            "connection_ids" : "108706,108710,135519,143370,149073",
            "channel_order_statuses" : "PROCESSED"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def count_order_unprocessed_shopee(self):
        url = "https://market-place.sapoapps.vn/v2/orders/order-counter"
        params = {
            "connection_ids" : "108706,108710,135519,143370,149073",
            "channel_order_statuses" : "READY_TO_SHIP,RETRY_SHIP"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def get_order_shopee_to_scan(self, page=1):
        url = "https://market-place.sapoapps.vn/v2/orders"
        params = {
            "page" : page,
            "limit" : 250,
            "connectionIds" : "108706,108710,135519,143370,149073",
            "channelOrderStatus" : "PROCESSED,CANCELLED",
            "printStatus": 1,
            "sortBy" : "ISSUED_AT",
            "orderBy" : "desc"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def count_order_awaiting_collection_tiktok(self):
        url = "https://market-place.sapoapps.vn/v2/orders/order-counter"
        params = {
            "connection_ids" : "117719",
            "channel_order_statuses" : "AWAITING_COLLECTION"
        }
        response = requests.get(url, params=params, headers=self.headers)
        return response
    def get_shipment_spx_ngoai_san(self, spx_tn):
        url = "https://spx.vn/shipment/order/open/order/get_order_info"
        params = {
            "spx_tn": spx_tn.upper(),
            "language_code": "vi"
        }
        response = requests.get(url, params=params, headers=self.headers)
        logging.info(f"SPX TN: {spx_tn.upper()}")
        return response