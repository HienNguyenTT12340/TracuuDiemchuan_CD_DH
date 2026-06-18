import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CẤU HÌNH TRANG WEB GIAO DIỆN
# ==========================================
st.set_page_config(
    page_title="Cổng Tra cứu Điểm chuẩn Đại học Toàn quốc",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# 2. HÀM ĐỌC VÀ ĐỊNH VỊ CỘT CHUẨN XÁC THEO FILE THẬT
# ==========================================
@st.cache_data
def load_and_map_columns():
    try:
        # Đọc dữ liệu thô đầu vào
        df_raw = pd.read_csv("diem_chuan_toan_quoc.csv", encoding="utf-8-sig", on_bad_lines='skip')
    except Exception:
        try:
            df_raw = pd.read_csv("diem_chuan_toan_quoc.csv", encoding="utf-8", on_bad_lines='skip', engine='python')
        except Exception as e:
            st.error(f"⚠️ Không thể mở file CSV dữ liệu: {e}")
            return pd.DataFrame()

    if df_raw.empty:
        return df_raw

    # Tạo một DataFrame mới sạch sẽ để định vị lại các cột theo đúng cấu trúc thực tế
    df_clean = pd.DataFrame()

    try:
        # Ánh xạ thủ công theo chỉ số vị trí cột để tránh nhầm lẫn dữ liệu lệch hàng
        df_clean["Trường"] = df_raw.iloc[:, 0].astype(str).str.strip()
        df_clean["Mã Trường"] = df_raw.iloc[:, 1].astype(str).str.strip()
        
        # Đồng bộ cột Khối: Ép về dạng chuỗi (String) để loại bỏ hoàn toàn các lỗi hỗn hợp kiểu dữ liệu
        df_clean["Khối"] = df_raw.iloc[:, 2].astype(str).str.strip().fillna("Chưa rõ")
        
        # Định vị cột Điểm số và xử lý số thực sạch
        df_clean["Điểm chuẩn"] = pd.to_numeric(df_raw.iloc[:, 3], errors='coerce').fillna(0.0)
        
        # Định vị cột Năm học
        df_clean["Năm"] = pd.to_numeric(df_raw.iloc[:, 4], errors='coerce').fillna(2025).astype(int)
        
        # Xử lý cột Ngành nếu có dữ liệu phụ kèm theo
        if df_raw.shape[1] >= 6:
            df_clean["Ngành"] = df_raw.iloc[:, 5].astype(str).str.strip()
        else:
            df_clean["Ngành"] = "Thông tin chung"
            
    except Exception as e:
        st.error(f"⚠️ Lỗi định vị cấu trúc hàng/cột: {e}")
        return df_raw

    # Loại bỏ các dòng trống không hợp lệ
    df_clean = df_clean.dropna(subset=["Trường"])
    return df_clean

df = load_and_map_columns()

# ==========================================
# 3. GIAO DIỆN HIỂN THỊ VÀ BỘ LỌC ĐA NHIỆM
# ==========================================
st.title("🎓 Hệ thống Tra cứu Điểm chuẩn Đại học Toàn quốc")
st.caption("Phiên bản cập nhật - Đã vá lỗi TypeError sắp xếp dữ liệu trống thành công")

if not df.empty:
    st.sidebar.header("🔍 Bộ lọc Tìm kiếm")
    
    # 1. Ô tìm kiếm tự do theo từ khóa
    search_keyword = st.sidebar.text_input(
        "Tìm nhanh theo tên Trường / từ khóa:", 
        placeholder="Ví dụ: Kinh tế Quốc dân, Bách Khoa..."
    ).strip()

    filtered_df = df.copy()
    if search_keyword:
        kw = search_keyword.lower()
        filtered_df = filtered_df[
            filtered_df["Trường"].str.lower().str.contains(kw, na=False) |
            filtered_df["Khối"].str.lower().str.contains(kw, na=False)
        ]

    # 2. Bộ lọc chọn Trường Đại học
    all_schools = sorted([str(s) for s in filtered_df["Trường"].unique() if str(s).strip() != ""])
    selected_school = st.sidebar.selectbox("Chọn Trường Đại học:", ["Tất cả"] + all_schools)
    if selected_school != "Tất cả":
        filtered_df = filtered_df[filtered_df["Trường"] == selected_school]

    # 3. Bộ lọc chọn khối thi (VÁ LỖI TYPEERROR: Chuyển đổi an toàn danh sách sang chuỗi)
    all_blocks = sorted([str(b) for b in filtered_df["Khối"].unique() if str(b).strip() != "" and str(b) != "nan"])
    selected_block = st.sidebar.selectbox("Chọn Tổ hợp môn (Khối):", ["Tất cả"] + all_blocks)
    if selected_block != "Tất cả":
        filtered_df = filtered_df[filtered_df["Khối"] == selected_block]

    # 4. Thanh trượt chọn khoảng Năm xét tuyển
    years = sorted(df["Năm"].unique())
    if len(years) > 1:
        min_y, max_y = int(min(years)), int(max(years))
        year_range = st.sidebar.slider("Chọn giai đoạn năm:", min_y, max_y, (min_y, max_y))
        filtered_df = filtered_df[(filtered_df["Năm"] >= year_range[0]) & (filtered_df["Năm"] <= year_range[1])]

    # ==========================================
    # 4. KHU VỰC HIỂN THỊ KẾT QUẢ VÀ THỐNG KÊ
    # ==========================================
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Bảng số liệu chi tiết")
        if not filtered_df.empty:
            display_df = filtered_df.sort_values(by=["Năm", "Điểm chuẩn"], ascending=[False, False])
            cols_to_show = ["Trường", "Mã Trường", "Khối", "Năm", "Điểm chuẩn"]
            st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Không tìm thấy kết quả trùng khớp. Hãy thử xóa bớt từ khóa tìm kiếm.")

    with col2:
        st.subheader("📊 Số liệu thống kê nhanh")
        if not filtered_df.empty:
            st.metric(label="Tổng số nguyện vọng / ngành tìm thấy", value=f"{len(filtered_df):,}")
            st.metric(label="Điểm chuẩn cao nhất trong bộ lọc", value=f"{filtered_df['Điểm chuẩn'].max():.2f}")
            st.metric(label="Điểm chuẩn thấp nhất trong bộ lọc", value=f"{filtered_df['Điểm chuẩn'].min():.2f}")
        else:
            st.write("Chưa có dữ liệu thống kê.")

    # --- BIỂU ĐỒ XU HƯỚNG ---
    st.markdown("---")
    st.subheader("📈 Biểu đồ Xu hướng Biến động Điểm chuẩn")
    if not filtered_df.empty and len(filtered_df["Năm"].unique()) > 1:
        fig = px.line(
            filtered_df, 
            x="Năm", 
            y="Điểm chuẩn", 
            color="Khối", 
            markers=True,
            title="Biến động điểm số theo khối xét tuyển"
        )
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Mẹo nhỏ: Hãy chọn một Trường cụ thể ở thanh công cụ bên trái để theo dõi biểu đồ đường biến động điểm qua các năm rõ ràng nhất.")
else:
    st.info("Trang web đang đợi nạp tệp cơ sở dữ liệu đầu vào `diem_chuan_toan_quoc.csv`.")
