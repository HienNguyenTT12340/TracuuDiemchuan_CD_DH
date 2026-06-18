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
# 2. HÀM TỰ ĐỘNG CHUẨN HÓA VÀ ĐỊNH VỊ CỘT CHÍNH XÁC
# ==========================================
@st.cache_data
def load_and_fix_columns():
    try:
        # Đọc file CSV
        df = pd.read_csv("diem_chuan_toan_quoc.csv", encoding="utf-8-sig", on_bad_lines='skip')
    except Exception:
        try:
            df = pd.read_csv("diem_chuan_toan_quoc.csv", encoding="utf-8", on_bad_lines='skip', engine='python')
        except Exception as e:
            st.error(f"⚠️ Không thể đọc file CSV dữ liệu: {e}")
            return pd.DataFrame()

    if df.empty:
        return df

    # --- THUẬT TOÁN ĐỊNH VỊ CỘT THÔNG MINH (CHỐNG NHẦM CỘT) ---
    col_mapping = {}
    for col in df.columns:
        col_lower = str(col).lower().strip()
        
        # Nhận diện cột Trường
        if "trường" in col_lower or "truong" in col_lower or "đại học" in col_lower:
            col_mapping["Trường"] = col
        # Nhận diện cột Ngành
        elif "ngành" in col_lower or "nganh" in col_lower or "tên ngành" in col_lower:
            col_mapping["Ngành"] = col
        # Nhận diện cột Năm
        elif "năm" in col_lower or "nam" in col_lower:
            col_mapping["Năm"] = col
        # Nhận diện cột Điểm chuẩn
        elif "điểm" in col_lower or "diem" in col_lower or "chuẩn" in col_lower:
            col_mapping["Điểm chuẩn"] = col
        # Nhận diện cột Khối / Tổ hợp
        elif "khối" in col_lower or "khoi" in col_lower or "tổ hợp" in col_lower or "to hop" in col_lower:
            col_mapping["Khối"] = col

    # Đổi tên các cột tìm được về tên chuẩn chuẩn của hệ thống
    df = df.rename(columns={v: k for k, v in col_mapping.items()})

    # Đảm bảo các cột tối thiểu phải có, nếu thiếu thì tự tạo cột rỗng tránh crash
    required_cols = ["Trường", "Ngành", "Năm", "Điểm chuẩn", "Khối"]
    for c in required_cols:
        if c not in df.columns:
            df[c] = "Chưa rõ" if c != "Điểm chuẩn" and c != "Năm" else 0

    # Chuẩn hóa kiểu dữ liệu số
    df["Năm"] = pd.to_numeric(df["Năm"], errors='coerce').fillna(2024).astype(int)
    df["Điểm chuẩn"] = pd.to_numeric(df["Điểm chuẩn"], errors='coerce').fillna(0.0)
    
    # Loại bỏ khoảng trắng thừa ở dữ liệu chữ
    for c in ["Trường", "Ngành", "Khối"]:
        df[c] = df[c].astype(str).str.strip()

    return df

df = load_and_fix_columns()

# ==========================================
# 3. GIAO DIỆN HIỂN THỊ VÀ BỘ LỌC ĐA NHIỆM
# ==========================================
st.title("🎓 Hệ thống Tra cứu Điểm chuẩn Đại học Toàn quốc")
st.caption("Hệ thống tự động đồng bộ và sửa lỗi nhầm cột dữ liệu từ file CSV của bạn")

if not df.empty:
    st.sidebar.header("🔍 Bộ lọc Tìm kiếm")
    
    # 1. Ô tìm kiếm tự do theo từ khóa
    search_keyword = st.sidebar.text_input(
        "Tìm nhanh theo tên Trường / tên Ngành:", 
        placeholder="Ví dụ: Bách Khoa, CNTT, Kinh tế..."
    ).strip()

    # Bắt đầu lọc dữ liệu dựa trên từ khóa tìm kiếm trước để thu hẹp dropdown thông minh
    filtered_df = df.copy()
    if search_keyword:
        kw = search_keyword.lower()
        filtered_df = filtered_df[
            filtered_df["Trường"].str.lower().str.contains(kw, na=False) |
            filtered_df["Ngành"].str.lower().str.contains(kw, na=False)
        ]

    # 2. Bộ lọc chọn Trường (Tự cập nhật danh sách theo kết quả tìm kiếm)
    all_schools = sorted(filtered_df["Trường"].unique())
    selected_school = st.sidebar.selectbox("Chọn Trường Đại học:", ["Tất cả"] + all_schools)
    if selected_school != "Tất cả":
        filtered_df = filtered_df[filtered_df["Trường"] == selected_school]

    # 3. Bộ lọc chọn Ngành (Tự động cập nhật để không bị triệt tiêu dữ liệu)
    all_majors = sorted(filtered_df["Ngành"].unique())
    selected_major = st.sidebar.selectbox("Chọn Ngành học cụ thể:", ["Tất cả"] + all_majors)
    if selected_major != "Tất cả":
        filtered_df = filtered_df[filtered_df["Ngành"] == selected_major]

    # 4. Bộ lọc chọn khối thi (A00, B00, C00...)
    all_blocks = sorted(filtered_df["Khối"].unique())
    if len(all_blocks) > 1:
        selected_block = st.sidebar.selectbox("Chọn Tổ hợp môn (Khối):", ["Tất cả"] + all_blocks)
        if selected_block != "Tất cả":
            filtered_df = filtered_df[filtered_df["Khối"] == selected_block]

    # 5. Thanh trượt chọn Năm
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
            # Sắp xếp hiển thị năm mới nhất lên trên đầu
            display_df = filtered_df.sort_values(by=["Năm", "Điểm chuẩn"], ascending=[False, False])
            
            # Chỉ hiển thị các cột quan trọng theo đúng thứ tự thẩm mỹ
            cols_to_show = [c for c in ["Trường", "Ngành", "Khối", "Năm", "Điểm chuẩn"] if c in display_df.columns]
            st.dataframe(display_df[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Không tìm thấy kết quả nào trùng khớp. Hãy thử xóa từ khóa hoặc chọn lại 'Tất cả' ở các bộ lọc.")

    with col2:
        st.subheader("📊 Số liệu thống kê nhanh")
        if not filtered_df.empty:
            st.metric(label="Tổng số nguyện vọng / ngành tìm thấy", value=f"{len(filtered_df):,}")
            st.metric(label="Điểm chuẩn cao nhất", value=f"{filtered_df['Điểm chuẩn'].max():.2f}")
            st.metric(label="Điểm chuẩn thấp nhất", value=f"{filtered_df['Điểm chuẩn'].min():.2f}")
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
            color="Ngành", 
            markers=True,
            title="Biến động điểm số qua các mùa tuyển sinh"
        )
        fig.update_layout(xaxis_type='category')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 Mẹo nhỏ: Chọn một Trường hoặc một Ngành cụ thể ở thanh công cụ bên trái để xem biểu đồ đường xu hướng biến động điểm qua các năm rõ ràng nhất.")
else:
    st.info("Trang web đang đợi nạp tệp cơ sở dữ liệu đầu vào `diem_chuan_toan_quoc.csv`.")
