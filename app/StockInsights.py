import streamlit as st
from auth import (
    verify_firebase_token,
    register_user_to_mongo,
    get_user_profile,
)
from utils import initialize_firebase, load_css

# ==== Cấu hình trang và tải CSS ====
st.set_page_config(page_title="Đăng nhập - Stock Insights", page_icon="🔮", layout="centered")
load_css()
auth_fb = initialize_firebase()

# Define the pages
#login = st.Page("StockInsights.py", title="Đăng nhập")
report = st.Page("pages/1_Báo_cáo.py", title="Báo cáo", icon="📊")
history = st.Page("pages/3_Lịch_sử.py", title="Lịch sử", icon="📜")
accounts = st.Page("pages/2_Tài_khoản.py", title="Tài khoản", icon="⚙", default=True)

# ==== Giao diện Đăng nhập / Đăng ký ====
if "uid" not in st.session_state:
    st.markdown('<div class="not-logged-in">', unsafe_allow_html=True)
    st.markdown("<h1>Stock Insights 🔮</h1>", unsafe_allow_html=True)
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
                        st.rerun()
                except Exception as e:
                    st.error("Sai email hoặc mật khẩu!")

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
                        else:
                            st.error("Không thể đăng ký. Vui lòng thử lại.")
    st.markdown('</div>', unsafe_allow_html=True)
    
elif "uid" in st.session_state:
    # Nếu đã đăng nhập, chào mừng và hướng dẫn
    pg = st.navigation(
        [report, history, accounts],
        position="top"
    )
    pg.run()

    # st.markdown("<h1>Chào mừng trở lại!</h1>", unsafe_allow_html=True)
    # st.info("Sử dụng thanh điều hướng bên trái để truy cập các tính năng. 👈")
    # st.balloons()
