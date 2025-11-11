import psycopg2,os
from psycopg2.extras import RealDictCursor
import logging
from contextlib import contextmanager
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv(), override=False)

host = os.getenv("POSTGRES_HOST")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
database = os.getenv("POSTGRES_DB")
port = os.getenv("POSTGRES_PORT")

# Cấu hình kết nối PostgreSQL
CONFIG = {
    "host": host,
    "port": port,
    "database": database,
    "user": user,
    "password": password,
}

class Postgres:
    """
    Class PostgreSQL để thực hiện các thao tác với database
    """

    def __init__(self, config=None):
        """
        Khởi tạo class Postgres
        Args:
            config (dict): Cấu hình kết nối database (optional)
        """
        self.config = config or CONFIG
        self.conn = None
        self.cursor = None

    def connect(self):
        """
        Tạo kết nối đến PostgreSQL database
        Returns:
            bool: True nếu kết nối thành công
        """
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logging.info("Kết nối PostgreSQL thành công")
            return True
        except psycopg2.Error as e:
            logging.error(f"Lỗi kết nối PostgreSQL: {e}")
            raise

    def disconnect(self):
        """
        Đóng kết nối PostgreSQL
        """
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Đã đóng kết nối PostgreSQL")

    def is_connected(self):
        """
        Kiểm tra xem có đang kết nối không
        Returns:
            bool: True nếu đang kết nối
        """
        return self.conn is not None and not self.conn.closed

    def ensure_connection(self):
        """
        Đảm bảo có kết nối đến database
        """
        if not self.is_connected():
            self.connect()

    def execute(self, query, params=None):
        """
        Thực thi query_handle_order_tts SQL thuần
        Args:
            query (str): SQL query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            cursor: Cursor object để xử lý kết quả
        """
        try:
            self.ensure_connection()
            self.cursor.execute(query, params)
            return self.cursor
        except psycopg2.Error as e:
            logging.error(f"Lỗi thực thi query_handle_order_tts: {e}")
            raise

    def fetch_all(self, query, params=None):
        """
        Thực thi query_handle_order_tts và lấy tất cả kết quả
        Args:
            query (str): SQL query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            list: Danh sách kết quả
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=None):
        """
        Thực thi query_handle_order_tts và lấy một kết quả
        Args:
            query (str): SQL query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            dict: Một kết quả hoặc None
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_many(self, query, params=None, size=1000):
        """
        Thực thi query_handle_order_tts và lấy nhiều kết quả theo batch
        Args:
            query (str): SQL query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
            size (int): Số lượng kết quả mỗi lần fetch
        Returns:
            list: Danh sách kết quả
        """
        cursor = self.execute(query, params)
        return cursor.fetchmany(size)

    def commit(self):
        """
        Commit transaction
        """
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """
        Rollback transaction
        """
        if self.conn:
            self.conn.rollback()

    def insert(self, query, params=None):
        """
        Thực thi INSERT query_handle_order_tts
        Args:
            query (str): INSERT query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            int: ID của record vừa insert (nếu có)
        """
        try:
            self.execute(query, params)
            self.commit()

            # Lấy ID của record vừa insert nếu có
            if self.cursor.description:
                return self.cursor.fetchone()[0] if self.cursor.rowcount > 0 else None
            return None
        except psycopg2.Error as e:
            self.rollback()
            logging.error(f"Lỗi thực thi INSERT: {e}")
            raise

    def update(self, query, params=None):
        """
        Thực thi UPDATE query_handle_order_tts
        Args:
            query (str): UPDATE query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            int: Số dòng bị ảnh hưởng
        """
        try:
            self.execute(query, params)
            self.commit()
            return self.cursor.rowcount
        except psycopg2.Error as e:
            self.rollback()
            logging.error(f"Lỗi thực thi UPDATE: {e}")
            raise

    def delete(self, query, params=None):
        """
        Thực thi DELETE query_handle_order_tts
        Args:
            query (str): DELETE query_handle_order_tts
            params (tuple/list): Tham số cho query_handle_order_tts
        Returns:
            int: Số dòng bị xóa
        """
        try:
            self.execute(query, params)
            self.commit()
            return self.cursor.rowcount
        except psycopg2.Error as e:
            self.rollback()
            logging.error(f"Lỗi thực thi DELETE: {e}")
            raise

    def execute_many(self, query, params_list):
        """
        Thực thi query_handle_order_tts với nhiều bộ tham số
        Args:
            query (str): SQL query_handle_order_tts
            params_list (list): Danh sách các bộ tham số
        Returns:
            int: Số dòng bị ảnh hưởng
        """
        try:
            self.ensure_connection()
            self.cursor.executemany(query, params_list)
            self.commit()
            return self.cursor.rowcount
        except psycopg2.Error as e:
            self.rollback()
            logging.error(f"Lỗi thực thi execute_many: {e}")
            raise

    @contextmanager
    def transaction(self):
        """
        Context manager cho transaction
        Usage:
            with db.transaction():
                db.execute("INSERT INTO ...")
                db.execute("UPDATE ...")
        """
        try:
            self.ensure_connection()
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise

    def __enter__(self):
        """
        Context manager entry
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit
        """
        if exc_type:
            self.rollback()
        self.disconnect()

    def __del__(self):
        """
        Destructor - đóng kết nối khi object bị hủy
        """
        self.disconnect()


# Ví dụ sử dụng
if __name__ == "__main__":
    # Cách 1: Sử dụng thông thường
    db = Postgres()

    try:
        # Kết nối
        db.connect()

        # Thực thi query_handle_order_tts thuần
        results = db.fetch_all("""SELECT * FROM "orders_tiktok" LIMIT 5""")
        print("Kết quả orders_tiktok:", results)
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        db.disconnect()