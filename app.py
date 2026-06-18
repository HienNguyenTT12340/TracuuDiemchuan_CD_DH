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
# 2. HÀM ĐỌC VÀ CHUẨN HÓA DỮ LIỆU THẬT
# ==========================================
@st.cache_data
def load_data():
    try:
        # Đọc dữ liệu từ file CSV kèm bộ giải mã tiếng Việt và bỏ qua dòng lệch cột
        df = pd.read_csv(
            "diem_chuan_toan_quoc.csv", 
            encoding="utf-8-sig", 
            on_bad_lines='skip'
        )
        
        # Ép kiểu dữ liệu Năm và Điểm chuẩn về dạng số để vẽ biểu đồ không bị lỗi
        if "Năm" in df.columns:
            df["Năm"] = df["Năm"].astype(int)
        if "Điểm chuẩn" in df.columns:
            df["Điểm chuẩn"] = pd.to_numeric(df["Điểm chuẩn"], errors='coerce').fillna(0.0)
        return df
        
    except Exception as e:
        # Cơ chế dự phòng nâng cao sử dụng Python engine tự quét cấu trúc file
        try:
            df = pd.read_csv(
                "diem_chuan_toan_quoc.csv", 
                encoding="utf-8", 
                on_bad_lines='skip', 
                engine='python'
            )
            return df
        except Exception as inner_error:
            st.error(f"⚠️ Hệ thống không thể đọc file dữ liệu. Vui lòng kiểm tra định dạng CSV: {inner_error}")
            return pd.DataFrame(columns=["Trường", "Mã Trường", "Ngành", "Khối", "Năm", "Điểm chuẩn"])

# Gọi hàm nạp dữ liệu vào hệ thống
df = load_data()

# ==========================================
# 3. GIAO DIỆN HIỂN THỊ CHÍNH
# ==========================================
st.title("🎓 Hệ thống Tra cứu Điểm chuẩn Đại học Toàn quốc")
st.caption("Dữ liệu thực tế được tổng hợp qua các năm - Tự động cập nhật xu hướng biến động điểm số")

if not df.empty:
    # --- THANH BỘ LỌC SIDEBAR THÔNG MINH ---
    st.sidebar.header("🔍 Bộ lọc Tìm kiếm")
    
    # 1. Ô tìm kiếm tự do (Cực kỳ hữu ích khi file có hàng vạn dòng của 300 trường)
    search_keyword = st.sidebar.text_input(
        "Tìm nhanh theo tên Trường / tên Ngành:", 
        placeholder="Ví dụ: Bách Khoa, Kinh tế, CNTT..."
    )

    # 2. Bộ lọc Dropdown chọn Trường (Tự động nhận diện từ file CSV)
    all_schools = sorted(df["Trường"].dropna().unique())
    selected_school = st.sidebar.selectbox("Chọn Trường Đại học cụ thể:", ["Tất cả"] + all_schools)

    # 3. Bộ lọc Dropdown chọn Ngành (Tự động nhận diện từ file CSV)
    all_majors = sorted(df["Ngành"].dropna().unique())
    selected_major = st.sidebar.selectbox("Chọn Ngành học cụ thể:", ["Tất cả"] + all_majors)

    # 4. Bộ lọc Thanh trượt chọn khoảng Năm xét tuyển
    years = sorted(df["Năm"].dropna().unique())
    if len(years) > 1:
        min_year, max_year = int(min(years)), int(max(years))
        year_range = st.sidebar.slider("Chọn giai đoạn năm:", min_year, max_year, (min_year, max_year))
    else:
        year_range = (int(years[0]), int(years[0])) if years else (2017, 2026)

    # --- TIẾN HÀNH LỌC DỮ LIỆU ---
    filtered_df = df.copy()
    
    # Ưu tiên lọc theo từ khóa gõ tay trước nếu người dùng có nhập
    if search_keyword:
        filtered_df = filtered_df[
            filtered_df["Trường"].str.contains(search_keyword, case=False, na=False) |
            filtered_df["Ngành"].str.contains(search_keyword, case=False, na=False)
        ]
        
    # Lọc tiếp theo các ô chọn Dropdown
    if selected_school != "Tất cả":
        filtered_df = filtered_df[filtered_df["Trường"] == selected_school]
    if selected_major != "Tất cả":
        filtered_df = filtered_df[filtered_df["Ngành"] == selected_major]
        
    # Lọc giới hạn theo khoảng năm người dùng kéo thanh trượt
    filtered_df = filtered_df[(filtered_df["Năm"] >= year_range[0]) & (filtered_df["Năm"] <= year_range[1])]

    # --- KHU VỰC HIỂN THỊ KẾT QUẢ VÀ THỐNG KÊ ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Bảng số liệu chi tiết")
        if not filtered_df.empty:
            # Sắp xếp hiển thị từ mùa tuyển sinh mới nhất trở về trước
            display_df = filtered_df.sort_values(by=["Năm", "Điểm chuẩn"], ascending=[False, False])
            
            # ĐÃ SỬA LỖI: Thay thế index=False bằng hide_index=True để không bị crash ứng dụng
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Không tìm thấy kết quả nào trùng khớp với bộ lọc hiện tại.")

    with col2:
        st.subheader("📊 Số liệu thống kê nhanh")
        if not filtered_df.empty:
            st.metric(label="Tổng số nguyện vọng / ngành tìm thấy", value=f"{len(filtered_df):,}")
            st.metric(label="Điểm chuẩn cao nhất", value=f"{filtered_df['Điểm chuẩn'].max():.2f}")
            st.metric(label="Điểm chuẩn thấp nhất", value=f"{filtered_df['Điểm chuẩn'].min():.2f}")
        else:
            st.write("Chưa có dữ liệu thống kê.")

    # --- BIỂU ĐỒ XU HƯỚNG TRỰC QUAN HÓA (PLOTLY) ---
    st.markdown("---")
    st.subheader("📈 Biểu đồ Xu hướng Biến động Điểm chuẩn")

    # Chỉ vẽ biểu đồ đường nếu dải năm lọc ra lớn hơn 1 để thấy được độ dốc tăng/giảm
    if not filtered_df.empty and len(filtered_df["Năm"].unique()) > 1:
        fig = px.line(
            filtered_df, 
            x="Năm", 
            y="Điểm chuẩn", 
            color="Ngành", 
            line_group="Trường",
            hover_name="Trường",
            markers=True,
            title="Biến động điểm số qua các mùa tuyển sinh"
        )
        # Ép trục X hiển thị dạng danh mục cố định chứ không phải số thập phân chia nhỏ
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Mẹo nhỏ: Để xem biểu đồ xu hướng chính xác và đẹp nhất, bạn hãy chọn một Ngành hoặc một Trường cụ thể ở thanh công cụ bên trái.")
else:
    st.info("Trang web đang đợi nạp tệp cơ sở dữ liệu đầu vào.")
