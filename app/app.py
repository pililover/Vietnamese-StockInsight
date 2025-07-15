import io
import hashlib
import os

import streamlit as st
from dotenv import load_dotenv, find_dotenv

from auth import register_user, login_user, save_avatar, get_avatar_blob

# --- Khởi động ---
load_dotenv(find_dotenv())
st.set_page_config(page_title="Stock Insights", layout="centered")

# Khởi tạo session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.auth_message = ""
    st.session_state.last_avatar = None
    st.session_state.show_upload = False


# Hàm hiển thị form đăng nhập/đăng ký
def show_auth_form():
    st.title("🔐 Đăng nhập / Đăng ký")
    mode = st.radio("Chế độ", ["Đăng nhập", "Đăng ký"], key="auth_mode")
    user = st.text_input("Tên người dùng", key="auth_user")
    pwd = st.text_input("Mật khẩu", type="password", key="auth_pwd")

    if st.button("Xác nhận", key="auth_submit"):
        if not user or not pwd:
            st.session_state.auth_message = "❌ Vui lòng nhập đủ thông tin."
        else:
            hashed_pwd = hashlib.sha256(pwd.encode()).hexdigest()
            if mode == "Đăng ký":
                if register_user(user, hashed_pwd):
                    st.session_state.auth_message = (
                        "✅ Đăng ký thành công! Mời đăng nhập."
                    )
                else:
                    st.session_state.auth_message = "❌ Tên đã tồn tại."
            else:
                if login_user(user, hashed_pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.auth_message = ""
                    st.rerun()
                else:
                    st.session_state.auth_message = "❌ Sai tên hoặc mật khẩu."

    if st.session_state.auth_message:
        st.info(st.session_state.auth_message)


# Hàm hiển thị dashboard
def show_dashboard():
    user = st.session_state.username
    st.title(f"🎉 Chào mừng, {user}!")
    st.markdown("---")

    # Hiển thị avatar
    img = st.session_state.last_avatar or get_avatar_blob(user)
    if img:
        st.image(io.BytesIO(img), width=150, caption="Avatar")
    else:
        st.info("Bạn chưa có avatar.")

    # Nút "Change Photo" bên dưới avatar
    if st.button("Change Photo", key="change_photo_button"):
        st.session_state.show_upload = True

    # Hiển thị các nút "Chọn tệp" và "Upload ảnh" khi nhấp "Change Photo"
    if st.session_state.show_upload:
        st.markdown("---")
        file = st.file_uploader(
            "Chọn tệp (PNG/JPG)", type=["png", "jpg", "jpeg"], key="upload_file"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Upload ảnh", key="upload_submit"):
                if file is None:
                    st.warning("❌ Vui lòng chọn tệp.")
                else:
                    data = file.read()
                    save_avatar(user, data)
                    st.session_state.last_avatar = data
                    st.success("✅ Upload thành công!")
                    st.session_state.show_upload = False
                    st.rerun()
        with col2:
            if st.button("Hủy", key="cancel_upload"):
                st.session_state.show_upload = False
                st.rerun()

    st.markdown("---")
    if st.button("🔓 Đăng xuất", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.auth_message = ""
        st.session_state.last_avatar = None
        st.session_state.show_upload = False
        st.rerun()


# Logic chính
if not st.session_state.logged_in:
    show_auth_form()
else:
    show_dashboard()
