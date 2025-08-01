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

st.set_page_config(page_title="Stock Insights", page_icon="📈", layout="centered")
st.markdown(
    "<h1 style='text-align: center; color: #3949ab; margin-bottom:0'>Stock Insights 🔒</h1>",
    unsafe_allow_html=True,
)


def render_avatar(uid):
    avatar_bytes = get_avatar_blob(uid)
    avatar_html = ""
    if avatar_bytes:
        img_base64 = base64.b64encode(avatar_bytes).decode()
        avatar_html = f"""
            <div style='display:flex; flex-direction:column; align-items:center;'>
                <img src="data:image/png;base64,{img_base64}"
                     style="border-radius:50%;border:4px solid #5e72e4;width:120px;height:120px;object-fit:cover;box-shadow:0 4px 12px #0001;">
            </div>
        """
    else:
        avatar_html = """
            <div style='display:flex; flex-direction:column; align-items:center;'>
                <div style='border-radius:50%; background:linear-gradient(135deg,#80d0c7,#0093e9);
                    width:120px;height:120px;display:flex;align-items:center;justify-content:center;
                    box-shadow:0 4px 12px #0001;'>
                    <span style='font-size:3em;color:#fff;'>👤</span>
                </div>
                <div style='margin-top:8px; color:gray; font-size:0.97em;'>Chưa có avatar</div>
            </div>
        """
    st.markdown(avatar_html, unsafe_allow_html=True)


# ----------- AUTH UI ----------
if "uid" not in st.session_state:
    tab = st.radio("Bạn đã có tài khoản chưa?", ("Đăng nhập", "Đăng ký"))
    email = st.text_input("Email", key="email")
    password = st.text_input("Mật khẩu", type="password", key="password")
    if tab == "Đăng ký":
        user_name = st.text_input("Tên người dùng", key="user_name")
        password_confirm = st.text_input(
            "Nhập lại mật khẩu", type="password", key="password2"
        )

    if st.button(tab, use_container_width=True):
        if (
            not email
            or not password
            or (tab == "Đăng ký" and (not password_confirm or not user_name))
        ):
            st.warning("Vui lòng nhập đầy đủ thông tin.")
        elif tab == "Đăng ký" and password != password_confirm:
            st.warning("Mật khẩu không khớp.")
        else:
            try:
                if tab == "Đăng nhập":
                    try:
                        user = auth_fb.sign_in_with_email_and_password(email, password)
                        id_token = user["idToken"]
                        info = verify_firebase_token(id_token)
                        if info:
                            st.session_state["uid"] = info["uid"]
                            st.session_state["user_email"] = info.get("email", "")
                            # Lấy user profile từ Mongo
                            profile = get_user_profile(info["uid"])
                            st.session_state["user_name"] = (
                                profile.get("user_name", "") if profile else ""
                            )
                            st.success(
                                f"Đăng nhập thành công! Xin chào {st.session_state['user_email']}."
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Token không hợp lệ hoặc tài khoản chưa xác thực email."
                            )
                    except Exception as e:
                        err = str(e)
                        if "EMAIL_NOT_FOUND" in err or "INVALID_PASSWORD" in err:
                            st.error("Sai email hoặc mật khẩu!")
                        else:
                            st.error("Không thể đăng nhập. Vui lòng thử lại.")
                else:  # Đăng ký
                    try:
                        reg = auth_fb.create_user_with_email_and_password(
                            email, password
                        )
                        # Lưu thêm user_name vào MongoDB
                        register_user_to_mongo(reg["localId"], email, user_name)
                        st.success("Đăng ký thành công! Hãy đăng nhập lại.")
                    except Exception as e:
                        err = str(e)
                        if "EMAIL_EXISTS" in err:
                            st.error("Email đã tồn tại!")
                        elif "WEAK_PASSWORD" in err:
                            st.error("Mật khẩu phải ít nhất 6 ký tự!")
                        else:
                            st.error("Không thể đăng ký. Vui lòng thử lại.")
            except Exception:
                st.error("Có lỗi xảy ra, vui lòng thử lại.")
else:
    # ==== PROFILE VIEW ====
    profile = get_user_profile(st.session_state["uid"])
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='display:flex;flex-direction:column;align-items:center;'>"
        f"<div style='font-size:1.3em;margin-bottom:8px;'><b>{profile.get('user_name','')}</b></div>"
        f"<div style='color:gray;font-size:1em;margin-bottom:4px'>{st.session_state['user_email']}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    # Avatar hiển thị ngay sau user name
    render_avatar(st.session_state["uid"])
    st.markdown("<br>", unsafe_allow_html=True)

    # --- AVATAR UPLOAD ---
    with st.expander("Thay đổi ảnh đại diện", expanded=True):
        file = st.file_uploader(
            "Chọn ảnh (png, jpg, jpeg)", type=["png", "jpg", "jpeg"]
        )
        if st.button("Lưu avatar", use_container_width=True):
            if file:
                save_avatar(st.session_state["uid"], file.read())
                st.success("Đã lưu avatar! Tải lại trang để thấy thay đổi.")
            else:
                st.warning("Hãy chọn ảnh trước khi lưu.")

    # --- CẬP NHẬT USERNAME (nếu muốn) ---
    with st.expander("Đổi tên người dùng"):
        new_username = st.text_input(
            "Tên người dùng mới",
            value=profile.get("user_name", ""),
            key="edit_username",
        )
        if st.button("Lưu tên mới"):
            update_username_in_mongo(st.session_state["uid"], new_username)
            st.success("Đã cập nhật tên người dùng! Tải lại trang để xem.")

    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.clear()
        st.rerun()
