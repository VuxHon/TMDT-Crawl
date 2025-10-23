import re
from typing import Dict, Any
from datetime import datetime
import pytz
from urllib.parse import unquote, urlparse, parse_qs
import json
import logging

class Helper:
    @staticmethod
    def parse_curl(curl_command: str) -> Dict[str, Any]:
        url_match = re.search(r"curl '([^']*)'", curl_command)
        url = url_match.group(1) if url_match else None

        headers = re.findall(r"-H '([^']*)'", curl_command)
        headers_dict = {}
        cookies = None
        authorization = None
        for header in headers:
            key, value = header.split(": ", 1)
            headers_dict[key] = value
            if key.lower() == 'cookie':
                cookies = value
            if key.lower() == 'authorization':
                authorization = value

        data_match = re.search(r"--data-raw '([^']*)'", curl_command)
        data = data_match.group(1) if data_match else None

        return {
            "url": url,
            "headers": headers_dict,
            "cookies": cookies,
            "authorization": authorization,
            "data": data
        }
    
    @staticmethod
    def parse_cookies_string_into_dict(cookies_string: str) -> Dict[str, str]:
        return dict(cookie.split("=", 1) for cookie in cookies_string.split("; ") if "=" in cookie)
    
    @staticmethod
    def to_unix_timestamp(date_input, is_end_date=False, timezone='Asia/Ho_Chi_Minh'):
        """
        Convert a date to a Unix timestamp.
        
        Args:
        date_input (str or datetime): The date to convert. If string, format should be 'YYYY-MM-DD'.
        is_end_date (bool): If True, set time to 23:59:59, otherwise 00:00:00.
        timezone (str): The timezone to use. Defaults to 'Asia/Ho_Chi_Minh'.
        
        Returns:
        int: The Unix timestamp (seconds since epoch).
        """
        if isinstance(date_input, str):
            # If input is a string, parse it to a datetime object
            date_obj = datetime.strptime(date_input, '%Y-%m-%d')
        elif isinstance(date_input, datetime):
            # If input is already a datetime object, use it directly
            date_obj = date_input
        else:
            raise ValueError("Input must be a string 'YYYY-MM-DD' or a datetime object")
        
        # Set the time to the end of the day if is_end_date is True, otherwise to the start of the day
        date_obj = date_obj.replace(
            hour=23 if is_end_date else 0,
            minute=59 if is_end_date else 0,
            second=59 if is_end_date else 0,
            microsecond=0
        )
        
        # Set the timezone
        tz = pytz.timezone(timezone)
        date_obj = tz.localize(date_obj)
        
        # Convert to Unix timestamp
        return int(date_obj.timestamp())
    
    @staticmethod
    def to_unix_timestamp_milliseconds(date_input, is_end_date=False, timezone='Asia/Ho_Chi_Minh'):
        return str(Helper.to_unix_timestamp(date_input, is_end_date, timezone) * 1000)
    
    @staticmethod
    def to_unix_timestamp_second(date_input, is_end_date=False, timezone='Asia/Ho_Chi_Minh'):
        return int(Helper.to_unix_timestamp(date_input, is_end_date, timezone))
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        Make the filename safe for all operating systems while preserving as much of the original name as possible.
        """
        # Decode URL-encoded characters
        filename = unquote(filename)
        
        # Replace forward slashes and backslashes with a suitable unicode character
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Replace colons with a unicode character
        filename = filename.replace(':', 'ː')
        
        # Replace other problematic characters
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove control characters
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # Ensure the filename doesn't start or end with a space or dot
        filename = filename.strip('. ')
        
        return filename
    
    @staticmethod
    def decode_curl_data_from_lark(encoded_string):
        try:
            # Parse the JSON string
            parsed_data = json.loads(encoded_string)
            
            # Function to recursively decode escaped quotes
            def decode_quotes(obj):
                if isinstance(obj, str):
                    return obj.replace(r'\\"', '"').replace(r'\\', '')
                elif isinstance(obj, dict):
                    return {k: decode_quotes(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [decode_quotes(i) for i in obj]
                else:
                    return obj
            
            # Decode the escaped quotes
            decoded_data = decode_quotes(parsed_data)
            
            return decoded_data
        except json.JSONDecodeError as e:
            logging.info(f"Error decoding JSON: {e}")
            return None
        
    @staticmethod
    def get_url_params(url):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        # parse_qs returns values as lists, simplify to single values if only one
        simplified_params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        return simplified_params