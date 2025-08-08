import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from pymongo import MongoClient
from bson.binary import Binary

load_dotenv()

cred_path = os.getenv("FIREBASE_ADMIN_KEY")
if not cred_path:
    raise ValueError("FIREBASE_ADMIN_KEY chưa được khai báo trong .env hoặc đường dẫn bị sai!")
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME")


def get_mongo_collection():
    client = MongoClient(mongo_uri)
    db = client[mongo_dbname]
    return db["users"]


def verify_firebase_token(id_token):
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        print("Token verify fail:", e)
        return None


def register_user_to_mongo(uid, email, user_name):
    users = get_mongo_collection()
    
    if not users.find_one({"uid": uid}):
        print("Registering new user:", uid, email, user_name)
        users.insert_one({"uid": uid, "email": email, "user_name": user_name})
    return True


def save_avatar(uid, file_bytes):
    users = get_mongo_collection()
    users.update_one(
        {"uid": uid}, {"$set": {"avatar_blob": Binary(file_bytes)}}, upsert=True
    )


def get_avatar_blob(uid):
    users = get_mongo_collection()
    user = users.find_one({"uid": uid}, {"avatar_blob": 1})
    return user.get("avatar_blob") if user and "avatar_blob" in user else None


def get_user_profile(uid):
    users = get_mongo_collection()
    return users.find_one({"uid": uid})


def update_username_in_mongo(uid, new_username):
    users = get_mongo_collection()
    users.update_one({"uid": uid}, {"$set": {"user_name": new_username}})
