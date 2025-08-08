import io
import streamlit as st
import pyrebase
import os
from dotenv import load_dotenv

load_dotenv()

from auth import (
    verify_firebase_token,
    register_user_to_mongo,
    save_avatar,
    get_avatar_blob,
    get_user_profile,
    update_username_in_mongo,
)
import base64
import json
from report_generator import generate_stock_report
import pandas as pd
import numpy as np
import requests


# ==== Firebase config ====
firebase_config = {
    "apiKey": "AIzaSyBZCwLqhhkRm0_G1rOHBhc8ffV7RekdiHU",
    "authDomain": "stockinsights-840d9.firebaseapp.com",
    "projectId": "stockinsights-840d9",
    "storageBucket": "stockinsights-840d9.appspot.com",
    "messagingSenderId": "585866525295",
    "appId": "1:585866525295:web:ccfe3c1f16873802086b9a",
    "databaseURL": "",
}

firebase = pyrebase.initialize_app(firebase_config)
auth_fb = firebase.auth()

# ==== Gemini API Key ====
gemini_api_key = os.getenv("GEMINI_API_KEY")

# ==== Hàm gọi Gemnini
def call_genai_summary(report_data, stock_code, time_period):
    api_key = gemini_api_key
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"

    prompt = f"""
    Hãy tóm tắt ngắn gọn, chuyên nghiệp về mã cổ phiếu {stock_code} trong giai đoạn {time_period[0]} đến {time_period[1]} dựa trên dữ liệu JSON sau:
    {json.dumps(report_data, ensure_ascii=False, indent=2)}
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        summary = data["candidates"][0]["content"]["parts"][0]["text"]
        return summary
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"


# ==== Cấu hình trang và CSS tùy chỉnh ====
st.set_page_config(page_title="Stock Insights", page_icon="🔮", layout="centered")

# CSS - Theme "Cyberpunk Neon"
st.markdown("""
<style>
    /* === Main container styling === */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* === Center the main content and give it a max-width === */
    .main .block-container {
        max-width: 450px;
        padding: 2rem 1rem;
    }

    /* === Card styling with "frosted glass" effect (Applied to Tabs only) === */
    div[data-testid="stTabs-panel"] {
        background-color: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(12px);
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        border: 1px solid rgba(100, 116, 139, 0.3);
    }

    /* === Button styling === */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #30cfd0;
        padding: 12px 20px;
        color: white;
        background: linear-gradient(90deg, #30cfd0, #330867);
        transition: all 0.3s ease-in-out;
        font-weight: 600;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px #30cfd0;
        transform: translateY(-2px);
    }
    .stButton>button:focus {
        outline: none !important;
        box-shadow: 0 0 25px #30cfd0 !important;
    }
    
    /* === Input fields styling === */
    .stTextInput label {
        color: #c9d1d9 !important; /* Make label text light and visible */
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: block;
    }
    .stTextInput>div>div>input {
        background-color: rgba(15, 23, 42, 0.5);
        border: 1px solid #64748b;
        border-radius: 8px;
        padding: 12px;
        color: #ffffff;
    }
    .stTextInput>div>div>input:focus {
        border-color: #30cfd0;
        box-shadow: 0 0 10px rgba(48, 207, 208, 0.5);
    }
    .stTextInput>div>div>input::placeholder {
        color: #94a3b8;
    }

    /* === Header styling === */
    h1 {
        text-align: center;
        color: #ffffff;
        margin-bottom: 0.5rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(48, 207, 208, 0.5);
    }
    
    /* === Sub-header for login/register === */
    .auth-subheader {
        text-align: center;
        color: #94a3b8;
        margin-bottom: 2rem;
    }
    
