import hashlib
import os

import streamlit as st
from dotenv import load_dotenv, find_dotenv
from auth import register_user, login_user

# Load .env từ thư mục gốc
load_dotenv(find_dotenv())

st.title("Stock Insights !!!")

menu = st.sidebar.selectbox("Chọn chức năng", ["Đăng ký", "Đăng nhập"])
username = st.text_input("Tên người dùng")
password = st.text_input("Mật khẩu", type="password")

# Hash mật khẩu
password_hash = hashlib.sha256(password.encode()).hexdigest()

if menu == "Đăng ký":
    if st.button("Đăng ký"):
        if username and password:
            ok = register_user(username, password_hash)
            if ok:
                st.success("Đăng ký thành công!")
            else:
                st.error("Tên người dùng đã tồn tại.")
        else:
            st.warning("Vui lòng nhập đủ thông tin.")
else:
    if st.button("Đăng nhập"):
        if username and password:
            valid = login_user(username, password_hash)
            if valid:
                st.success(f"Chào mừng, {username}!")
            else:
                st.error("Sai tên hoặc mật khẩu.")
        else:
            st.warning("Vui lòng nhập đủ thông tin.")
