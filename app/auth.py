import os
import hashlib
from dotenv import load_dotenv

import mysql.connector


mysql_config = {
    "host": os.getenv("MYSQL_HOST", "db"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE"),
}


def get_mysql_connection():
    return mysql.connector.connect(**mysql_config)


def register_user(username, password_hash):
    """
    Trả về True nếu đăng ký thành công,
    False nếu username đã tồn tại hoặc có lỗi khác.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor()
    try:
        # Chèn thẳng vào bảng users đã có sẵn
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )
        conn.commit()
        return True
    except mysql.connector.IntegrityError:
        # Đây sẽ bắt trường hợp username trùng (UNIQUE constraint)
        return False
    finally:
        cursor.close()
        conn.close()


def login_user(username, password_hash):
    """
    Trả về True nếu tìm thấy username + password_hash khớp,
    False nếu không khớp hoặc có lỗi.
    """
    conn = get_mysql_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username = %s AND password_hash = %s",
        (username, password_hash),
    )
    found = cursor.fetchone() is not None

    cursor.close()
    conn.close()
    return found
