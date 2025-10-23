import requests
import json
import library.config as cf
import logging
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Lark:
    def __init__(self):
        self.app_id = cf.APP_ID
        self.app_secret = cf.APP_SECRET
        self.app_access_token: str = ""
        self.tenant_access_token: str = ""
        self.expire: int = 0
        self.__get_access_token()

    def __get_access_token(self) -> None:
        url = 'https://open.larksuite.com/open-apis/auth/v3/app_access_token/internal'
        headers = {'Content-Type': 'application/json'}
        payload = {
            'app_id': self.app_id,
            'app_secret': self.app_secret
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get('code') == 0:
                self.app_access_token = response_data['app_access_token']
                self.expire = response_data['expire']
                self.tenant_access_token = response_data['tenant_access_token']
                logger.info("Access token fetched successfully")
            else:
                raise Exception(f"Error: {response_data.get('msg', 'Unknown error')}")
        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {str(e)}")
            raise

    def fetch_tokens(self) -> Dict[str, str]:
        return {
            'app_access_token': self.app_access_token,
            'tenant_access_token': self.tenant_access_token
        }
    
    def get_lark_base_record(self, base_id: str, table_id: str, record_id: str, field: str = 'all') -> Any:
        url = f'https://open.larksuite.com/open-apis/bitable/v1/apps/{base_id}/tables/{table_id}/records/{record_id}'
        headers = {'Authorization': f'Bearer {self.tenant_access_token}'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()['data']['record']['fields']
            return data if field == 'all' else data[field]
        except requests.RequestException as e:
            logger.error(f"Error fetching Lark base record: {str(e)}")
            raise

    @staticmethod
    def send_message_to_lark(message: str, webhook = None) -> None:
        if webhook == None:
            webhook = cf.PERSONAL_LARK_WEBHOOK
        headers = {'Content-Type': 'application/json'}
        data = {"message": message}
        try:
            response = requests.post(webhook, headers=headers, json=data)
            response.raise_for_status()
            logger.info("Message sent to Lark successfully")
        except requests.RequestException as e:
            logger.error(f"Error sending message to Lark: {str(e)}")
            raise