import streamlit as st
import pandas as pd
import plotly.express as px

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="Cổng Tra cứu Điểm chuẩn Đại học Việt Nam",
    page_icon="🎓",
    layout="wide"
)

# --- HÀM ĐỌC DỮ LIỆU THẬT TỪ FILE CSV ---
@st.cache_data
def load_data():
    try:
        # Sử dụng on_bad_lines='skip' để tự động bỏ qua các dòng lỗi cấu trúc lệch cột
        df = pd.read_csv(
            "diem_chuan_toan_quoc.csv", 
            encoding="utf-8-sig", 
            on_bad_lines='skip'
        )
        
        # Đồng bộ và chuẩn hóa dữ liệu đầu vào để tránh lỗi hiển thị
        if "Năm" in df.columns:
            df["Năm"] = df["Năm"].astype(int)
        if "Điểm chuẩn" in df.columns:
            df["Điểm chuẩn"] = pd.to_numeric(df["Điểm chuẩn"], errors='coerce').fillna(0.0)
        return df
        
    except FileNotFoundError:
        st.error("❌ Không tìm thấy file 'diem_chuan_toan_quoc.csv' trong thư mục. Vui lòng kiểm tra lại!")
        return pd.DataFrame(columns=["Trường", "Mã Trường", "Ngành", "Khối", "Năm", "Điểm chuẩn"])
    except Exception as e:
        # Phương án dự phòng cuối cùng nếu vẫn gặp lỗi phân tách khác
        st.error(f"⚠️ Hệ thống phát hiện lỗi cấu trúc file dữ liệu: {e}")
        return pd.DataFrame(columns=["Trường", "Mã Trường", "Ngành", "Khối", "Năm", "Điểm chuẩn"])

df = load_data()

# --- TIÊU ĐỀ GIAO DIỆN ---
st.title("🎓 Hệ thống Tra cứu Điểm chuẩn Đại học Toàn quốc")
st.caption("Dữ liệu thực tế bóc tách từ năm 2017 đến nay - Tự động cập nhật xu hướng biến động")

if not df.empty:
    # --- THANH BỘ LỌC SIDEBAR ---
    st.sidebar.header("🔍 Bộ lọc Tìm kiếm")
    
    # 1. Ô tìm kiếm nhanh bằng từ khóa (Rất cần thiết khi có tận 300 trường)
    search_keyword = st.sidebar.text_input("Tìm nhanh theo tên Trường / tên Ngành:", placeholder="Ví dụ: Bách Khoa, Kinh tế, CNTT...")

    # 2. Bộ lọc Dropdown chọn Trường
    all_schools = sorted(df["Trường"].dropna().unique())
    selected_school = st.sidebar.selectbox("Chọn Trường cụ thể:", ["Tất cả"] + all_schools)

    # 3. Bộ lọc Dropdown chọn Ngành
    all_majors = sorted(df["Ngành"].dropna().unique())
    selected_major = st.sidebar.selectbox("Chọn Ngành cụ thể:", ["Tất cả"] + all_majors)

    # 4. Bộ lọc Khoảng năm xét tuyển
    years = sorted(df["Năm"].dropna().unique())
    if len(years) > 1:
        min_year, max_year = int(min(years)), int(max(years))
        year_range = st.sidebar.slider("Chọn giai đoạn năm:", min_year, max_year, (min_year, max_year))
    else:
        year_range = (int(years[0]), int(years[0])) if years else (2017, 2026)

    # --- XỬ LÝ LỌC DỮ LIỆU THÔNG MINH ---
    filtered_df = df.copy()
    
    # Ưu tiên lọc theo từ khóa gõ tay trước
    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["Trường"].str.contains(search_keyword, case=False, na=False) |
            filtered_df["Ngành"].str.contains(search_keyword, case=False, na=False)
        ]
        
    # Tiếp tục lọc theo dropdown nếu người dùng chọn cụ thể
    if selected_school != "Tất cả":
        filtered_df = filtered_df[filtered_df["Trường"] == selected_school]
    if selected_major != "Tất cả":
        filtered_df = filtered_df[filtered_df["Ngành"] == selected_major]
        
    filtered_df = filtered_df[(filtered_df["Năm"] >= year_range[0]) & (filtered_df["Năm"] <= year_range[1])]

    # --- HIỂN THỊ KẾT QUẢ TRÊN WEB ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Bảng số liệu chi tiết")
        if not filtered_df.empty:
            # Sắp xếp hiển thị từ năm gần nhất đổ lại
            display_df = filtered_df.sort_values(by=["Năm", "Điểm chuẩn"], ascending=[False, False])
            st.dataframe(display_df, use_container_width=True, index=False)
        else:
            st.warning("Không tìm thấy ngành hoặc trường nào khớp với bộ lọc hiện tại.")

    with col2:
        st.subheader("📊 Số liệu thống kê")
        if not filtered_df.empty:
            st.metric(label="Tổng số dòng tìm thấy", value=len(filtered_df))
            st.metric(label="Điểm chuẩn cao nhất", value=f"{filtered_df['Điểm chuẩn'].max():.2f}")
            st.metric(label="Điểm chuẩn thấp nhất", value=f"{filtered_df['Điểm chuẩn'].min():.2f}")
        else:
            st.write("Chưa có dữ liệu.")

    # --- ĐỒ THỊ TRỰC QUAN HÓA ---
    st.markdown("---")
    st.subheader("📈 Biểu đồ Xu hướng Biến động Điểm số")

    if not filtered_df.empty and len(filtered_df["Năm"].unique()) > 1:
        fig = px.line(
            filtered_df, 
            x="Năm", 
            y="Điểm chuẩn", 
            color="Ngành", 
            line_group="Trường",
            hover_name="Trường",
            markers=True,
            title="Đường xu hướng điểm chuẩn qua các năm"
        )
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Mẹo tra cứu: Để xem biểu đồ đường rõ nhất, bạn nên chọn cụ thể 1 Ngành hoặc 1 Trường ở thanh bên trái.")
