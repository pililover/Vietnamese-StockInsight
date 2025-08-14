import streamlit as st
import os
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from report_generator import generate_stock_report, show_report
from utils import load_css, call_genai_summary

def main():
    mongo_uri = os.getenv("MONGO_URI")
    mongo_dbname = os.getenv("MONGO_DBNAME")

    def get_db():
        client = MongoClient(mongo_uri)
        db = client[mongo_dbname]
        return db["reports"]

    reports_history = get_db()


    load_css()

    if "uid" not in st.session_state:
        st.warning("Vui lòng đăng nhập để sử dụng tính năng này.")
        st.page_link("StockInsights.py", label="Về trang Đăng nhập", icon="🏠")
        st.stop()

    # ==== Giao diện trang báo cáo ===
    st.markdown("<h2>Báo cáo Cổ phiếu Thông minh</h2>", unsafe_allow_html=True)

    # st.markdown("<div class='report-container'>", unsafe_allow_html=True)

    col_history, col_main = st.columns([1, 3])

    # ===== LEFT: Report History =====
    with col_history:
        st.markdown("<h4>Báo cáo đã xem</h4>", unsafe_allow_html=True)

        # Initialize history list
        if "reports_history_list" not in st.session_state:
            query = {"uid": st.session_state["uid"]}
            st.session_state["reports_history_list"] = list(
                reports_history.find(query).sort("created_at", -1)
            )

        history = st.session_state["reports_history_list"]

        if not history:
            st.info("Chưa có báo cáo nào được lưu.")
        else:
            for idx, report in enumerate(history):
                if st.button(
                    f"{report['report_data'].get('stock_code', 'N/A')} ({report['report_data'].get('report_period', 'N/A')})",
                    key=f"history_btn_{idx}"
                ):
                    # Update the selected report in session state
                    st.session_state["selected_report"] = report
                    st.session_state["show_form"] = False  # Hide form when viewing history

    # ===== RIGHT: Report View=====
    with col_main:
        if st.session_state.get("selected_report") and not st.session_state.get("show_form", False):
            selected = st.session_state["selected_report"]
            show_report(selected["report_data"], selected["summary"], selected["report_data"]["stock_code"])
            
            # Tạo báo cáo mới 
            if st.button("Tạo báo cáo mới", key="new_report_btn"):
                st.session_state["show_form"] = True
                st.session_state.pop("selected_report", None)
                st.rerun()
        
        else:
            with st.form("report_form"):
                stock_code_input = st.text_input(
                    "Nhập mã cổ phiếu (ví dụ: VIC, HPG...)", value="HPG").upper()

                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input(
                        "Từ ngày", value=pd.to_datetime("2025-05-01"))
                with col_end:
                    end_date = st.date_input("Đến ngày", value=datetime.now())

                submitted = st.form_submit_button("Tạo báo cáo", use_container_width=True)

            if submitted and stock_code_input:
                with st.spinner(f'Đang tổng hợp và phân tích dữ liệu cho mã {stock_code_input}...'):
                    report_data = generate_stock_report(
                        stock_code_input, (str(start_date), str(end_date)))

                    if report_data and (report_data["overall_sentiment"]["positive_mentions"] > 0 or report_data["overall_sentiment"]["negative_mentions"] > 0):
                        summary = call_genai_summary(
                            report_data, stock_code_input, (str(start_date), str(end_date)))
                    else:
                        summary = f"Không tìm thấy đủ dữ liệu nổi bật cho mã **{stock_code_input}** trong khoảng thời gian đã chọn để tạo tóm tắt AI."

                    # Save to MongoDB
                    inserted_id = reports_history.insert_one({
                        "uid": st.session_state["uid"],
                        "report_data": report_data,
                        "summary": summary,
                        "created_at": datetime.utcnow()
                    }).inserted_id

                    # Add new report to top of history
                    new_report = {
                        "_id": inserted_id,
                        "report_data": report_data,
                        "summary": summary,
                        "created_at": datetime.utcnow()
                    }
                    st.session_state["reports_history_list"].insert(0, new_report)

                    # Show new report
                    st.session_state["selected_report"] = new_report
                    st.session_state["show_form"] = False
                    st.rerun()
