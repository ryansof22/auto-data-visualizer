import streamlit as st
import pandas as pd
from src.data_loader import load_data
from src.column_mapper import categorize_columns, get_standard_mapping

# Coba impor fungsi opsional dari column_mapper dan visualizer — jika tidak ada, gunakan fallback None
try:
    from src.column_mapper import filter_regional_hierarchy
except Exception as e:
    filter_regional_hierarchy = None
    try:
        st.warning(f"Optional function 'filter_regional_hierarchy' tidak tersedia: {e}")
    except Exception:
        pass

try:
    from src.visualizer import render_kpi_cards, render_primary_charts, render_category_kpis, render_data_table
except Exception:
    # render_category_kpis mungkin belum ada di visualizer; impor fungsi yang pasti ada dan set fallback
    from src.visualizer import render_kpi_cards, render_primary_charts, render_data_table
    render_category_kpis = None

st.set_page_config(
    page_title="Automated Data Visualizer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Automated Enterprise Data Visualizer")
st.markdown("Unggah berkas Excel/CSV (BPS, Pemkab, Laporan Penjualan) untuk menghasilkan dashboard visualisasi otomatis terstruktur.")

st.sidebar.header("📁 Ingesti Data")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel atau CSV",
    type=["xlsx", "xls", "csv"]
)

# Checkbox debug dan opsi filter wilayah, supaya tidak otomatis memfilter tanpa persetujuan user
show_debug = st.sidebar.checkbox("Tampilkan debug data (kolom, head, region)", value=False)
apply_hierarchy_filter = st.sidebar.checkbox("Gunakan filter hierarki wilayah (opsional)", value=False)

if uploaded_file is not None:
    st.sidebar.success(f"Berkas dimuat: {uploaded_file.name}")

    # Stage 1: Load Data
    raw_df = load_data(uploaded_file)

    if raw_df is not None:
        # Normalisasi region/category agar tidak hanya menampilkan satu nilai karena whitespace/case mismatch
        for col in raw_df.columns:
            if raw_df[col].dtype == 'object':
                raw_df[col] = raw_df[col].astype(str).str.strip()

        # Stage 2: Categorization & Hierarchical Filtering
        df, dimensions, metrics = categorize_columns(raw_df)
        std_map = get_standard_mapping(dimensions)

        # Enhanced Debug panel (opsional) — tampilkan di sidebar dan di area utama
        if show_debug:
            # Sidebar debug (ringkasan)
            st.sidebar.markdown("---")
            st.sidebar.write("Debug columns:", df.columns.tolist())
            st.sidebar.write("Debug dimensions:", dimensions)
            st.sidebar.write("Debug metrics:", metrics)
            st.sidebar.write("Debug std_map:", std_map)

            # Main area debug (lebih lengkap)
            st.markdown("---")
            st.subheader("🔎 Debug: Struktur Data & Contoh")
            st.write("Jumlah baris:", len(df))
            st.write("Nama kolom terdeteksi:")
            st.write(df.columns.tolist())

            st.write("Contoh 10 baris pertama:")
            st.dataframe(df.head(10), use_container_width=True)

            reg_col = std_map.get('region')
            if reg_col and reg_col in df.columns:
                st.write(f"Distribusi nilai pada kolom region ({reg_col}):")
                vc = df[reg_col].astype(str).str.strip().value_counts(dropna=True)
                # tampilkan tabel top 30
                st.write(vc.head(30))
                # tampilkan grafik ringkas
                try:
                    st.bar_chart(vc.head(20))
                except Exception:
                    pass
            else:
                st.write("Kolom region tidak terdeteksi atau tidak ada di dataset.")

        # Filter hierarki wilayah (hanya bila user mengaktifkan checkbox)
        df_filtered = df.copy()
        if apply_hierarchy_filter and filter_regional_hierarchy is not None:
            try:
                result = filter_regional_hierarchy(df_filtered, code_col=std_map.get('code') or 'KODE')
                if isinstance(result, tuple) and len(result) >= 1:
                    df_filtered = result[0]
                else:
                    df_filtered = result
            except Exception as e:
                st.warning(f"filter_regional_hierarchy gagal dijalankan: {e}")

        # Sidebar Filter Dinamis (User Manual)
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Filter Data")

        reg_col = std_map.get('region')
        if reg_col and reg_col in df_filtered.columns:
            unique_regions = df_filtered[reg_col].dropna().astype(str).str.strip().unique().tolist()
            selected_region = st.sidebar.multiselect(
                f"Filter Berdasarkan {reg_col}:",
                options=unique_regions,
                default=[]
            )
            if selected_region:
                df_filtered = df_filtered[df_filtered[reg_col].astype(str).str.strip().isin(selected_region)]

        # Stage 3: Render Dashboard Visualisasi Komplit
        render_kpi_cards(df_filtered, metrics)
        render_primary_charts(df_filtered, std_map, metrics)

        # Rincian KPI per Kategori (opsional)
        if render_category_kpis is not None:
            try:
                render_category_kpis(df_filtered, std_map, metrics)
            except Exception as e:
                st.warning(f"render_category_kpis gagal dijalankan: {e}")

        # Tabel Data Terstruktur & Download
        render_data_table(df_filtered)

else:
    st.info("Silakan unggah berkas Excel/CSV melalui sidebar di sebelah kiri untuk memulai analisis.")
