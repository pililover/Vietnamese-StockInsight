import os
import streamlit as st
from pymongo import MongoClient
from report_generator import show_report
from utils import load_css

mongo_uri = os.getenv("MONGO_URI")
mongo_dbname = os.getenv("MONGO_DBNAME")

def get_db():
    client = MongoClient(mongo_uri)
    db = client[mongo_dbname]
    return db["reports"]

reports_history = get_db()

st.set_page_config(page_title="Lịch sử - Stock Insights", page_icon="🔮", layout="centered")
load_css()

if "uid" not in st.session_state:
    st.warning("Vui lòng đăng nhập để sử dụng tính năng này.")
    st.page_link("StockInsights.py", label="Về trang Đăng nhập", icon="🏠")
    st.stop()

# ==== Giao diện trang lịch sử ====
st.markdown("<h2>Các báo cáo đã tạo</h2>", unsafe_allow_html=True)
search_code = st.text_input("Tìm theo mã cổ phiếu", "").upper()

query = {"uid": st.session_state["uid"]}
if search_code:
    query["report_data.stock_code"] = {"$regex": f"^{search_code}", "$options": "i"}

history = list(reports_history.find(query).sort("created_at", -1))

if history:
    for item in history:
        stock_code = item["report_data"]["stock_code"]
        period = item["report_data"]["report_period"]
        with st.expander(f"{stock_code}: {period}"):
            show_report(item["report_data"], item["summary"], item["report_data"]["stock_code"])
else:
    st.info("Chưa có báo cáo nào cả")