</style>
""", unsafe_allow_html=True)


def render_avatar(uid):
    avatar_bytes = get_avatar_blob(uid)
    avatar_html = ""
    if avatar_bytes:
        img_base64 = base64.b64encode(avatar_bytes).decode()
        avatar_html = f"""
            <div style='display:flex; justify-content:center; margin-bottom: 1rem;'>
                <img src="data:image/png;base64,{img_base64}"
                     style="border-radius:50%; border:4px solid #30cfd0; width:120px; height:120px; object-fit:cover; box-shadow:0 0 20px rgba(48, 207, 208, 0.5);">
            </div>
        """
    else:
        avatar_html = """
            <div style='display:flex; flex-direction:column; align-items:center; margin-bottom: 1rem;'>
                <div style='border-radius:50%; background:linear-gradient(135deg, #30cfd0, #330867);
                            width:120px; height:120px; display:flex; align-items:center; justify-content:center;
                            box-shadow:0 0 20px rgba(48, 207, 208, 0.3);'>
                    <span style='font-size:3em; color:#fff;'>👤</span>
                </div>
                <div style='margin-top:8px; color:#94a3b8; font-size:0.9em;'>Chưa có avatar</div>
            </div>
        """
    st.markdown(avatar_html, unsafe_allow_html=True)


# ==== Main App Logic ====
st.markdown("<h1>Stock Insights 🔮</h1>", unsafe_allow_html=True)

if "uid" not in st.session_state:
    st.markdown("<p class='auth-subheader'>Chào mừng! Vui lòng đăng nhập hoặc đăng ký.</p>", unsafe_allow_html=True)
    
    login_tab, register_tab = st.tabs(["✨ Đăng nhập", "📝 Đăng ký"])

    # --- FORM ĐĂNG NHẬP ---
    with login_tab:
        email_login = st.text_input("Email", key="email_login", placeholder="you@example.com")
        password_login = st.text_input("Mật khẩu", type="password", key="password_login", placeholder="••••••••")
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        if st.button("Đăng nhập", key="login_btn", use_container_width=True):
            if not email_login or not password_login:
                st.warning("Vui lòng nhập đầy đủ email và mật khẩu.")
            else:
                try:
                    user = auth_fb.sign_in_with_email_and_password(email_login, password_login)
                    id_token = user["idToken"]
                    info = verify_firebase_token(id_token)
                    if info:
                        st.session_state["uid"] = info["uid"]
                        st.session_state["user_email"] = info.get("email", "")
                        profile = get_user_profile(info["uid"])
                        st.session_state["user_name"] = profile.get("user_name", "") if profile else ""
                        st.success(f"Đăng nhập thành công! Xin chào {st.session_state['user_name']}.")
                        st.rerun()
                    else:
                        st.error("Token không hợp lệ hoặc tài khoản chưa xác thực email.")
                except Exception as e:
                    err = str(e)
                    if "EMAIL_NOT_FOUND" in err or "INVALID_PASSWORD" in err:
                        st.error("Sai email hoặc mật khẩu!")
                    else:
                        st.error("Không thể đăng nhập. Vui lòng thử lại.")

    # --- FORM ĐĂNG KÝ ---
    with register_tab:
        with st.form("registration_form", clear_on_submit=True):
            user_name_reg = st.text_input("Tên người dùng", placeholder="Nguyen Van A")
            email_reg = st.text_input("Email", placeholder="you@example.com")
            password_reg = st.text_input("Mật khẩu", type="password", placeholder="••••••••")
            password_confirm_reg = st.text_input("Nhập lại mật khẩu", type="password", placeholder="••••••••")
            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Đăng ký", use_container_width=True)

            if submitted:
                if not email_reg or not password_reg or not password_confirm_reg or not user_name_reg:
                    st.warning("Vui lòng nhập đầy đủ thông tin.")
                elif password_reg != password_confirm_reg:
                    st.warning("Mật khẩu không khớp.")
                else:
                    try:
                        reg = auth_fb.create_user_with_email_and_password(email_reg, password_reg)
                        register_user_to_mongo(reg["localId"], email_reg, user_name_reg)
                        st.success("Đăng ký thành công! Giờ bạn có thể đăng nhập.")
                        st.balloons()
                    except Exception as e:
                        err = str(e)
                        if "EMAIL_EXISTS" in err:
                            st.error("Email đã tồn tại!")
                        elif "WEAK_PASSWORD" in err:
                            st.error("Mật khẩu phải có ít nhất 6 ký tự!")
                        else:
                            st.error("Không thể đăng ký. Vui lòng thử lại.")
else:
    # ==== TRANG CÁ NHÂN (PROFILE VIEW) ====
    col1, col2, col3 = st.columns([0.5, 3, 0.5])

    with col2:
        profile = get_user_profile(st.session_state["uid"])
        
        render_avatar(st.session_state["uid"])

        st.html(f"<h3 style='text-align: center; color: #ffffff; margin-bottom: 0.25rem; font-weight: 600;'>{profile.get('user_name', '')}</h3>")
        st.html(f"<p style='text-align: center; color: #94a3b8; margin-bottom: 2rem;'>{st.session_state['user_email']}</p>")

        with st.expander("⚙️ Chỉnh sửa thông tin"):
            new_username = st.text_input(
                "Tên người dùng mới",
                value=profile.get("user_name", ""),
                key="edit_username",
            )
            if st.button("Lưu tên mới", use_container_width=True, key="save_name"):
                if new_username:
                    update_username_in_mongo(st.session_state["uid"], new_username)
                    st.success("Đã cập nhật tên người dùng!")
                    st.rerun()
                else:
                    st.warning("Tên người dùng không được để trống.")
            
            st.markdown("<hr style='margin: 1rem 0; border-color: rgba(100, 116, 139, 0.3);'>", unsafe_allow_html=True)
            
            file = st.file_uploader(
                "Thay đổi ảnh đại diện (png, jpg, jpeg)", type=["png", "jpg", "jpeg"]
            )
            if st.button("Lưu avatar", use_container_width=True, key="save_avatar"):
                if file:
                    save_avatar(st.session_state["uid"], file.read())
                    st.success("Đã lưu avatar!")
                    st.rerun()
                else:
                    st.warning("Hãy chọn ảnh trước khi lưu.")

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    
        if st.button("Đăng xuất", use_container_width=True, key="logout_btn"):
            st.session_state.clear()
            st.rerun()
            
    # ==== TRANG BÁO CÁO LAI (ĐÃ SỬA ĐỔI) ====
    st.markdown("<h2 style='text-align:center; color: #ffffff; margin-top: 2rem;'>📊 Báo cáo Cổ phiếu Thông minh</h2>", unsafe_allow_html=True)
    
    with st.form("report_form"):
        stock_code_input = st.text_input("Nhập mã cổ phiếu (ví dụ: VIC, HPG...)", value="HPG").upper()
        
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Từ ngày", value=pd.to_datetime("2025-05-01"))
        with col_end:
            end_date = st.date_input("Đến ngày", value=pd.to_datetime("now"))
            
        submitted = st.form_submit_button("Tạo báo cáo", use_container_width=True)

    if submitted and stock_code_input:
        with st.spinner(f'Đang tổng hợp và phân tích dữ liệu cho mã {stock_code_input}...'):
            report_data = generate_stock_report(stock_code_input, (str(start_date), str(end_date)))
            
            # Chỉ gọi GenAI nếu có dữ liệu để phân tích
            if report_data["overall_sentiment"]["positive_mentions"] > 0 or report_data["overall_sentiment"]["negative_mentions"] > 0:
                summary = call_genai_summary(report_data, stock_code_input, (str(start_date), str(end_date)))
            else:
                summary = f"Không tìm thấy đủ dữ liệu nổi bật cho mã **{stock_code_input}** trong khoảng thời gian đã chọn để tạo tóm tắt AI."

        # --- BẮT ĐẦU HIỂN THỊ BÁO CÁO ---
        
        st.markdown(f"---")
        st.markdown(f"<h3 style='text-align: center; color: #30cfd0;'>Báo cáo Phân tích cho {report_data['stock_code']}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Giai đoạn: {report_data['report_period']}</p>", unsafe_allow_html=True)

        # 1. Tóm tắt từ GenAI
        st.markdown("#### 🤖 Tóm tắt từ AI")
        st.info(summary)

        # 2. Tổng quan Cảm xúc
        st.markdown("#### 📊 Tổng quan Cảm xúc")
        sentiment = report_data['overall_sentiment']
        score = sentiment['score']
        trend_color = "normal"
        if sentiment['trend'] == "Tích cực": trend_color = "normal"
        if sentiment['trend'] == "Tiêu cực": trend_color = "inverse"
        
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

        # 3. Các Bảng Chi tiết
        st.markdown("---")
        
        col_events, col_risks = st.columns(2)
        with col_events:
            st.markdown("#### ⚡ Sự kiện Nổi bật")
            if report_data["key_events"]:
                # Kiểm tra key thực tế
                df_events = pd.DataFrame(report_data["key_events"])
                # Đổi tên cột nếu cần
                if 'avg_sentiment' in df_events.columns:
                    df_events = df_events.rename(columns={'entity_text': 'Sự kiện', 'avg_sentiment': 'Sentiment'})
                    show_cols = ['Sự kiện', 'count', 'Sentiment']
                elif 'sentiment' in df_events.columns:
                    df_events = df_events.rename(columns={'entity_text': 'Sự kiện'})
                    show_cols = ['Sự kiện', 'count', 'sentiment']
                else:
                    df_events = df_events.rename(columns={'entity_text': 'Sự kiện'})
                    show_cols = ['Sự kiện', 'count']
                st.dataframe(df_events[show_cols], use_container_width=True)
            else:
                st.write("Không có sự kiện nổi bật.")

        with col_risks:
            st.markdown("#### ⚠️ Rủi ro được đề cập")
            if report_data["key_risks_mentioned"]:
                df_risks = pd.DataFrame(report_data["key_risks_mentioned"])
                if 'avg_sentiment' in df_risks.columns:
                    df_risks = df_risks.rename(columns={'entity_text': 'Rủi ro', 'avg_sentiment': 'Sentiment'})
                    show_cols = ['Rủi ro', 'count', 'Sentiment']
                elif 'sentiment' in df_risks.columns:
                    df_risks = df_risks.rename(columns={'entity_text': 'Rủi ro'})
                    show_cols = ['Rủi ro', 'count', 'sentiment']
                else:
                    df_risks = df_risks.rename(columns={'entity_text': 'Rủi ro'})
                    show_cols = ['Rủi ro', 'count']
                st.dataframe(df_risks[show_cols], use_container_width=True)
            else:
                st.write("Không có rủi ro nổi bật.")

        st.markdown("#### 📈 Hành động Giá Chính")
        if report_data["key_price_actions"]:
            df_price = pd.DataFrame(report_data["key_price_actions"])
            if 'avg_sentiment' in df_price.columns:
                df_price = df_price.rename(columns={'entity_text': 'Hành động giá', 'avg_sentiment': 'Sentiment'})
                show_cols = ['Hành động giá', 'count', 'Sentiment']
            elif 'sentiment' in df_price.columns:
                df_price = df_price.rename(columns={'entity_text': 'Hành động giá'})
                show_cols = ['Hành động giá', 'count', 'sentiment']
            else:
                df_price = df_price.rename(columns={'entity_text': 'Hành động giá'})
                show_cols = ['Hành động giá', 'count']
            st.dataframe(df_price[show_cols], use_container_width=True)
        else:
            st.write("Không có hành động giá nổi bật.")
            
        # 4. Thực thể liên quan
        st.markdown("---")
        st.markdown("#### 🔗 Các Thực thể Liên quan nhiều nhất")
        related = report_data['top_related_entities']
        if any(related.values()):
            for etype, entities in related.items():
                if entities:
                    st.markdown(f"**{etype.replace('_', ' ').title()}:** {', '.join(entities)}")
        else:
            st.write("Không tìm thấy thực thể liên quan nổi bật.")
            
        # 5. Nguồn bài viết
        st.markdown("---")
        st.markdown("#### 📰 Nguồn Bài viết Tham khảo")
        if report_data["source_articles"]:
            for article in report_data["source_articles"]:
                st.markdown(f"- [{article['title']}]({article['source_url']}) - *Cảm xúc: {article['sentiment_label']}*")
        else:
            st.write("Không có bài viết nào trong khoảng thời gian này.")