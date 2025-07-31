import os
import hashlib
from dotenv import load_dotenv

from pymongo import MongoClient
from bson.binary import Binary

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME", "test")


def get_mongo_collection():
    client = MongoClient(mongo_uri)
    db = client[mongo_dbname]
    return db["users"]


def register_user(username, password_hash):
    """
    Trả về True nếu đăng ký thành công,
    False nếu username đã tồn tại hoặc có lỗi khác.
    """
    users = get_mongo_collection()
    try:
        if users.find_one({"username": username}):
            return False  # Đã tồn tại username
        users.insert_one({"username": username, "password_hash": password_hash})
        return True
    except Exception as e:
        print(e)
        return False


def login_user(username, password_hash):
    """
    Trả về True nếu tìm thấy username + password_hash khớp,
    False nếu không khớp hoặc có lỗi.
    """
    users = get_mongo_collection()
    return (
        users.find_one({"username": username, "password_hash": password_hash})
        is not None
    )


def save_avatar(username, file_bytes):
    """
    Lưu raw bytes của file (ảnh) vào cột avatar_blob.
    """
    users = get_mongo_collection()
    # Lưu file_bytes dưới dạng Binary cho MongoDB
    users.update_one(
        {"username": username}, {"$set": {"avatar_blob": Binary(file_bytes)}}
    )


def get_avatar_blob(username):
    """
    Lấy bytes của avatar đã lưu.
    Trả về None nếu chưa có.
    """
    users = get_mongo_collection()
    user = users.find_one({"username": username}, {"avatar_blob": 1})
    return user.get("avatar_blob") if user and "avatar_blob" in user else None
