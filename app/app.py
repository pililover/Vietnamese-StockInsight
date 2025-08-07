import io
import streamlit as st
import pyrebase
from auth import (
    verify_firebase_token,
    register_user_to_mongo,
    save_avatar,
    get_avatar_blob,
    get_user_profile,
    update_username_in_mongo,
)
import base64

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

    /* === Card styling with "frosted glass" effect === */
    div[data-testid="stTabs-panel"], .profile-container {
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
    
    /* === Profile card specific styling === */
    .profile-container {
        text-align: center;
    }
    .profile-container h3 {
        color: #ffffff;
    }
    .profile-container p {
        color: #94a3b8;
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
        st.markdown("<br>", unsafe_allow_html=True)
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
        user_name_reg = st.text_input("Tên người dùng", key="user_name_reg", placeholder="Nguyen Van A")
        email_reg = st.text_input("Email", key="email_reg", placeholder="you@example.com")
        password_reg = st.text_input("Mật khẩu", type="password", key="password_reg", placeholder="••••••••")
        password_confirm_reg = st.text_input("Nhập lại mật khẩu", type="password", key="password_confirm_reg", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Đăng ký", key="register_btn", use_container_width=True):
            if not email_reg or not password_reg or not password_confirm_reg or not user_name_reg:
                st.warning("Vui lòng nhập đầy đủ thông tin.")
            elif password_reg != password_confirm_reg:
                st.warning("Mật khẩu không khớp.")
            else:
                try:
                    reg = auth_fb.create_user_with_email_and_password(email_reg, password_reg)
                    register_user_to_mongo(reg["localId"], email_reg, user_name_reg)
                    st.success("Đăng ký thành công! Vui lòng chuyển qua tab Đăng nhập để vào tài khoản.")
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
    with st.container():
        st.markdown("<div class='profile-container'>", unsafe_allow_html=True)
        profile = get_user_profile(st.session_state["uid"])
        
        render_avatar(st.session_state["uid"])

        st.markdown(f"<h3 style='margin-bottom:0.5rem;'>{profile.get('user_name', '')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8; margin-bottom: 2rem;'>{st.session_state['user_email']}</p>", unsafe_allow_html=True)

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

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Đăng xuất", use_container_width=True, key="logout_btn"):
            st.session_state.clear()
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)
