import streamlit as st

st.set_page_config(page_title="Báo cáo - Stock Insights", page_icon="🔮", layout="wide")

import pandas as pd
from datetime import datetime
from report_generator import generate_stock_report
from utils import load_css, call_genai_summary

load_css()

if "uid" not in st.session_state:
    st.warning("Vui lòng đăng nhập để sử dụng tính năng này.")
    st.page_link("StockInsights.py", label="Về trang Đăng nhập", icon="🏠")
    st.stop()


# ==== Giao diện trang báo cáo ====
st.markdown("<h2>Báo cáo Cổ phiếu Thông minh</h2>", unsafe_allow_html=True)

# st.markdown("<div class='report-container'>", unsafe_allow_html=True)

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

    # --- HIỂN THỊ BÁO CÁO ---
    st.markdown(
        f"<h3 style='text-align: center; color: #30cfd0; margin-top:2rem;'>Báo cáo Phân tích cho {report_data.get('stock_code', stock_code_input)}</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align: center; color: #94a3b8;'>Giai đoạn: {report_data.get('report_period', 'N/A')}</p>", unsafe_allow_html=True)

    st.markdown("#### 🤖 Tóm tắt từ AI")
    st.info(summary)

    # Tổng quan cảm xúc
    st.markdown("#### 📊 Tổng quan Cảm xúc")
    sentiment = report_data['overall_sentiment']
    score = sentiment['score']
    trend_color = "normal"
    if sentiment['trend'] == "Tích cực":
        trend_color = "normal"
        if sentiment['trend'] == "Tiêu cực":
            trend_color = "inverse"

    st.metric(
        label="Điểm Cảm xúc (có trọng số thời gian)",
        value=f"{score:.2f}" if score is not None else "N/A",
        delta=sentiment['trend'],
        delta_color=trend_color
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("👍 Tích cực", sentiment['positive_mentions'])
    col2.metric("👎 Tiêu cực", sentiment['negative_mentions'])
    col3.metric("😐 Trung tính", sentiment['neutral_mentions'])

    # Các bảng chi tiết
    st.markdown("---")

    col_events, col_risks = st.columns(2)
    with col_events:
        st.markdown("#### ⚡ Sự kiện Nổi bật")
        if report_data["key_events"]:
            # Kiểm tra key thực tế
            df_events = pd.DataFrame(report_data["key_events"])
            if 'avg_sentiment' in df_events.columns:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện', 'avg_sentiment': 'Sentiment'})
                show_cols = ['Sự kiện', 'count', 'Sentiment']
            elif 'sentiment' in df_events.columns:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện'})
                show_cols = ['Sự kiện', 'count', 'sentiment']
            else:
                df_events = df_events.rename(
                    columns={'entity_text': 'Sự kiện'})
                show_cols = ['Sự kiện', 'count']
            st.dataframe(df_events[show_cols], use_container_width=True)
        else:
            st.write("Không có sự kiện nổi bật.")

    with col_risks:
        st.markdown("#### ⚠️ Rủi ro được đề cập")
        if report_data["key_risks_mentioned"]:
            df_risks = pd.DataFrame(report_data["key_risks_mentioned"])
            if 'avg_sentiment' in df_risks.columns:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro', 'avg_sentiment': 'Sentiment'})
                show_cols = ['Rủi ro', 'count', 'Sentiment']
            elif 'sentiment' in df_risks.columns:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro'})
                show_cols = ['Rủi ro', 'count', 'sentiment']
            else:
                df_risks = df_risks.rename(
                    columns={'entity_text': 'Rủi ro'})
                show_cols = ['Rủi ro', 'count']
            st.dataframe(df_risks[show_cols], use_container_width=True)
        else:
            st.write("Không có rủi ro nổi bật.")

    st.markdown("#### 📈 Hành động Giá Chính")
    if report_data["key_price_actions"]:
        df_price = pd.DataFrame(report_data["key_price_actions"])
        if 'avg_sentiment' in df_price.columns:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá', 'avg_sentiment': 'Sentiment'})
            show_cols = ['Hành động giá', 'count', 'Sentiment']
        elif 'sentiment' in df_price.columns:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá'})
            show_cols = ['Hành động giá', 'count', 'sentiment']
        else:
            df_price = df_price.rename(
                columns={'entity_text': 'Hành động giá'})
            show_cols = ['Hành động giá', 'count']
        st.dataframe(df_price[show_cols], use_container_width=True)
    else:
        st.write("Không có hành động giá nổi bật.")

    # Thực thể liên quan
    st.markdown("---")
    st.markdown("#### 🔗 Các Thực thể Liên quan nhiều nhất")
    related = report_data['top_related_entities']
    if any(related.values()):
        for etype, entities in related.items():
            if entities:
                st.markdown(
                    f"**{etype.replace('_', ' ').title()}:** {', '.join(entities)}")
    else:
        st.write("Không tìm thấy thực thể liên quan nổi bật.")

    # Nguồn bài viết
    st.markdown("---")
    st.markdown("#### 📰 Nguồn Bài viết Tham khảo")
    if report_data["source_articles"]:
        for article in report_data["source_articles"]:
            st.markdown(
                f"- [{article['title']}]({article['source_url']}) - *Cảm xúc: {article['sentiment_label']}*")
    else:
        st.write("Không có bài viết nào trong khoảng thời gian này.")

st.markdown("</div>", unsafe_allow_html=True)
