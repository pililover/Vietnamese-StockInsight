import streamlit as st
from utils import initialize_firebase, load_css
from auth import (
    verify_firebase_token,
    register_user_to_mongo,
    get_user_profile,
)

# ==== Cấu hình trang và tải CSS ====
st.set_page_config(page_title="Đăng nhập - Stock Insights", page_icon="🔮", layout="centered")

auth_fb = initialize_firebase()

# Khởi tạo page mặc định
if "page" not in st.session_state:
    st.session_state.page = "report"

# ==== Giao diện Đăng nhập / Đăng ký ====
if "uid" not in st.session_state:
    # Set layout về centered cho trang đăng nhập
    
    st.markdown("<h1>Stock Insights 🔮</h1>", unsafe_allow_html=True)
    st.markdown("<p class='auth-subheader'>Chào mừng! Vui lòng đăng nhập hoặc đăng ký.</p>", unsafe_allow_html=True)
    load_css()

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
                # ... (Giữ nguyên logic đăng ký) ...
                st.success("Đăng ký thành công! Giờ bạn có thể đăng nhập.")

# ==== Giao diện chính sau khi đăng nhập ====
else:
    # --- Thanh điều hướng tùy chỉnh ---
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Sử dụng st.columns để đặt các nút cạnh nhau
    col1, col2, col3 = st.columns(3)
    
    with col1:
        is_active = st.session_state.page == "report"
        if st.button("📊 Báo cáo", use_container_width=True, key="nav_report"):
            st.session_state.page = "report"
            # Reset trạng thái báo cáo cũ
            st.session_state.pop("selected_report", None)
            st.session_state["show_form"] = True
        if is_active:
            st.markdown('<style>button[data-testid="stButton-nav_report"] {border-color: #30cfd0; color: #ffffff; box-shadow: 0 0 15px rgba(48, 207, 208, 0.4);}</style>', unsafe_allow_html=True)

    with col2:
        is_active = st.session_state.page == "history"
        st.button("📜 Lịch sử", use_container_width=True, on_click=lambda: st.session_state.update(page="history"), 
                  type="secondary" if not is_active else "primary",
                  key="nav_history")
        if is_active:
            st.markdown('<style>button[data-testid="stButton-nav_history"] {border-color: #30cfd0; color: #ffffff; box-shadow: 0 0 15px rgba(48, 207, 208, 0.4);}</style>', unsafe_allow_html=True)

    with col3:
        is_active = st.session_state.page == "account"
        st.button("⚙️ Tài khoản", use_container_width=True, on_click=lambda: st.session_state.update(page="account"), 
                  type="secondary" if not is_active else "primary",
                  key="nav_account")
        if is_active:
            st.markdown('<style>button[data-testid="stButton-nav_account"] {border-color: #30cfd0; color: #ffffff; box-shadow: 0 0 15px rgba(48, 207, 208, 0.4);}</style>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- Hiển thị nội dung trang tương ứng ---
    if st.session_state.page == "report":
        from pages.page_report import main as report_main
        report_main()
    elif st.session_state.page == "history":
        from pages.page_history import main as history_main
        history_main()
    elif st.session_state.page == "account":
        from pages.page_account import main as account_main
        account_main()
