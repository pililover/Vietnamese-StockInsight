import streamlit as st
import pyrebase
import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ==== Firebase Config & Initialization ====
def initialize_firebase():
    """Khởi tạo và trả về các đối tượng Firebase. Sử dụng singleton pattern."""
    if "firebase_app" not in st.session_state:
        firebase_config = {
            "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyBZCwLqhhkRm0_G1rOHBhc8ffV7RekdiHU"),
            "authDomain": "stockinsights-840d9.firebaseapp.com",
            "projectId": "stockinsights-840d9",
            "storageBucket": "stockinsights-840d9.appspot.com",
            "messagingSenderId": "585866525295",
            "appId": "1:585866525295:web:ccfe3c1f16873802086b9a",
            "databaseURL": "",
        }
        st.session_state.firebase_app = pyrebase.initialize_app(firebase_config)
    
    auth_fb = st.session_state.firebase_app.auth()
    return auth_fb

# ==== CSS Dùng chung ====
def load_css():
    """Tải CSS theme Cyberpunk Neon."""
    st.markdown("""
    <style>
        /* === Hide default sidebar === */
        section[data-testid="stSidebar"] {display: none;}

        /* === Main container styling === */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        
        /* === Main content area styling === */
        .main .block-container {
            max-width: 950px;
            padding: 2rem 1.5rem;
        }
        /* CSS cho trang login/register hẹp hơn */
        .not-logged-in .main .block-container {
            max-width: 450px;
        }

        /* === Card styling with "frosted glass" effect === */
        div[data-testid="stTabs-panel"], .report-container {
            background-color: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border: 1px solid rgba(100, 116, 139, 0.3);
        }

        /* === Sidebar styling === */
        div[data-testid="stSidebar"] > div:first-child {
            background: linear-gradient(180deg, #16213e, #0d1117);
            border-right: 1px solid rgba(100, 116, 139, 0.3);
        }
        div[data-testid="stSidebar"] h2 {
            color: #ffffff;
            text-align: center;
            text-shadow: 0 0 5px #30cfd0;
            margin-top: 1rem;
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
        .stTextInput label, .stDateInput label {
            color: #c9d1d9 !important;
            font-weight: 600;
            margin-bottom: 0.5rem;
            display: block;
        }
        .stTextInput>div>div>input, .stDateInput>div>div>input {
            background-color: rgba(15, 23, 42, 0.5);
            border: 1px solid #64748b;
            border-radius: 8px;
            padding: 12px;
            color: #ffffff;
        }
        .stTextInput>div>div>input:focus, .stDateInput>div>div>input:focus {
            border-color: #30cfd0;
            box-shadow: 0 0 10px rgba(48, 207, 208, 0.5);
        }
        .stTextInput>div>div>input::placeholder {
            color: #94a3b8;
        }

        /* === Header styling === */
        h1, h2 {
            text-align: center;
            color: #ffffff;
            font-weight: 700;
            letter-spacing: 1px;
            text-shadow: 0 0 10px rgba(48, 207, 208, 0.5);
        }
        h1 { margin-bottom: 0.5rem; }
        h2 { margin-top: 1rem; }
        
        /* === Sub-header for login/register === */
        .auth-subheader {
            text-align: center;
            color: #94a3b8;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)


# ==== Hàm Render Avatar ====
def render_avatar(uid, container, get_avatar_blob_func):
    """Render avatar trong một container cụ thể."""
    avatar_bytes = get_avatar_blob_func(uid)
    if avatar_bytes:
        img_base64 = base64.b64encode(avatar_bytes).decode()
        avatar_html = f'<img src="data:image/png;base64,{img_base64}" style="border-radius:50%; border:4px solid #30cfd0; width:120px; height:120px; object-fit:cover; box-shadow:0 0 20px rgba(48, 207, 208, 0.5);">'
    else:
        avatar_html = """
            <div style='border-radius:50%; background:linear-gradient(135deg, #30cfd0, #330867);
                        width:120px; height:120px; display:flex; align-items:center; justify-content:center;
                        box-shadow:0 0 20px rgba(48, 207, 208, 0.3);'>
                <span style='font-size:3em; color:#fff;'>👤</span>
            </div>
            <div style='margin-top:8px; color:#94a3b8; font-size:0.9em;'>Chưa có avatar</div>
        """
    container.html(f"<div style='display:flex; flex-direction:column; align-items:center; margin-bottom: 1rem;'>{avatar_html}</div>")

# ==== Hàm gọi Gemini API ====
def call_genai_summary(report_data, stock_code, time_period):
    """Gọi Gemini API để lấy tóm tắt."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("Vui lòng cung cấp GEMINI_API_KEY trong file .env")
        return "Lỗi: Chưa cấu hình API Key."
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    prompt = f"""
    Hãy tóm tắt ngắn gọn, chuyên nghiệp về mã cổ phiếu {stock_code} trong giai đoạn {time_period[0]} đến {time_period[1]} dựa trên dữ liệu JSON sau:
    {json.dumps(report_data, ensure_ascii=False, indent=2)}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Lỗi khi gọi Gemini API: {e}"