import streamlit as st

st.set_page_config(page_title="Tài khoản - Stock Insights", page_icon="🔮", layout="centered")

from auth import (
    get_user_profile,
    update_username_in_mongo,
    save_avatar,
    get_avatar_blob,
)
from utils import load_css, render_avatar

load_css()

if "uid" not in st.session_state:
    st.warning("Vui lòng đăng nhập để sử dụng tính năng này.")
    st.page_link("StockInsights.py", label="Về trang Đăng nhập", icon="🏠")
    st.stop()
    

# ==== Giao diện trang tài khoản ====
st.markdown("<h2>Thông tin Tài khoản</h2>", unsafe_allow_html=True)

_, col_center, _ = st.columns([1, 2, 1])

with col_center:
    profile = get_user_profile(st.session_state["uid"])
    
    render_avatar(st.session_state["uid"], st, get_avatar_blob)

    st.html(f"<h3 style='text-align: center; color: #ffffff; margin-bottom: 0.25rem; font-weight: 600;'>{profile.get('user_name', '')}</h3>")
    st.html(f"<p style='text-align: center; color: #94a3b8; margin-bottom: 2rem;'>{st.session_state['user_email']}</p>")

    with st.expander("⚙️ Chỉnh sửa thông tin"):
        new_username = st.text_input("Tên người dùng mới", value=profile.get("user_name", ""), key="edit_username")
        if st.button("Lưu tên mới", use_container_width=True, key="save_name"):
            if new_username:
                update_username_in_mongo(st.session_state["uid"], new_username)
                st.success("Đã cập nhật tên người dùng!")
                st.rerun()
            else:
                st.warning("Tên người dùng không được để trống.")
        
        st.markdown("<hr style='margin: 1rem 0; border-color: rgba(100, 116, 139, 0.3);'>", unsafe_allow_html=True)
        
        file = st.file_uploader("Thay đổi ảnh đại diện (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])
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
        st.switch_page("Stock_Insights.py")
